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

import logging

from mcfw.consts import REST_FLAVOR_TO
from mcfw.exceptions import HttpBadRequestException
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.rpc import users
from rogerthat.rpc.service import ServiceApiException
from rogerthat.to.payment import ServicePaymentProviderTO
from solutions.common.bizz.payment import save_payment_settings, get_providers_settings, \
    save_provider
from solutions.common.dal import get_solution_settings_or_identity_settings, get_solution_settings
from solutions.common.to.payments import PaymentSettingsTO


@rest('/common/payments/settings', 'get', read_only_access=True, silent_result=True)
@returns(PaymentSettingsTO)
@arguments()
def rest_get_payment_settings():
    service_user = users.get_current_user()
    service_identity = users.get_current_session().service_identity
    sln_settings = get_solution_settings(service_user)
    sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, service_identity)
    return PaymentSettingsTO.from_model(sln_i_settings)


@rest('/common/payments/settings', 'post')
@returns(PaymentSettingsTO)
@arguments(optional=bool)
def rest_put_payment_settings(optional):
    service_user = users.get_current_user()
    service_identity = users.get_current_session().service_identity
    try:
        sln_i_settings = save_payment_settings(service_user, service_identity, optional)
        return PaymentSettingsTO.from_model(sln_i_settings)
    except ServiceApiException as e:
        logging.exception(e)
        raise HttpBadRequestException(e.message)


@rest('/common/payments/providers', 'get', read_only_access=True, silent_result=True)
@returns([ServicePaymentProviderTO])
@arguments()
def rest_get_providers():
    service_identity = users.get_current_session().service_identity
    return get_providers_settings(users.get_current_user(), service_identity)


@rest('/common/payments/providers/<provider_id:[^/]+>', 'put', flavor=REST_FLAVOR_TO)
@returns(ServicePaymentProviderTO)
@arguments(provider_id=unicode, data=ServicePaymentProviderTO)
def rest_put_provider_settings(provider_id, data):
    # type: (unicode, ServicePaymentProviderTO) -> ServicePaymentProviderTO
    service_user = users.get_current_user()
    service_identity = users.get_current_session().service_identity
    try:
        return save_provider(service_user, service_identity, provider_id, data)
    except ServiceApiException as e:
        raise HttpBadRequestException(e.message)
