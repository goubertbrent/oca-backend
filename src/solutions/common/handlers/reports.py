# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley NV
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
# @@license_version:1.5@@

import webapp2

from rogerthat.bizz.maps.reports import _reports_request
from rogerthat.dal.profile import get_service_profile
from rogerthat.rpc import users


class ReportsHandler(webapp2.RequestHandler):
    def _handle_request(self):
        url = self.request.url.split('/common/reports')[1]
        service_profile = get_service_profile(users.get_current_user())
        result = _reports_request(url, self.request.method, self.request.body, service_profile.defaultLanguage,
                                  service_profile.sik)
        self.response.set_status(result.status_code)
        self.response.headers.extend(result.headers)
        self.response.out.write(result.content)

    def get(self):
        self._handle_request()

    def post(self):
        self._handle_request()

    def put(self):
        self._handle_request()

    def delete(self):
        self._handle_request()
