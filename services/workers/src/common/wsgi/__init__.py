# -*- coding: utf-8 -*-
# Copyright 2020 Green Valley Belgium NV
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
# @@license_version:1.7@@

import logging
import time

import webapp2

from common.setup_functions import DEBUG, start_suppressing
from common.wsgi.context import run_in_context


class CommonWSGIApplication(webapp2.WSGIApplication):
    def __init__(self, handlers):
        super(CommonWSGIApplication, self).__init__(handlers)

    def __call__(self, environ, start_response):
        return run_in_context(self._call_in_context, environ, start_response, _path=environ['PATH_INFO'])

    def _call_in_context(self, environ, start_response):
        from google.appengine.api.runtime import runtime
        import os
        try:
            current_memory_start = runtime.memory_usage().current()
        except:
            logging.debug('memory_debugging failed to get start memory', exc_info=True)
            current_memory_start = 0

        path = environ['PATH_INFO']
        if path in ('/_ah/queue/deferred', '/_ah/pipeline/output', '/_ah/pipeline/finalized'):
            start_suppressing()
        if DEBUG:
            start_time = time.time()
            result = webapp2.WSGIApplication.__call__(self, environ, start_response)
            took_time = time.time() - start_time
            logging.info('Handling {0} - {1:.3f}s'.format(environ['PATH_INFO'], took_time))
            return result
        try:
            return webapp2.WSGIApplication.__call__(self, environ, start_response)
        finally:
            try:
                current_memory_end = runtime.memory_usage().current()
            except:
                logging.debug('memory_debugging failed to get end memory', exc_info=True)
                current_memory_end = 0

            if current_memory_end > current_memory_start:
                logging.debug('memory_debugging:+%s start:%s end:%s instance_id:%s', current_memory_end - current_memory_start, current_memory_start, current_memory_end, os.environ.get('INSTANCE_ID', '<unknown>'))
            elif current_memory_start > current_memory_end:
                logging.debug('memory_debugging:-%s start:%s end:%s instance_id:%s', current_memory_start - current_memory_end, current_memory_start, current_memory_end, os.environ.get('INSTANCE_ID', '<unknown>'))
            else:
                logging.debug('memory_debugging:= start:%s end:%s instance_id:%s', current_memory_start, current_memory_end, os.environ.get('INSTANCE_ID', '<unknown>'))
