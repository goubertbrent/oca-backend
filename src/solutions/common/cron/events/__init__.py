# -*- coding: utf-8 -*-
# Copyright 2016 Mobicage NV
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
# @@license_version:1.1@@

import importlib

from google.appengine.ext import deferred
from mcfw.utils import chunks
from rogerthat.rpc import users
from solution_server_settings import get_solution_server_settings
import webapp2


class SolutionEventsScraper(webapp2.RequestHandler):

    def get(self):
        solution_server_settings = get_solution_server_settings()
        for module_name, service_user in chunks(solution_server_settings.solution_events_scrapers, 2):
            try:
                module = importlib.import_module("solutions.common.cron.events.%s" % module_name)
                getattr(module, 'check_for_events')(users.User(service_user))
            except:
                pass
