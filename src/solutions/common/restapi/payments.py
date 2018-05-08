# -*- coding: utf-8 -*-
# Copyright 2017 Mobicage NV
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
# @@license_version:1.2@@


import json
import logging

from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.rpc import users
from rogerthat.rpc.service import ServiceApiException
from rogerthat.service.api.payments import get_provider, put_provider
from rogerthat.to import ReturnStatusTO, RETURNSTATUS_TO_SUCCESS
from solutions.common.bizz.payment import get_payment_settings, save_payment_settings, \
    is_in_test_mode
from solutions.common.to.payments import PaymentSettingsTO, PayconiqProviderTO


@rest('/common/payments/settings', 'get', read_only_access=True, silent_result=True)
@returns(PaymentSettingsTO)
@arguments()
def rest_get_payment_settings():
    service_user = users.get_current_user()
    service_identity = users.get_current_session().service_identity
    to = PaymentSettingsTO()
    to.enabled, to.optional, to.min_amount_for_fee = get_payment_settings(service_user, service_identity)
    return to


@rest('/common/payments/settings', 'post')
@returns(ReturnStatusTO)
@arguments(enabled=bool, optional=bool, min_amount_for_fee=(int, long))
def rest_put_payment_settings(enabled, optional, min_amount_for_fee):
    service_user = users.get_current_user()
    service_identity = users.get_current_session().service_identity
    try:
        save_payment_settings(service_user, service_identity, enabled, optional, min_amount_for_fee)
        return RETURNSTATUS_TO_SUCCESS
    except ServiceApiException as e:
        logging.exception(e)
        return ReturnStatusTO.create(False, None)


@rest('/common/payments/payconiq', 'get', read_only_access=True, silent_result=True)
@returns(PayconiqProviderTO)
@arguments()
def rest_get_payconiq_settings():
    service_user = users.get_current_user()
    service_identity = users.get_current_session().service_identity
    r = get_provider(u'payconiq', service_identity, is_in_test_mode(service_user, service_identity))
    return PayconiqProviderTO.fromProvider(r)


@rest('/common/payments/payconiq', 'post')
@returns(ReturnStatusTO)
@arguments(merchant_id=unicode, jwt=unicode)
def rest_put_payconiq_settings(merchant_id, jwt):
    service_user = users.get_current_user()
    service_identity = users.get_current_session().service_identity

    settings = {
        u'merchant_id': merchant_id,
        u'jwt': jwt
    }

    try:
        put_provider(u'payconiq', json.dumps(settings).decode('utf8'), service_identity, is_in_test_mode(service_user, service_identity))
        return ReturnStatusTO.create(True, None)
    except ServiceApiException as e:
        logging.exception(e)
        return ReturnStatusTO.create(False, None)
