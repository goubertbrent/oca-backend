# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# @@license_version:1.6@@

import inspect
import logging
import new
import os
import pprint
import time
import traceback
from datetime import datetime

from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext.deferred import deferred

import autopep8
from mcfw.exceptions import HttpBadRequestException, HttpNotFoundException, HttpConflictException
from mcfw.rpc import arguments, returns
from models import Script, ScriptFunction, LastScriptRun
from to import CreateScriptTO, RunResultTO, RunScriptTO, UpdateScriptTO


@returns(Script)
@arguments(script=CreateScriptTO)
def create_script(script):
    return _put_script(Script(author=users.get_current_user()), script)


def get_script(script_id):
    # type: (long) -> Script
    script = Script.create_key(script_id).get()
    if not script:
        raise HttpNotFoundException('oca.error', {'message': 'Script with id %s not found' % script_id})
    return script


@returns(Script)
@arguments(script_id=(int, long), script=UpdateScriptTO)
def update_script(script_id, script):
    model = get_script(script_id)
    if model.version != script.version:
        msg = 'Cannot save, script has been modified by %s on %s. Please reload the page.' % (model.modified_by,
                                                                                              model.modified_on)
        raise HttpConflictException('oca.error', {'message': msg})
    return _put_script(model, script)


def _get_script_function_models(script_name, source, old_functions, ignore_errors=False):
    script_module = new.module(str(script_name))
    try:
        exec source in script_module.__dict__
    except Exception:
        logging.warn('Compilation failed for \'%s\'', script_name, exc_info=True)
        if ignore_errors:
            return []
        msg = 'Could not compile script: %s' % traceback.format_exc()
        raise HttpBadRequestException('oca.error', {'message': msg})
    functions = inspect.getmembers(script_module,
                                   lambda x: inspect.isfunction(x) and x.__module__ == script_module.__name__)
    function_models = []
    old_funcs = {f.name: f for f in old_functions}

    lines = source.splitlines()
    for f in functions:
        f_name = unicode(f[0])
        line_number = 1
        for i, line in enumerate(lines):
            if 'def %s' % f_name in line:
                line_number = i + 1
                break
        if f_name in old_funcs:
            updated_function = old_funcs[f_name]
            updated_function.line_number = line_number
            function_models.append(updated_function)
        else:
            function_models.append(ScriptFunction(name=f_name, line_number=line_number))
    return function_models


def _put_script(model, script):
    # type: (Script, UpdateScriptTO) -> Script
    assert users.is_current_user_admin()
    formatted_source = autopep8.fix_code(script.source, options={'max_line_length': 120})
    model.populate(name=script.name,
                   source=formatted_source,
                   modified_by=users.get_current_user(),
                   modified_on=datetime.now(),
                   version=model.version + 1,
                   functions=_get_script_function_models(script.name, formatted_source, model.functions))
    model.put()
    return model


def get_scripts():
    return Script.list().fetch(None, projection=[Script.name]) or _migrate_scripts()


def delete_script(script_id):
    return Script.create_key(script_id).delete()


@arguments(script_id=(int, long), data=RunScriptTO)
def run_script(script_id, data):
    # type: (long, RunScriptTO) -> RunResultTO
    assert users.is_current_user_admin()
    script = get_script(script_id)
    task_id = None
    run_result = None
    if data.deferred:
        task_id = deferred.defer(_run_deferred, script_id, data).name.decode('utf-8')
    else:
        run_result = _run_script(script, data)
    for f in script.functions:
        if f.name == data.function:
            f.last_run = LastScriptRun(date=datetime.now(),
                                       user=users.get_current_user(),
                                       task_id=task_id,
                                       request_id=run_result.request_id if run_result else None,
                                       time=run_result.time if run_result else None,
                                       succeeded=run_result.succeeded if run_result else True)
            break
    script.put_async()
    result = f.last_run.to_dict()
    if run_result:
        result.update(run_result.to_dict())
    result.update({'script': script.to_dict()})
    result['user'] = unicode(result['user'])
    return RunResultTO.from_dict(result)


def _run_script(script, function):
    # type: (Script, RunScriptTO) -> RunResultTO
    script_module = new.module(str(script.name))
    exec script.source in script_module.__dict__
    func = getattr(script_module, str(function.function))
    start = time.time()
    try:
        result = pprint.pformat(func()).decode(errors='replace')
        succeeded = True
    except Exception:
        result = traceback.format_exc().decode(errors='replace')
        succeeded = False
    return RunResultTO(result=result,
                       succeeded=succeeded,
                       time=time.time() - start,
                       request_id=os.environ.get('REQUEST_LOG_ID'))


def _run_deferred(script_id, function):
    # type: (long, RunScriptTO) -> None
    script = get_script(script_id)
    run_result = _run_script(script, function)
    logging.info('Result from running function "%s" in script "%s"', function.function, script.name)
    logging.info(run_result.to_dict(exclude=['result']))
    logging.info(run_result.result)


def _migrate_scripts():
    from rogerthat.models import Code
    scripts = []
    for code in Code.all():
        scripts.append(Script(name=code.name,
                              author=code.author,
                              modified_on=datetime.utcfromtimestamp(code.timestamp),
                              modified_by=code.author,
                              source=code.source,
                              functions=_get_script_function_models(code.name, code.source, [], ignore_errors=True),
                              version=code.version))
    ndb.put_multi(scripts)
    return scripts
