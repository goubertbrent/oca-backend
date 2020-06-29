# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
# NOTICE: THIS FILE HAS BEEN MODIFIED BY GREEN VALLEY BELGIUM NV IN ACCORDANCE WITH THE APACHE LICENSE VERSION 2.0
# Copyright 2018 GIG Technology NV
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

import logging
import os
import pickle
import threading

from google.appengine.api.taskqueue import taskqueue
import google.appengine.api.users
from google.appengine.ext import deferred
import webapp2

from utils import get_current_queue


SERVER_SOFTWARE = os.environ.get("SERVER_SOFTWARE", "Development")
DEBUG = SERVER_SOFTWARE.startswith('Development')


def patch_users():
    # THIS PIECE OF CODE MUST BE ON TOP BECAUSE IT MONKEY PATCHES THE BUILTIN USER CLASS
    # START MONKEY PATCH
    def email_lower(email):
        if email is None:
            return None
        email = email.email() if isinstance(email, google.appengine.api.users.User) else email
        email = unicode(email) if not isinstance(email, unicode) else email
        return email.lower()

    original_constructor = google.appengine.api.users.User.__init__

    def __init__(self, *args, **kwargs):
        if args:
            email = args[0]
            if email:
                lower_email = email_lower(email)
                if lower_email != email:
                    args = list(args)
                    args[0] = lower_email
        else:
            email = kwargs.get('email', None)
            if email is not None:
                lower_email = email_lower(email)
                if lower_email != email:
                    kwargs['email'] = lower_email
        original_constructor(self, *args, **kwargs)

    google.appengine.api.users.User.__init__ = __init__


# MONKEY PATCH logging
# Add possibility to bring down error levels for tasks

class _TLocal(threading.local):
    def __init__(self):
        self.suppress = 0


_tlocal = _TLocal()
del _TLocal


def start_suppressing():
    _tlocal.suppress += 1


def stop_suppressing():
    if _tlocal.suppress > 0:
        _tlocal.suppress -= 1


def reset_suppressing():
    _tlocal.suppress = 0


class StubsFilter(logging.Filter):
    def filter(self, record):
        # Get rid of the annoying 'Sandbox prevented access to file' warnings
        return 'stubs.py' != record.filename


def patch_logging():
    logging.root.addFilter(StubsFilter())
    _orig_error = logging.error
    _orig_critical = logging.critical

    def _new_error(msg, *args, **kwargs):
        suppress = kwargs.pop('_suppress', True)
        if _tlocal.suppress > 0 and suppress:
            logging.warning(msg, *args, **kwargs)
        else:
            _orig_error(msg, *args, **kwargs)

    def _new_critical(msg, *args, **kwargs):
        suppress = kwargs.pop('_suppress', True)
        if _tlocal.suppress > 0 and suppress:
            logging.warning(msg, *args, **kwargs)
        else:
            _orig_critical(msg, *args, **kwargs)

    def _new_exception(msg, *args, **kwargs):
        suppress = kwargs.pop('_suppress', True)
        if _tlocal.suppress > 0 and suppress:
            logging.warning(msg, *args, exc_info=1, **kwargs)
        else:
            _orig_error(msg, *args, exc_info=1, **kwargs)

    logging.error = _new_error
    logging.critical = _new_critical
    logging.exception = _new_exception


def patch_deferred():
    def _new_deferred_run(data):
        try:
            func, args, kwds = pickle.loads(data)
        except Exception as e:
            raise deferred.PermanentTaskFailure(e)
        else:
            try:
                logging.debug('Queue: %s\ndeferred.run(%s.%s%s%s)',
                              get_current_queue(),
                              func.__module__, func.__name__,
                              "".join((",\n             %s" % repr(a) for a in args)),
                              "".join((",\n             %s=%s" % (k, repr(v)) for k, v in kwds.iteritems())))
            except:
                logging.exception('Failed to log the info of this defer (%s)', func)

            try:
                return func(*args, **kwds)
            except deferred.PermanentTaskFailure:
                stop_suppressing()
                raise
            except:
                request = webapp2.get_request()
                if request:
                    execution_count_triggering_error_log = 9
                    execution_count = request.headers.get('X-Appengine-Taskexecutioncount', None)
                    if execution_count and int(execution_count) == execution_count_triggering_error_log:
                        logging.error('This deferred.run already failed %s times!', execution_count, _suppress=False)
                raise

    def _new_deferred_defer(obj, *args, **kwargs):
        # Fixes an issue where the transactional argument wasn't supplied when the task is too large
        taskargs = dict((x, kwargs.pop(("_%s" % x), None))
                        for x in ("countdown", "eta", "name", "target",
                                  "retry_options"))
        taskargs["url"] = kwargs.pop("_url", deferred.deferred._DEFAULT_URL)
        transactional = kwargs.pop("_transactional", False)
        taskargs["headers"] = dict(deferred.deferred._TASKQUEUE_HEADERS)
        taskargs["headers"].update(kwargs.pop("_headers", {}))
        queue = kwargs.pop("_queue", deferred.deferred._DEFAULT_QUEUE)
        pickled = deferred.serialize(obj, *args, **kwargs)
        try:
            task = taskqueue.Task(payload=pickled, **taskargs)
            return task.add(queue, transactional=transactional)
        except taskqueue.TaskTooLargeError:
            key = deferred.deferred._DeferredTaskEntity(data=pickled).put()
            pickled = deferred.deferred.serialize(deferred.deferred.run_from_datastore, str(key))
            task = taskqueue.Task(payload=pickled, **taskargs)
            # this is the patched line (transactional=transactional)
            return task.add(queue, transactional=transactional)

    deferred.run = deferred.deferred.run = _new_deferred_run
    deferred.defer = deferred.deferred.defer = _new_deferred_defer


def patch_buildin_functions():
    patch_logging()
    patch_users()
    patch_deferred()


def setup():
    patch_buildin_functions()
    if DEBUG:
        # Log which datastore models are being read / written on the devserver.
        from db_hooks import add_before_put_hook, add_after_get_hook
        from db_hooks.hooks import put_hook, after_get_hook
    
        add_before_put_hook(put_hook)
        add_after_get_hook(after_get_hook)
