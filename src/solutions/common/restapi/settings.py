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

from datetime import datetime

from mcfw.consts import REST_TYPE_TO
from mcfw.restapi import rest, GenericRESTRequestHandler
from mcfw.rpc import returns, arguments
from rogerthat.bizz.registration import get_headers_for_consent
from rogerthat.bizz.service import re_index_map_only
from rogerthat.rpc import users
from rogerthat.utils import try_or_defer
from rogerthat.utils.service import create_service_identity_user
from shop.bizz import get_customer_consents, update_customer_consents
from shop.dal import get_customer
from solutions.common.bizz.settings import get_service_info, update_service_info, get_consents_for_app
from solutions.common.integrations.cirklo.cirklo import check_merchant_whitelisted
from solutions.common.integrations.cirklo.models import CirkloMerchant,\
    CirkloCity
from solutions.common.models import SolutionServiceConsent
from solutions.common.to.settings import ServiceInfoTO, UpdatePrivacySettingsTO, PrivacySettingsGroupTO


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
@returns([PrivacySettingsGroupTO])
@arguments()
def rest_get_privacy_settings():
    customer = get_customer(users.get_current_user())
    consents = get_customer_consents(customer.user_email)
    return get_consents_for_app(customer.default_app_id, customer.language, consents.types)


@rest('/common/settings/privacy', 'put')
@returns()
@arguments(data=UpdatePrivacySettingsTO)
def save_consent(data):
    from solutions.common.dal.cityapp import get_service_user_for_city
    customer = get_customer(users.get_current_user())
    context = u'User dashboard'
    headers = get_headers_for_consent(GenericRESTRequestHandler.getCurrentRequest())
    # User can enable the consent, but can only disable the actual voucher settings.
    # This way they can't enable themselves again when the city has disabled them
    update_customer_consents(customer.user_email, {data.type: data.enabled}, headers, context)
    if data.type == SolutionServiceConsent.TYPE_CIRKLO_SHARE:
        service_user_email = customer.service_user.email()
        cirklo_merchant_key = CirkloMerchant.create_key(service_user_email)
        if data.enabled:
            cirklo_merchant = cirklo_merchant_key.get()  # type: CirkloMerchant
            if not cirklo_merchant:
                service_user = get_service_user_for_city(customer.default_app_id)
                city_id = CirkloCity.get_by_service_email(service_user.email()).city_id

                cirklo_merchant = CirkloMerchant(key=cirklo_merchant_key)
                cirklo_merchant.creation_date = datetime.utcfromtimestamp(customer.creation_time)
                cirklo_merchant.service_user_email = service_user_email
                cirklo_merchant.customer_id = customer.id
                cirklo_merchant.city_id = city_id
                cirklo_merchant.data = None
                cirklo_merchant.whitelisted = check_merchant_whitelisted(city_id, customer.user_email)
                cirklo_merchant.denied = False
                cirklo_merchant.put()
        else:
            cirklo_merchant_key.delete()

        service_identity_user = create_service_identity_user(customer.service_user)
        try_or_defer(re_index_map_only, service_identity_user)
