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

from mcfw.consts import REST_TYPE_TO
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.bizz.payment import create_payment_provider, update_payment_provider, delete_payment_provider
from rogerthat.dal.payment import get_payment_providers, get_payment_provider
from rogerthat.settings import get_server_settings
from rogerthat.to.payment import PaymentProviderTO


@rest('/console-api/payment/providers', 'get')
@returns([PaymentProviderTO])
@arguments()
def api_list_payment_providers():
    base_url = get_server_settings().baseUrl
    return [PaymentProviderTO.from_model(base_url, provider) for provider in get_payment_providers()]


@rest('/console-api/payment/providers', 'post', type=REST_TYPE_TO)
@returns(PaymentProviderTO)
@arguments(data=PaymentProviderTO)
def api_create_payment_provider(data):
    """
    Args:
        data (CreatePaymentProviderTO)
    """
    payment_provider = create_payment_provider(data)
    base_url = get_server_settings().baseUrl
    return PaymentProviderTO.from_model(base_url, payment_provider)


@rest('/console-api/payment/providers/<provider_id:[^/]+>', 'get')
@returns(PaymentProviderTO)
@arguments(provider_id=unicode)
def api_get_payment_provider(provider_id):
    base_url = get_server_settings().baseUrl
    return PaymentProviderTO.from_model(base_url, get_payment_provider(provider_id))


@rest('/console-api/payment/providers/<provider_id:[^/]+>', 'put', type=REST_TYPE_TO)
@returns(PaymentProviderTO)
@arguments(provider_id=unicode, data=PaymentProviderTO)
def api_update_payment_providers(provider_id, data):
    """
    Args:
        provider_id (unicode)
        data (CreatePaymentProviderTO)
    """
    pp = update_payment_provider(provider_id, data)
    base_url = get_server_settings().baseUrl
    return PaymentProviderTO.from_model(base_url, pp)


@rest('/console-api/payment/providers/<provider_id:[^/]+>', 'delete', type=REST_TYPE_TO)
@returns()
@arguments(provider_id=unicode)
def api_delete_payment_provider(provider_id):
    delete_payment_provider(provider_id)
