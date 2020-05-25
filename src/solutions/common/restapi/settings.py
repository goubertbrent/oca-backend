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
import logging

from mcfw.consts import REST_TYPE_TO
from mcfw.restapi import rest, GenericRESTRequestHandler
from mcfw.rpc import returns, arguments
from rogerthat.bizz.registration import get_headers_for_consent
from rogerthat.rpc import users
from shop.bizz import get_customer_consents, update_customer_consents
from shop.dal import get_customer
from solutions.common.bizz.settings import get_service_info, update_service_info, get_consents_for_app
from solutions.common.integrations.cirklo.models import VoucherSettings, VoucherProviderId
from solutions.common.models import SolutionServiceConsent
from solutions.common.to.settings import ServiceInfoTO, PrivacySettingsTO, UpdatePrivacySettingsTO


@rest('/common/service-info', 'get', read_only_access=True, silent=True)
@returns(ServiceInfoTO)
@arguments()
def rest_get_service_info():
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    return ServiceInfoTO.from_model(get_service_info(users.get_current_user(), service_identity))


@rest('/common/service-info', 'put', type=REST_TYPE_TO, silent=True, silent_result=True)
@returns(ServiceInfoTO)
@arguments(data=ServiceInfoTO)
def rest_save_service_info(data):
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    return ServiceInfoTO.from_model(update_service_info(users.get_current_user(), service_identity, data))


@rest('/common/settings/privacy', 'get', type=REST_TYPE_TO, silent=True, silent_result=True)
@returns([PrivacySettingsTO])
@arguments()
def rest_get_privacy_settings():
    customer = get_customer(users.get_current_user())
    consents = get_customer_consents(customer.user_email)
    return get_consents_for_app(customer.default_app_id, customer.language, consents.types)


@rest('/common/settings/privacy', 'put')
@returns()
@arguments(data=UpdatePrivacySettingsTO)
def save_consent(data):
    # type: (UpdatePrivacySettingsTO) -> None
    customer = get_customer(users.get_current_user())
    context = u'User dashboard'
    headers = get_headers_for_consent(GenericRESTRequestHandler.getCurrentRequest())
    update_customer_consents(customer.user_email, {data.type: data.enabled}, headers, context)
    if data.type == SolutionServiceConsent.TYPE_CIRKLO_SHARE and not data.enabled:
        voucher_settings = VoucherSettings.create_key(users.get_current_user()).get()  # type: VoucherSettings
        logging.warning(voucher_settings)
        if voucher_settings and VoucherProviderId.CIRKLO in voucher_settings.providers:
            voucher_settings.providers.remove(VoucherProviderId.CIRKLO)
            voucher_settings.put()
        logging.warning(voucher_settings)
