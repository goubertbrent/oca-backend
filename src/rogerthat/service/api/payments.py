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

from mcfw.rpc import returns, arguments
from rogerthat.bizz.payment import service_put_provider, service_get_provider, service_get_providers, \
    service_delete_provider
from rogerthat.bizz.service import get_and_validate_service_identity_user
from rogerthat.rpc import users
from rogerthat.rpc.service import service_api
from rogerthat.to.payment import ServicePaymentProviderTO, ServicePaymentProviderFeeTO


@service_api(function=u'payments.put_provider')
@returns(ServicePaymentProviderTO)
@arguments(provider_id=unicode, settings=dict, service_identity=unicode, test_mode=bool, enabled=bool,
           fee=ServicePaymentProviderFeeTO)
def put_provider(provider_id, settings, service_identity=None, test_mode=False, enabled=True, fee=None):
    service_user = users.get_current_user()
    service_identity_user = get_and_validate_service_identity_user(service_user, service_identity)

    provider = service_put_provider(service_identity_user, provider_id, settings, test_mode, enabled, fee)
    return ServicePaymentProviderTO.from_model(provider)


@service_api(function=u'payments.get_provider')
@returns(ServicePaymentProviderTO)
@arguments(provider_id=unicode, service_identity=unicode, test_mode=bool)
def get_provider(provider_id, service_identity=None, test_mode=False):
    service_user = users.get_current_user()
    service_identity_user = get_and_validate_service_identity_user(service_user, service_identity)

    provider = service_get_provider(service_identity_user, provider_id, test_mode)
    if not provider:
        return None

    return ServicePaymentProviderTO.from_model(provider)


@service_api(function=u'payments.delete_provider')
@returns()
@arguments(provider_id=unicode, service_identity=unicode, test_mode=bool)
def delete_provider(provider_id, service_identity=None, test_mode=False):
    service_user = users.get_current_user()
    service_identity_user = get_and_validate_service_identity_user(service_user, service_identity)

    service_delete_provider(service_identity_user, provider_id, test_mode)


@service_api(function=u'payments.list_providers')
@returns([ServicePaymentProviderTO])
@arguments(service_identity=unicode, test_mode=bool)
def list_providers(service_identity=None, test_mode=False):
    service_user = users.get_current_user()
    service_identity_user = get_and_validate_service_identity_user(service_user, service_identity)

    return [ServicePaymentProviderTO.from_model(p) for p in service_get_providers(service_identity_user, test_mode)]
