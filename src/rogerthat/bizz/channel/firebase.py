# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
# NOTICE: THIS FILE HAS BEEN MODIFIED BY GREEN VALLEY BELGIUM NV IN ACCORDANCE WITH THE APACHE LICENSE VERSION 2.0
# Copyright 2018 GIG Technology NV
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
# @@license_version:1.6@@

#
# Most of this file is taken from gae-plugin-framework/framework/server/framework/bizz/firebase.py
# with some modifications for custom token claims
from base64 import b64encode
import json
import logging
import time

from google.appengine.api import app_identity
import httplib2
from jose import jwt
from jose.constants import Algorithms
from oauth2client.client import GoogleCredentials

from rogerthat.consts import DEBUG
from rogerthat.models import AppSettings
from rogerthat.models.firebase import FirebaseProjectSettings
from rogerthat.settings import get_server_settings

try:
    from functools import lru_cache
except ImportError:
    from functools32 import lru_cache

_IDENTITY_ENDPOINT = 'https://identitytoolkit.googleapis.com/google.identity.identitytoolkit.v1.IdentityToolkit'
_FIREBASE_SCOPES = [
    'https://www.googleapis.com/auth/firebase.database',
    'https://www.googleapis.com/auth/userinfo.email']


@lru_cache()
def _get_firebase_db_url():
    return get_server_settings().firebaseDatabaseUrl


# Memoize the authorized http, to avoid fetching new access tokens
@lru_cache()
def _get_http():
    """Provides an authed http object."""
    http = httplib2.Http(timeout=30)
    # Use application default credentials to make the Firebase calls
    # https://firebase.google.com/docs/reference/rest/database/user-auth
    creds = GoogleCredentials.get_application_default().create_scoped(
        _FIREBASE_SCOPES)
    creds.authorize(http)
    return http


def send_firebase_message(channel_id, message):
    """Updates data in firebase. If a message is provided, then it updates
     the data at /channels/<channel_id> with the message using the PATCH
     http method.
     """
    db_url = _get_firebase_db_url()
    if not db_url:
        if not DEBUG:
            logging.error('Can not send out Firebase messages because the database URL is not set in ServerSettings.')
        return
    path = '{}/channels/{}.json'.format(db_url, channel_id)
    return _get_http().request(path, 'PATCH', body=message)


def create_custom_token(uid, claims, mobile=None):
    """Create a secure token for the given ids.
    This method is used to create secure custom JWT tokens to be passed to
    clients. It takes a unique id (uid) and a session id (sid) that will be used
    by Firebase's security rules to prevent unauthorized access.

    Args:
        uid (str): a unique id (between 1-36 characters long)
        claims (dict): Additional claims
        mobile (Mobile): if the app service account should be used instead of default service account
    """

    if mobile:
        credentials = None
        if mobile.is_ios:
            app_settings = AppSettings.get(AppSettings.create_key(mobile.app_id))
            if app_settings and app_settings.ios_firebase_project_id:
                fps = FirebaseProjectSettings.create_key(app_settings.ios_firebase_project_id).get()
                if fps:
                    credentials = fps.service_account_key

        if not credentials:
            credentials = json.loads(get_server_settings().mobileFirebaseCredentials)
        client_email = credentials['client_email']
    else:
        # use the app_identity service from google.appengine.api to get the
        # project's service account email automatically
        client_email = app_identity.get_service_account_name()

    now = int(time.time())
    payload = {
        'iss': client_email,
        'sub': client_email,
        'aud': _IDENTITY_ENDPOINT,
        'uid': uid,
        'iat': now,
        'exp': now + 3600,
        'claims': claims
    }
    if mobile:
        return jwt.encode(payload, credentials['private_key'], algorithm=Algorithms.RS256)
    else:
        if DEBUG:
            from google.appengine.api.app_identity.app_identity_stub import APP_SERVICE_ACCOUNT_NAME
            if client_email == APP_SERVICE_ACCOUNT_NAME:
                raise Exception('Cannot create firebase token with default development service account.'
                                ' Set the GOOGLE_APPLICATION_CREDENTIALS environment variable with as value the path '
                                'to a json file containing the credentials for a service account.'
                                ' See https://developers.google.com/identity/protocols/application-default-credentials')
        # encode the required claims
        # per https://firebase.google.com/docs/auth/server/create-custom-tokens
        # uid and sid will be used as channel ids, sid is added to *claims*
        header = b64encode(json.dumps({'typ': 'JWT', 'alg': 'RS256'}))
        encoded_payload = b64encode(json.dumps(payload))
        to_sign = '%s.%s' % (header, encoded_payload)
        return '{}.{}'.format(to_sign, b64encode(app_identity.sign_blob(to_sign)[1]))
