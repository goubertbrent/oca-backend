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
# @@license_version:1.5@@

import webapp2

from rogerthat.rpc import users
from rogerthat.utils.channel import send_message
from solutions.common.bizz.events import save_google_credentials


class EventsGoogleOauth2callbackHandler(webapp2.RequestHandler):

    def get(self):
        service_user = users.get_current_user()
        calendarId = long(self.request.get("state"))
        code = self.request.get("code", None)
        error = self.request.get("error", None)
        if error:
            send_message(service_user, u"solutions.common.calendar.google.callback", success=False, calendar_id=calendarId)
        else:
            success = save_google_credentials(service_user, calendarId, code)
            send_message(service_user, u"solutions.common.calendar.google.callback", success=success, calendar_id=calendarId)

        self.response.write("Loading...")
