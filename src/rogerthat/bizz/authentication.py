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

from __future__ import unicode_literals
import logging
import hashlib
import httplib

from google.appengine.api import memcache
from rogerthat.settings import get_server_settings
from rogerthat.utils import now


ITS_YOU_ONLINE_DOMAIN = 'itsyou.online'
OAUTH_BASE_URL = 'https://itsyou.online/v1/oauth'
ITS_YOU_ONLINE_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MHYwEAYHKoZIzj0CAQYFK4EEACIDYgAES5X8XrfKdx9gYayFITc89wad4usrk0n2
7MjiGYvqalizeSWTHEpnd7oea9IQ8T5oJjMVH5cc0H5tFSKilFFeh//wngxIyny6
6+Vq5t5B0V0Ehy01+2ceEon2Y0XDkIKv
-----END PUBLIC KEY-----"""
JWT_AUDIENCE = 'rogerthat-control-center'
JWT_ISSUER = 'itsyouonline'


class Scope(object):
    server_settings = get_server_settings()
    ROOT_ORGANIZATION = server_settings.rootOrganization
    BACKEND_ORGANIZATION = server_settings.backendOrganization
    # Can do everything on this server
    ROOT_ADMIN = 'user:memberof:%s' % ROOT_ORGANIZATION
    ADMIN = 'user:memberof:%s.admins' % ROOT_ORGANIZATION
    BACKEND_ADMIN = 'user:memberof:%s.backends.%s.admins' % (ROOT_ORGANIZATION, BACKEND_ORGANIZATION)
    # Can read/update everything on this server
    BACKEND_EDITOR = 'user:memberof:%s.backends.%s.editors' % (ROOT_ORGANIZATION, BACKEND_ORGANIZATION)
    # Can do everything related to one app
    APP_ADMIN = 'user:memberof:%s.backends.%s.apps.{app_id}.admins' % (ROOT_ORGANIZATION, BACKEND_ORGANIZATION)
    # Can read/update everything related to one app
    APP_EDITOR = 'user:memberof:%s.backends.%s.apps.{app_id}.editors' % (ROOT_ORGANIZATION, BACKEND_ORGANIZATION)
    APPS_CREATOR = 'user:memberof:%s.backends.%s.apps.creators' % (ROOT_ORGANIZATION, BACKEND_ORGANIZATION)
    APPS_ADMIN = 'user:memberof:%s.backends.%s.apps.admins' % (ROOT_ORGANIZATION, BACKEND_ORGANIZATION)


class Scopes(object):
    ADMIN = [Scope.ADMIN, Scope.ROOT_ADMIN]
    APPS_ADMIN = [Scope.APPS_ADMIN] + ADMIN
    APPS_CREATOR = APPS_ADMIN + [Scope.APPS_CREATOR]
    APP_ADMIN = [Scope.APP_ADMIN, Scope.BACKEND_EDITOR, Scope.BACKEND_ADMIN] + APPS_ADMIN
    APP_EDITOR = APP_ADMIN + [Scope.APP_EDITOR]
    BACKEND_ADMIN = [Scope.BACKEND_ADMIN, Scope.ADMIN] + ADMIN
    BACKEND_EDITOR = [Scope.BACKEND_EDITOR] + BACKEND_ADMIN


def decode_jwt_cached(token, verify_aud=True):
    from jose import jwt
    # memcache key should be shorter than 250 bytes
    memcache_key = 'jwt-cache-{}'.format(hashlib.sha256(token).hexdigest())
    decoded_jwt = memcache.get(key=memcache_key)  # @UndefinedVariable
    if decoded_jwt:
        return decoded_jwt
    timestamp = now()
    options = {
        'verify_aud': verify_aud
    }
    decoded_jwt = jwt.decode(token, str(ITS_YOU_ONLINE_PUBLIC_KEY), audience=JWT_AUDIENCE, issuer=JWT_ISSUER,
                             options=options)
    # Cache JWT for as long as it's valid
    memcache.set(key=memcache_key, value=decoded_jwt, time=decoded_jwt['exp'] - timestamp)  # @UndefinedVariable
    return decoded_jwt


def get_user_scopes_from_request(handler):
    from jose import ExpiredSignatureError
    """
    Args:
        handler (webapp2.RequestHandler)
    """
    authorization_header = handler.request.headers.get('Authorization')
    if not authorization_header:
        handler.abort(httplib.UNAUTHORIZED)
    split_header = authorization_header.split(' ')
    if split_header[0] == 'Bearer':
        token = split_header[1]
        try:
            decoded_jwt = decode_jwt_cached(token)
            return decoded_jwt['scope']
        except ExpiredSignatureError:
            handler.abort(httplib.UNAUTHORIZED)
        except Exception as e:
            logging.exception(e)
            raise
    else:
        logging.debug('Unknown authorization header %s', authorization_header)
        handler.abort(httplib.UNAUTHORIZED)
