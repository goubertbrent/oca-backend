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

import uuid

from google.appengine.ext import deferred
from rogerthat.bizz.payment import sync_payment_assets
from rogerthat.dal.payment import get_payment_user_key
from rogerthat.models.payment import PaymentOauthLoginState, PaymentUser, PaymentUserProvider
from rogerthat.utils import now
from rogerthat.utils.transactions import run_in_transaction


def create_login_state(app_user, provider_id):
    state = str(uuid.uuid4())
    login_state = PaymentOauthLoginState(key=PaymentOauthLoginState.create_key(state))
    login_state.timestamp = now()
    login_state.provider_id = provider_id
    login_state.app_user = app_user
    login_state.code = None
    login_state.completed = False
    login_state.put()
    return state


def add_code_to_login_state(state, code):
    login_state = PaymentOauthLoginState.create_key(state).get()
    if not login_state:
        return None
    if login_state.code:
        return None
    login_state.code = code
    login_state.put()
    return login_state.app_id


def get_login_state(state):
    return PaymentOauthLoginState.create_key(state).get()


def finish_login_state(state, token):
    def trans():
        login_state = PaymentOauthLoginState.create_key(state).get()
        if not login_state:
            return False
        if login_state.completed:
            return False
        login_state.completed = True
        login_state.put()

        payment_user_key = get_payment_user_key(login_state.app_user)
        payment_user = payment_user_key.get()
        if not payment_user:
            payment_user = PaymentUser(key=payment_user_key)
            payment_user.providers = []
            payment_user.assets = []

        pup = payment_user.get_provider(login_state.provider_id)
        if pup:
            pup.token = token
        else:
            payment_user.providers.append(PaymentUserProvider(provider_id=login_state.provider_id, token=token))
        payment_user.put()

        deferred.defer(sync_payment_assets, login_state.app_user, login_state.provider_id, True, _transactional=True)

        return True
    return run_in_transaction(trans, True)
