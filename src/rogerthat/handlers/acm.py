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
import json
import logging
from random import getrandbits
import urllib
import uuid

from google.appengine.api import urlfetch
from jose import jwt
import webapp2

from mcfw.cache import cached
from mcfw.rpc import returns, arguments
from rogerthat.consts import DEBUG, DAY
from rogerthat.models.auth.acm import ACMSettings, ACMLoginState, ACMLogoutState


APP_LOGIN_URL_TEMPLATE = '%s://x-callback-url/auth/login'
APP_LOGOUT_URL_TEMPLATE = '%s://x-callback-url/auth/logout'


@cached(1, lifetime=DAY)
@returns(dict)
@arguments(url=unicode)
def _get_openid_config(url):
    response = urlfetch.fetch(url, deadline=10)
    if response.status_code != 200:
        return None
    return json.loads(response.content)


@cached(1, lifetime=DAY)
@returns(unicode)
@arguments(url=unicode)
def _get_jwks(url):
    response = urlfetch.fetch(url, deadline=10)
    if response.status_code != 200:
        return None
    return response.content


class ACMOpenIdLoginHandler(webapp2.RequestHandler):
    def get(self):
        code_challenge = self.request.GET.get('code_challenge') # SHA256
        app_id = self.request.GET.get('app_id')

        settings = ACMSettings.create_key(app_id).get()
        if not settings:
            logging.info('ACMSettings %s not found', app_id)
            self.abort(400)

        response_type = u'code'
        scope = u'openid rrn profile vo offline_access'

        state = str(uuid.uuid4())
        nonce = str(getrandbits(64))

        state_model = ACMLoginState(key=ACMLoginState.create_key(state),
                                    app_id=app_id,
                                    scope=scope,
                                    code_challenge=code_challenge)
        state_model.put()
        params = {
            'client_id': settings.client_id,
            'redirect_uri': settings.auth_redirect_uri,
            'response_type': response_type,
            'scope': scope,
            'state': state,
            'nonce': nonce,
            'code_challenge': code_challenge,
            'code_challenge_method': u'S256'
        }
        openid_config = _get_openid_config(settings.openid_config_uri)
        authorize_url = "%s?%s" % (openid_config['authorization_endpoint'], urllib.urlencode(params))
        logging.info('Redirecting to %s', authorize_url)
        self.redirect(str(authorize_url))


class ACMOpenIdTokenHandler(webapp2.RequestHandler):
    def post(self):
        app_id = self.request.get("app_id", None)
        state = self.request.get("state", None)
        code = self.request.get("code", None)
        code_verifier = self.request.get("code_verifier", None)

        settings = ACMSettings.create_key(app_id).get()
        if not settings:
            logging.info('ACMSettings %s not found', app_id)
            self.abort(400)

        state_model = ACMLoginState.create_key(state).get()
        if not state_model:
            logging.info('ACMLoginState %s not found', state)
            self.abort(400)
            
        hashed = hashlib.sha256(code_verifier.encode('ascii')).digest()
        encoded = base64.urlsafe_b64encode(hashed)
        code_challenge = encoded.decode('ascii')[:-1]
        if state_model.code_challenge != code_challenge:
            logging.info('Invalid code challenge got %s and expected %s for %s', code_challenge, state_model.code_challenge, state)
            self.abort(400)
            
        if state_model.id_token:
            logging.info('ACMLoginState %s token already set', state)
            self.abort(400)

        post_body = {
            'grant_type': u'authorization_code',
            'code': code,
            'client_id': settings.client_id,
            'client_secret': settings.client_secret,
            'redirect_uri': settings.auth_redirect_uri,
            'code_verifier': code_verifier
        }
        payload = urllib.urlencode(post_body)
        openid_config = _get_openid_config(settings.openid_config_uri)
        logging.info('Request to: %s\n%s', openid_config['token_endpoint'], payload)
        token_result = urlfetch.fetch(openid_config['token_endpoint'], payload, urlfetch.POST, deadline=15)  # type: urlfetch._URLFetchResult
        if DEBUG:
            logging.info('%s\n%s\n%s', token_result.status_code, token_result.headers, token_result.content)
        if token_result.status_code != 200:
            logging.info('Invalid response: %s %s' % (token_result.status_code, token_result.content))
            self.abort(400)

        state_model.token = json.loads(token_result.content)
        jwks = _get_jwks(openid_config['jwks_uri'])
        state_model.id_token = jwt.decode(state_model.token['id_token'],
                                          key=jwks,
                                          audience=settings.client_id,
                                          issuer=openid_config['issuer'],
                                          access_token=state_model.token['access_token'])
        state_model.put()
        
        result = {
            'sub': state_model.id_token['sub']
        }

        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(json.dumps(result))


class ACMOpenIdLogoutHandler(webapp2.RequestHandler):
    def get(self):
        app_id = self.request.GET.get('app_id')

        settings = ACMSettings.create_key(app_id).get()
        if not settings:
            logging.info('ACMSettings %s not found', app_id)
            self.abort(400)

        state = str(uuid.uuid4())
        state_model = ACMLogoutState(key=ACMLogoutState.create_key(state),
                                     app_id=app_id)
        state_model.put()

        params = {
            'client_id': settings.client_id,
            'post_logout_redirect_uri': settings.logout_redirect_uri,
            'state': state,
        }
        openid_config = _get_openid_config(settings.openid_config_uri)
        logout_url = "%s?%s" % (openid_config['end_session_endpoint'], urllib.urlencode(params))
        logging.info('Redirecting to %s', logout_url)
        self.redirect(str(logout_url))


class ACMOpenIdAuthorizedCallbackHandler(webapp2.RequestHandler):
    def get(self):
        state = self.request.GET.get('state')
        code = self.request.GET.get('code')

        state_model = ACMLoginState.create_key(state).get()
        if not state_model:
            logging.info('ACMLoginState %s not found', state)
            self.abort(400)

        base_redirect_url = APP_LOGIN_URL_TEMPLATE % state_model.app_id
        params = {
            'provider': 'acm',
            'state': state,
            'code': code,
        }
        app_url = "%s?%s" % (base_redirect_url, urllib.urlencode(params))
        logging.info('Redirecting to %s', app_url)
        self.redirect(str(app_url))


class ACMOpenIdLoggedOutCallbackHandler(webapp2.RequestHandler):
    def get(self):
        state = self.request.GET.get('state')

        state_model = ACMLogoutState.create_key(state).get()
        if not state_model:
            logging.info('ACMLogoutState %s not found', state)
            self.abort(400)

        base_redirect_url = APP_LOGOUT_URL_TEMPLATE % state_model.app_id
        params = {
            'provider': 'acm',
            'state': state,
        }
        app_url = "%s?%s" % (base_redirect_url, urllib.urlencode(params))
        logging.info('Redirecting to %s', app_url)
        self.redirect(str(app_url))
