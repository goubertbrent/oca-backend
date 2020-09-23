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

from google.appengine.ext import db

from rogerthat.bizz.communities.communities import get_community
from rogerthat.bizz.payment import get_api_module
from rogerthat.consts import DEBUG
from rogerthat.dal.profile import get_service_profile
from rogerthat.models import ServiceIdentity
from rogerthat.rpc import users
from rogerthat.service.api.payments import list_providers, put_provider
from rogerthat.to.payment import ServicePaymentProviderTO, PAYMENT_SETTINGS_MAPPING, ServicePaymentProviderFeeTO
from solutions.common.bizz import broadcast_updates_pending
from solutions.common.dal import get_solution_settings, get_solution_identity_settings, \
    get_solution_settings_or_identity_settings
from solutions.common.to.payments import TransactionDetailsTO
from solutions.common.utils import is_default_service_identity


def is_in_test_mode(service_user, service_identity):
    # type: (users.User, unicode) -> bool
    if is_default_service_identity(service_identity):
        sln_i_settings = get_solution_settings(service_user)
    else:
        sln_i_settings = get_solution_identity_settings(service_user, service_identity)
    return sln_i_settings.payment_test_mode


def save_payment_settings(service_user, service_identity, optional):
    def trans():
        sln_settings = get_solution_settings(service_user)
        sln_settings.updates_pending = True

        if is_default_service_identity(service_identity):
            sln_i_settings = sln_settings
        else:
            sln_settings.put()
            sln_i_settings = get_solution_identity_settings(service_user, service_identity)

        sln_i_settings.payment_optional = optional
        sln_i_settings.put()
        return sln_settings, sln_i_settings

    sln_settings, sln_i_settings = db.run_in_transaction(trans)
    broadcast_updates_pending(sln_settings)
    return sln_i_settings


def save_provider(service_user, service_identity, provider_id, data):
    # type: (users.User, unicode, unicode, ServicePaymentProviderTO) -> ServicePaymentProviderTO
    sln_settings = get_solution_settings(service_user)
    sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, service_identity)
    sln_settings.updates_pending = True
    provider = put_provider(provider_id, data.settings.to_dict(), service_identity, sln_i_settings.payment_test_mode,
                            data.enabled, data.fee)
    sln_i_settings.payment_enabled = any(p.is_enabled for p in get_providers_settings(service_user, service_identity))
    db.put([sln_i_settings, sln_settings])
    broadcast_updates_pending(sln_settings)
    return provider


def get_providers_settings(service_user, service_identity):
    # type: (users.User, unicode) -> list[ServicePaymentProviderTO]
    service_identity = service_identity or ServiceIdentity.DEFAULT
    test_mode = is_in_test_mode(service_user, service_identity)
    results = []
    visible_providers = get_visible_payment_providers(service_user, service_identity, test_mode)
    with users.set_user(service_user):
        providers = {provider.provider_id: provider for provider in list_providers(service_identity, test_mode)}
        for provider_id in visible_providers:
            provider = providers.get(provider_id)
            if provider:
                results.append(provider)
            else:
                provider = ServicePaymentProviderTO(
                    provider_id=provider_id,
                    fee=ServicePaymentProviderFeeTO(
                        amount=ServicePaymentProviderFeeTO.amount.default,  # @UndefinedVariable
                        precision=ServicePaymentProviderFeeTO.precision.default,  # @UndefinedVariable
                        currency=None
                    ),
                    enabled=False)
                provider.settings = PAYMENT_SETTINGS_MAPPING[provider_id]()
                results.append(provider)
        return results


def get_visible_payment_providers(service_user, service_identity, test_mode):
    community = get_community(get_service_profile(service_user).community_id)
    providers = []
    if DEBUG or community.demo:
        return ['payconiq']
    if community.country == 'BE':
        providers.append('payconiq')
    return providers


def get_transaction_details(payment_provider, transaction_id, service_user, service_identity, app_user):
    # type: (unicode, unicode, users.User, unicode, users.User) -> TransactionDetailsTO
    mod = get_api_module(payment_provider)
    if payment_provider == 'payconiq':
        transaction = mod.get_public_transaction(transaction_id)
        return TransactionDetailsTO.from_dict(transaction)
    else:
        raise Exception('Unknown payment provider %s' % payment_provider)
