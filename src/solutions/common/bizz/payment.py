# -*- coding: utf-8 -*-
# Copyright 2018 Mobicage NV
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
# @@license_version:1.3@@

import json

from google.appengine.api import urlfetch
from google.appengine.ext import db

from mcfw.rpc import parse_complex_value
from rogerthat.settings import get_server_settings
from solutions.common.bizz import broadcast_updates_pending
from solutions.common.dal import get_solution_settings, \
    get_solution_identity_settings
from solutions.common.to.payments import TransactionDetailsTO
from solutions.common.utils import is_default_service_identity


def is_in_test_mode(service_user, service_identity):
    if is_default_service_identity(service_identity):
        sln_i_settings = get_solution_settings(service_user)
    else:
        sln_i_settings = get_solution_identity_settings(service_user, service_identity)
    if sln_i_settings.payment_test_mode is None:
        return False
    return sln_i_settings.payment_test_mode


def get_payment_settings(service_user, service_identity):
    sln_settings = get_solution_settings(service_user)
    if is_default_service_identity(service_identity):
        sln_i_settings = sln_settings
    else:
        sln_i_settings = get_solution_identity_settings(service_user, service_identity)
    if sln_i_settings.payment_enabled is None:
        return False, True, 0
    return sln_i_settings.payment_enabled, sln_i_settings.payment_optional, sln_settings.payment_min_amount_for_fee


def save_payment_settings(service_user, service_identity, enabled, optional, min_amount_for_fee):
    def trans():
        sln_settings = get_solution_settings(service_user)
        sln_settings.updates_pending = True
        sln_settings.payment_min_amount_for_fee = min_amount_for_fee

        if is_default_service_identity(service_identity):
            sln_i_settings = sln_settings
        else:
            sln_settings.put()
            sln_i_settings = get_solution_identity_settings(service_user, service_identity)

        sln_i_settings.payment_enabled = enabled
        sln_i_settings.payment_optional = optional
        sln_i_settings.put()
        return sln_settings

    sln_settings = db.run_in_transaction(trans)
    broadcast_updates_pending(sln_settings)


def get_transaction_details(payment_provider, transaction_id):
    # type: (unicode, unicode) -> TransactionDetailsTO
    url = u'%s/payments/transaction/%s/%s' % (get_server_settings().baseUrl, payment_provider, transaction_id)
    result = urlfetch.fetch(url)  # type: urlfetch._URLFetchResult
    if result.status_code == 200:
        return parse_complex_value(TransactionDetailsTO, json.loads(result.content), False)
    else:
        # todo proper exception
        raise Exception('Invalid status code while getting transaction details: %s\n%s' % (result.status_code,
                                                                                           result.content))
