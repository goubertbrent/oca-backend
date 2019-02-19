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

from google.appengine.ext import db, ndb
from google.appengine.ext.deferred import deferred

from mcfw.properties import azzert
from rogerthat.bizz.payment import get_api_module
from rogerthat.bizz.payment.providers.threefold.api import _get_total_amount
from rogerthat.consts import DEBUG
from rogerthat.dal.service import get_service_identity
from rogerthat.models import ServiceIdentity
from rogerthat.rpc import users
from rogerthat.service.api.payments import list_providers, put_provider
from rogerthat.to.payment import ServicePaymentProviderTO, PAYMENT_SETTINGS_MAPPING, ServicePaymentProviderFeeTO
from rogerthat.utils.channel import send_message
from rogerthat.utils.service import create_service_identity_user
from solutions.common.bizz import broadcast_updates_pending
from solutions.common.dal import get_solution_settings, get_solution_identity_settings, \
    get_solution_settings_or_identity_settings
from solutions.common.models.payment import PaymentTransaction
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
                provider = ServicePaymentProviderTO(provider_id=provider_id,
                                                    fee=ServicePaymentProviderFeeTO(
                                                        amount=ServicePaymentProviderFeeTO.amount.default,
                                                        precision=ServicePaymentProviderFeeTO.precision.default,
                                                        currency=None
                                                    ),
                                                    enabled=False)
                provider.settings = PAYMENT_SETTINGS_MAPPING[provider_id]()
                results.append(provider)
        return results


def get_visible_payment_providers(service_user, service_identity, test_mode):
    default_app_id = get_service_identity(create_service_identity_user(service_user, service_identity)).defaultAppId
    providers = []
    if DEBUG or default_app_id.startswith('osa-'):
        return ['payconiq', 'threefold_testnet']
    if default_app_id.startswith('be-'):
        providers.append('payconiq')
    # In the future the `if 'threefold'` will be removed
    if 'threefold' in default_app_id:
        if test_mode:
            providers.append('threefold_testnet')
        else:
            providers.append('threefold')
    return providers


def get_transaction_details(payment_provider, transaction_id, service_user, service_identity, app_user):
    # type: (unicode, unicode, users.User, unicode, users.User) -> TransactionDetailsTO
    mod = get_api_module(payment_provider)
    if payment_provider == 'payconiq':
        transaction = mod.get_public_transaction(transaction_id)
        return TransactionDetailsTO.from_dict(transaction)
    elif payment_provider in ['threefold', 'threefold_testnet']:
        settings_mapping = {p.provider_id: p.settings for p in get_providers_settings(service_user, service_identity)}
        tf_settings = settings_mapping[payment_provider]  # type: ThreeFoldSettingsTO
        service_address = tf_settings.address
        azzert(tf_settings.address)
        transaction = mod.get_public_transaction(transaction_id)
        amount = _get_total_amount(transaction, service_address)
        azzert(amount)
        status = PaymentTransaction.STATUS_SUCCEEDED
        if transaction['unconfirmed']:  # Usually will be true
            status = PaymentTransaction.STATUS_PENDING
        # Transaction id = external transaction id for ThreeFold transactions
        transaction_key = PaymentTransaction.create_key(payment_provider, transaction_id)
        transaction_model = PaymentTransaction(
            key=transaction_key,
            test_mode=False,
            target=service_address,
            currency='TFT',
            amount=amount,
            precision=9,
            app_user=app_user.email(),
            status=status,
            external_id=transaction_id,
            service_user=service_user.email())
        if status == PaymentTransaction.STATUS_PENDING:
            deferred.defer(_check_transaction_completed, transaction_key, _countdown=60)
        else:
            transaction_model.timestamp = mod.get_timestamp_from_block(transaction['transaction']['height'])
        transaction_model.put()
        return TransactionDetailsTO.from_model(transaction_model)
    else:
        raise Exception('Unknown payment provider %s' % payment_provider)


@ndb.transactional(xg=True)
def _check_transaction_completed(transaction_key):
    transaction = transaction_key.get()  # type: PaymentTransaction
    if transaction.status != PaymentTransaction.STATUS_PENDING:
        return
    mod = get_api_module(transaction.provider_id)
    try:
        ext_trans = mod.get_public_transaction(transaction.external_id)
    except Exception as e:
        logging.exception(e.message)
        if 'unrecognized hash' in e.message:  # in case of a fork this transaction will not exist
            transaction.status = PaymentTransaction.STATUS_FAILED
            transaction.put()
            deferred.defer(send_message, transaction.service_user, u'solutions.common.orders.update',
                           _transactional=True)
        return
    if ext_trans['unconfirmed']:
        deferred.defer(_check_transaction_completed, transaction_key, _transactional=True, _countdown=60)
    else:
        transaction.status = PaymentTransaction.STATUS_SUCCEEDED
        transaction.timestamp = mod.get_timestamp_from_block(ext_trans['transaction']['height'])
        transaction.put()
        deferred.defer(send_message, transaction.service_user, u'solutions.common.orders.update', _transactional=True)
