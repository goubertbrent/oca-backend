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
import json
import logging
import urllib

import webapp2

from mcfw.rpc import serialize_complex_value
from rogerthat.bizz.payment import get_payment_provider_for_user, get_api_module
from rogerthat.bizz.payment.state import finish_login_state, create_login_state, get_login_state
from rogerthat.dal.payment import get_payment_provider
from rogerthat.rpc import users
from rogerthat.settings import get_server_settings
from rogerthat.to.payment import AppPaymentProviderTO
from rogerthat.utils.app import create_app_user_by_email


class PaymentCallbackHandler(webapp2.RequestHandler):
    def get(self, provider_id, path):
        params = dict(self.request.GET)
        logging.debug("PaymentCallbackHandler.GET '%s', at path '%s' with params %s", provider_id, path, params)
        get_api_module(provider_id).web_callback(self, path, params)

    def post(self, provider_id, path):
        params = dict(self.request.POST)
        logging.debug("PaymentCallbackHandler.POST '%s', at path '%s' with params %s", provider_id, path, params)
        get_api_module(provider_id).web_callback(self, path, params)


class PaymentLoginRedirectHandler(webapp2.RequestHandler):
    def get(self, provider_id):
        pp = get_payment_provider(provider_id)
        if not pp:
            logging.debug('PaymentLoginRedirectHandler: payment provider not found')
            self.abort(400)
            return

        email = self.request.get("email", None)
        app_id = self.request.get("app_id", None)
        app_user = create_app_user_by_email(email, app_id)

        state = create_login_state(app_user, provider_id)
        args = {
            'state': state,
            'response_type': 'code',
            'client_id': pp.oauth_settings.client_id,
            'scope': pp.oauth_settings.scope,
            'redirect_uri': pp.redirect_url(get_server_settings().baseUrl)
        }
        url = '%s?%s' % (pp.oauth_settings.authorize_url, urllib.urlencode(args))
        logging.debug('Redirecting to %s', url)
        self.redirect(url.encode('utf-8'))


class PaymentLoginAppHandler(webapp2.RequestHandler):
    def post(self):
        params = dict(self.request.POST)
        logging.debug("PaymentLoginAppHandler with params %s", params)
        user = self.request.headers.get("X-MCTracker-User", None)
        password = self.request.headers.get("X-MCTracker-Pass", None)
        if not (user and password):
            logging.debug("user not provided")
            self.response.set_status(500)
            return

        if not users.set_json_rpc_user(base64.decodestring(user), base64.decodestring(password)):
            logging.debug("user not set")
            self.response.set_status(500)
            return
        app_user = users.get_current_user()

        state = params["state"]
        login_state = get_login_state(state)
        if app_user != login_state.app_user:
            self.response.set_status(500)
            logging.error("%s tried to finish anothers user login %s", app_user, state)
            return

        token = get_api_module(login_state.provider_id).handle_code(login_state)
        logging.debug('Received token: %s', token)
        if not finish_login_state(state, token):
            logging.debug("user already finished this login")
            self.response.set_status(500)
            return

        args = {"result": "success",
                "payment_provider": serialize_complex_value(
                    get_payment_provider_for_user(app_user, login_state.provider_id), AppPaymentProviderTO, False)}
        r = json.dumps(args)
        self.response.out.write(r)
