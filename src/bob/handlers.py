# -*- coding: utf-8 -*-
# Copyright 2017 Mobicage NV
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
# @@license_version:1.2@@

import httplib
import json
import logging

import webapp2
from solution_server_settings import get_solution_server_settings

from bob.bizz import set_ios_app_id
from rogerthat.bizz.app import AppDoesNotExistException


def _validate_request(handler):
    solution_server_settings = get_solution_server_settings()
    secret = handler.request.headers.get("X-BOB-SECRET")
    if not solution_server_settings.bob_api_secret:
        logging.error("bob_api_secret is not set yet")
        handler.abort(401)
    if secret != solution_server_settings.bob_api_secret:
        handler.abort(401)


class SetIosAppIdHandler(webapp2.RequestHandler):
    def post(self):
        _validate_request(self)
        data = json.loads(self.request.body)
        app_id = data['app_id']
        ios_app_id = data['ios_app_id']
        try:
            set_ios_app_id(app_id, ios_app_id)
        except AppDoesNotExistException:
            self.abort(httplib.NOT_FOUND)
