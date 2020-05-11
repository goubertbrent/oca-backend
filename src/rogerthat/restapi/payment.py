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

from mcfw.consts import REST_TYPE_TO
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.bizz.authentication import Scopes
from rogerthat.bizz.payment import create_payment_provider, update_payment_provider, delete_payment_provider
from rogerthat.dal.payment import get_payment_providers, get_payment_provider
from rogerthat.settings import get_server_settings
from rogerthat.to.payment import PaymentProviderTO


@rest('/restapi/payment/providers', 'get', scopes=Scopes.BACKEND_EDITOR)
@returns([PaymentProviderTO])
@arguments()
def api_list_payment_providers():
    base_url = get_server_settings().baseUrl
    return [PaymentProviderTO.from_model(base_url, provider) for provider in get_payment_providers()]


@rest('/restapi/payment/providers', 'post', scopes=Scopes.BACKEND_EDITOR, type=REST_TYPE_TO)
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


@rest('/restapi/payment/providers/<provider_id:[^/]+>', 'get', scopes=Scopes.BACKEND_EDITOR)
@returns(PaymentProviderTO)
@arguments(provider_id=unicode)
def api_get_payment_provider(provider_id):
    base_url = get_server_settings().baseUrl
    return PaymentProviderTO.from_model(base_url, get_payment_provider(provider_id))


@rest('/restapi/payment/providers/<provider_id:[^/]+>', 'put', scopes=Scopes.BACKEND_EDITOR, type=REST_TYPE_TO)
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


@rest('/restapi/payment/providers/<provider_id:[^/]+>', 'delete', scopes=Scopes.BACKEND_ADMIN, type=REST_TYPE_TO)
@returns()
@arguments(provider_id=unicode)
def api_delete_payment_provider(provider_id):
    delete_payment_provider(provider_id)
