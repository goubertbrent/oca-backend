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
from types import NoneType

from admin.explorer.scripts import get_scripts, create_script, get_script, update_script, delete_script, run_script
from admin.explorer.to import CreateScriptTO, UpdateScriptTO, RunResultTO, RunScriptTO
from mcfw.consts import REST_TYPE_TO
from mcfw.restapi import rest
from mcfw.rpc import arguments, returns


@rest('/admin/api/scripts', 'get', silent_result=True)
@returns([dict])
@arguments()
def api_get_scripts():
    return [script.to_dict() for script in get_scripts()]


@rest('/admin/api/scripts', 'post', type=REST_TYPE_TO)
@returns(dict)
@arguments(data=CreateScriptTO)
def api_create_script(data):
    return create_script(data).to_dict()


@rest('/admin/api/scripts/<script_id:[^/]+>', 'get')
@returns(dict)
@arguments(script_id=(int, long))
def api_get_script(script_id):
    return get_script(script_id).to_dict()


@rest('/admin/api/scripts/<script_id:[^/]+>', 'put', type=REST_TYPE_TO)
@returns(dict)
@arguments(script_id=(int, long), data=UpdateScriptTO)
def api_update_script(script_id, data):
    return update_script(script_id, data).to_dict()


@rest('/admin/api/scripts/<script_id:[^/]+>', 'delete')
@returns(NoneType)
@arguments(script_id=(int, long))
def api_delete_script(script_id):
    delete_script(script_id)


@rest('/admin/api/scripts/<script_id:[^/]+>', 'post', silent_result=True, type=REST_TYPE_TO)
@returns(RunResultTO)
@arguments(script_id=(int, long), data=RunScriptTO)
def api_run_script(script_id, data):
    return run_script(script_id, data)
