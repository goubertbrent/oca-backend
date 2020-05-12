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

import json
import logging
import urllib

import webapp2

from rogerthat.bizz.itsme import get_itsme_openid_config, get_userinfo, get_authorization_token, \
    get_itsme_openid_settings
from rogerthat.consts import DEBUG
from rogerthat.models import OAuthState
from rogerthat.models.properties.forms import OpenIdWidgetResult
from rogerthat.pages import UserAwareRequestHandler
from rogerthat.rpc import users
from rogerthat.settings import get_server_settings
from rogerthat.utils.app import get_app_user_tuple

# See https://belgianmobileid.github.io/slate/login.html#Onboarding

APP_REDIRECT_URL_TEMPLATE = 'oauth-%s://x-callback-url/oauth/widget/itsme?&'


class ItsmeAuthorizeHandler(UserAwareRequestHandler):
    def get(self):
        has_current_user = self.set_user()
        if not has_current_user:
            self.abort(401)
        current_user = users.get_current_user()
        user, app_id = get_app_user_tuple(current_user)

        scope = self.request.GET.get('scope') or ''
        # Add default scopes which must always be present
        server_settings = get_server_settings()
        settings = get_itsme_openid_settings(app_id)
        scope += ' openid service:%s' % settings.data['service_code']
        url = get_itsme_openid_config(settings).authorization_endpoint
        state = OAuthState(
            user=user.email(),
            app_id=app_id,
            scope=scope,
            redirect_url='%s%s' % (server_settings.baseUrl, self.url_for('itsme_login')),
        )
        state.put()
        parameters = {
            'response_type': 'code',
            'scope': scope,
            'client_id': settings.client_id,
            'state': state.state,
            'redirect_uri': state.redirect_url
        }
        authorize_url = '%s?&%s' % (url, urllib.urlencode(parameters))
        logging.info('Redirecting to %s', authorize_url)
        self.redirect(str(authorize_url))


class ItsmeLoginHandler(webapp2.RequestHandler):
    def get(self):
        code = self.request.GET.get('code')
        state = self.request.GET.get('state')
        if not state:
            self.abort(400)
        if state:
            state = int(state)
        state_model = OAuthState.create_key(state).get()  # type: OAuthState
        if not state_model:
            logging.info('OAuthState %s not found', state)
            self.abort(400)
        base_redirect_url = APP_REDIRECT_URL_TEMPLATE % state_model.app_id
        params = {
            'state': state,
            'status': 'success',
        }
        if 'error' in self.request.params:
            if self.request.params['error'] == 'access_denied':
                # 'aborted' avoids showing an error on the client
                # since they've denied the authorization request themselves
                params['status'] = 'aborted'
            else:
                logging.error('Error in itsme callback: %s', self.request.params)
                params['status'] = 'error'
        else:
            settings = get_itsme_openid_settings(state_model.app_id)
            openid_config = get_itsme_openid_config(settings)
            state_model.token = get_authorization_token(code, openid_config, settings, state_model.redirect_url)
            state_model.put()
            if DEBUG:
                logging.debug(state_model.token)
        self.redirect(str(base_redirect_url + urllib.urlencode(params)))


class ItsmeAuthorizedHandler(UserAwareRequestHandler):
    def get(self):
        # This is called by the OpenId widget
        has_current_user = self.set_user()
        if not has_current_user:
            self.abort(401)

        state = self.request.GET.get('state')
        if not state:
            self.abort(400)
        state = int(state)
        state_model = OAuthState.create_key(state).get()  # type: OAuthState
        if not state_model:
            self.abort(400)
        user, app_id = get_app_user_tuple(users.get_current_user())
        settings = get_itsme_openid_settings(app_id)
        config = get_itsme_openid_config(settings)
        if state_model.user != user.email():
            self.abort(403)
        user_info = get_userinfo(settings, config, state_model.token)
        logging.debug(user_info)
        # Convert itsme info to the info our apps expects
        result = OpenIdWidgetResult.from_dict(user_info)
        self.response.write(json.dumps(result.to_dict()))


class ItsmeJWKsHandler(webapp2.RequestHandler):
    def get(self, app_id=None):
        settings = get_itsme_openid_settings(app_id or 'rogerthat')
        keys = ['kty', 'e', 'use', 'kid', 'alg', 'n']
        sig_key = {k: v for k, v in settings.signature_private_key.iteritems() if k in keys}
        enc_key = {k: v for k, v in settings.encryption_private_key.iteritems() if k in keys}
        jwkset = {'keys': [sig_key, enc_key]}
        self.response.headers['Content-Type'] = 'application/jwk-set+json'
        self.response.write(json.dumps(jwkset, indent=2, sort_keys=True))
