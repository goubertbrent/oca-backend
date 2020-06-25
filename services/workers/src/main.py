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
# @@license_version:1.7@@import datetime


from google.appengine.api import app_identity
from google.appengine.ext.deferred.deferred import TaskHandler
import webapp2

from common.mcfw.restapi import rest_functions, GenericRESTRequestHandler
from workers.jobs import restapi as jobs_restapi
from workers.jobs.handlers import CleanupJobsHandeler, SyncVDABJobsHandler
from common.setup_functions import DEBUG


class MainHandler(webapp2.RequestHandler):

    def get(self):
        self.response.write('service-workers main')


def authorize_internal_request():
    if DEBUG:
        return True
    
    allowed_app_ids = [app_identity.get_application_id()]
    
    request = GenericRESTRequestHandler.getCurrentRequest()
    incoming_app_id = request.headers.get('X-Appengine-Inbound-Appid', None)
    if incoming_app_id and incoming_app_id in allowed_app_ids:
        return True
    return False


handlers = [
    ('/_ah/queue/deferred', TaskHandler),
    ('/_ah/warmup', MainHandler),
    ('/cron/jobs/cleanup', CleanupJobsHandeler),
    ('/cron/jobs/vdab/sync', SyncVDABJobsHandler),
    ('/', MainHandler),
]
handlers.extend(rest_functions(jobs_restapi, authorized_function=authorize_internal_request))

app = webapp2.WSGIApplication(handlers)