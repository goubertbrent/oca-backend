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

import hashlib
import logging

from google.appengine.ext import webapp

from rogerthat.dal.app import get_app_by_id


class UploadAppAppleCertsHandler(webapp.RequestHandler):

    def post(self):
        from rogerthat.settings import get_server_settings
        settings = get_server_settings()
        secret = self.request.headers.get("X-Nuntiuz-Secret", None)
        if secret != settings.jabberSecret:
            logging.error(u"Received unauthenticated callback response, ignoring ...")
            return

        app_id = self.request.POST.get("app_id", None)
        cert = self.request.POST.get("cert", None)
        key = self.request.POST.get("key", None)
        valid_until = int(self.request.POST.get("valid_until", None))
        checksum = self.request.POST.get("checksum", None)

        digester = hashlib.sha256()
        digester.update(app_id)
        digester.update(cert)
        digester.update(app_id)
        digester.update(key)
        digester.update(app_id)
        digester.update(str(valid_until))
        digester.update(app_id)
        checksum_calculated = digester.hexdigest()

        if checksum != checksum_calculated:
            self.response.write("Checksum does not pass.")
            self.error(400)
            return

        app = get_app_by_id(app_id)
        if not app:
            self.response.write("App not found.")
            self.error(400)
            return

        app.apple_push_cert = cert
        app.apple_push_key = key
        app.apple_push_cert_valid_until = valid_until
        app.put()

        self.response.write("Certificate and key successfully updated!")
