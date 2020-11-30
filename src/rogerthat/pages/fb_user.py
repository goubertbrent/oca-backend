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

import base64
import hashlib
import hmac
import json
import logging

from google.appengine.ext import deferred
import webapp2

from rogerthat.bizz.app import get_app
from rogerthat.bizz.user import delete_account
from rogerthat.models import FacebookProfilePointer
from rogerthat.settings import get_server_settings


class FacebookDeleteUserHandler(webapp2.RequestHandler):

    def return_exception(self, status_code, error):
        self.response.headers['Content-Type'] = "application/json"
        self.response.out.write(json.dumps(dict(status_code=status_code, error=error)))
        self.response.set_status(status_code)

    def get(self):
        self.response.out.write('Deleted')

    def post(self):
        logging.debug(self.request.GET)
        logging.debug(self.request.POST)
        signed_request = self.request.get('signed_request')

        try:
            encoded_sig, payload = signed_request.split('.', 2)
        except:
            logging.debug('Invalid request', exc_info=True)
            return self.return_exception(400, 'Invalid request')

        try:
            tmp_payload = payload.encode('ascii')
            tmp_payload += "=" * ((4 - len(tmp_payload) % 4) % 4)
            decoded_payload = json.loads(base64.urlsafe_b64decode(tmp_payload))
            if type(decoded_payload) is not dict or 'user_id' not in decoded_payload.keys():
                return self.return_exception(400, 'Invalid payload data')
        except:
            logging.debug('Could not decode payload', exc_info=True)
            return self.return_exception(400, 'Could not decode payload')

        try:
            app_id = self.request.get("app_id")
            app = get_app(app_id)
            secret = app.facebook_app_secret
            tmp_encoded_sig = encoded_sig.encode('ascii')
            tmp_encoded_sig += "=" * ((4 - len(tmp_encoded_sig) % 4) % 4)
            decoded_sig = base64.urlsafe_b64decode(tmp_encoded_sig)
            expected_sig = hmac.new(secret.encode('utf8'), payload.encode('utf8'), hashlib.sha256).digest()
        except:
            logging.debug('Could not decode signature', exc_info=True)
            return self.return_exception(400, 'Could not decode signature')

        if not hmac.compare_digest(expected_sig, decoded_sig):
            return self.return_exception(400, 'Invalid request')

        fpp = FacebookProfilePointer.get_by_key_name(decoded_payload['user_id'])
        if fpp:
            app_user = fpp.user
            logging.debug("delete_account user:%s", app_user)
            deferred.defer(delete_account, app_user)

        url = u'%s/unauthenticated/facebook/user/delete?uid=%s' % (get_server_settings().baseUrl, decoded_payload['user_id'])
        confirmation_code = decoded_payload['user_id']
        self.response.headers['Content-Type'] = "application/json"
        self.response.out.write(json.dumps(dict(url=url, confirmation_code=confirmation_code)))