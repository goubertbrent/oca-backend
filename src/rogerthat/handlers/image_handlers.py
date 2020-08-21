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

import httplib

import webapp2

from rogerthat.bizz.system import qrcode
from rogerthat.models import QRTemplate
from rogerthat.settings import get_server_settings
from shop.view import authorize_manager


class AppQRTemplateHandler(webapp2.RequestHandler):
    def get(self, app_id, description):
        if not authorize_manager():
            self.abort(403)
        key_name = QRTemplate.create_key_name(app_id, description)
        template = QRTemplate.get_by_key_name(key_name)
        if not template:
            self.abort(httplib.NOT_FOUND)
        self.response.headers['Content-Type'] = 'image/png'
        self.response.headers['Cache-Control'] = "public, max-age=31536000"  # Cache forever since they can't be updated
        url = '%s/' % get_server_settings().baseUrl
        self.response.out.write(qrcode(url, template.blob, map(int, template.body_color), False))
