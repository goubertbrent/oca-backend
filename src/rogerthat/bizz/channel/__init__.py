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
import uuid

from google.appengine.ext import db

from mcfw.rpc import returns, arguments
from rogerthat.bizz.channel import firebase
from rogerthat.rpc import users
from rogerthat.settings import get_server_settings


@returns(tuple)
@arguments()
def create_channel_token():
    user = users.get_current_user()
    session = users.get_current_session()
    user_channel_id = get_uid(user.email())
    session_channel_id = get_uid(session.key())

    token = firebase.create_custom_token(user_channel_id, {'sid': session_channel_id})
    return token, user_channel_id, session_channel_id


@returns(str)
@arguments(key=(unicode, db.Key))
def get_uid(key):
    if not isinstance(key, unicode):
        key = unicode(key)

    base64_key = base64.b64encode(key)
    uid = uuid.uuid5(uuid.NAMESPACE_URL, base64_key)
    return str(uid)


def append_firebase_params(params):
    """A utility function to append firebase required parameters to a dict.

    Args:
        params (dict)
    """
    from rogerthat.models import ServiceIdentity
    session = users.get_current_session()
    if session:
        server_settings = get_server_settings()
        token, user_channel_id, session_channel_id = create_channel_token()

        params['firebase_api_key'] = server_settings.firebaseApiKey
        params['firebase_auth_domain'] = server_settings.firebaseAuthDomain
        params['firebase_database_url'] = server_settings.firebaseDatabaseUrl
        params['firebase_token'] = token
        params['user_channel_id'] = user_channel_id
        params['session_channel_id'] = session_channel_id
        params['service_identity'] = session.service_identity or ServiceIdentity.DEFAULT


def send_message(user_or_session_id, data):
    channel_id = get_uid(user_or_session_id)
    firebase.send_firebase_message(channel_id, data)
