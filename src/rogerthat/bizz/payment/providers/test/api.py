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
from rogerthat.bizz.payment.providers.test.consts import PAYMENT_PROVIDER_ID
from rogerthat.rpc import users
from rogerthat.to.payment import GetPaymentProfileResponseTO, PaymentProviderAssetTO, \
    CreatePaymentAssetTO,  CryptoTransactionTO, PaymentAssetBalanceTO


@returns(PaymentProviderAssetTO)
@arguments()
def create_test_asset():
    to = PaymentProviderAssetTO()
    to.provider_id = PAYMENT_PROVIDER_ID
    to.id = u"test"
    to.type = u"account"
    to.name = u"Name"
    to.currency = u"CURRENCY"
    to.available_balance = PaymentAssetBalanceTO()
    to.available_balance.amount = 123
    to.available_balance.description = None
    to.total_balance = None
    to.verified = True
    to.enabled = True
    to.has_balance = True
    to.has_transactions = True
    return to


def web_callback(self, path, params):
    self.abort(404)


@returns(GetPaymentProfileResponseTO)
@arguments(app_user=users.User)
def get_payment_profile(app_user):
    response = GetPaymentProfileResponseTO()

    response.first_name = u"test"
    response.last_name = u"user"

    return response


@returns([PaymentProviderAssetTO])
@arguments(app_user=users.User, currency=unicode)
def get_payment_assets(app_user, currency=None):
    return [create_test_asset()]


@returns(PaymentProviderAssetTO)
@arguments(app_user=users.User, asset_id=unicode)
def get_payment_asset(app_user, asset_id):
    return create_test_asset()


@returns(unicode)
@arguments(app_user=users.User, asset_id=unicode)
def get_payment_asset_currency(app_user, asset_id):
    return u"CURRENCY"


@returns(PaymentProviderAssetTO)
@arguments(app_user=users.User, asset=CreatePaymentAssetTO)
def create_payment_asset(app_user, asset):
    raise NotImplementedError('create_payment_asset is not implemented yet')


@returns(tuple)
@arguments(app_user=users.User, asset_id=unicode, cursor=unicode)
def get_confirmed_transactions(app_user, asset_id, cursor=None):
    return [], None


@returns(tuple)
@arguments(app_user=users.User, asset_id=unicode, cursor=unicode)
def get_pending_transactions(app_user, asset_id, cursor=None):
    return [], None


@returns()
@arguments(app_user=users.User, asset_id=unicode, code=unicode)
def verify_payment_asset(app_user, asset_id, code):
    raise NotImplementedError('verify_payment_asset is not implemented yet')


@returns(CryptoTransactionTO)
@arguments(app_user=users.User, transaction_id=unicode, from_asset_id=unicode, to_asset_id=unicode, amount=(int, long),
           currency=unicode, memo=unicode)
def get_payment_signature_data(app_user, transaction_id, from_asset_id, to_asset_id, amount, currency, memo):
    return None


@returns(unicode)
@arguments(from_user=users.User, to_user=users.User, transaction_id=unicode, from_asset_id=unicode, to_asset_id=unicode, amount=(int, long),
           currency=unicode, memo=unicode, crypto_transaction=CryptoTransactionTO)
def confirm_payment(from_user, to_user, transaction_id, from_asset_id, to_asset_id, amount, currency, memo, crypto_transaction):
    raise NotImplementedError('confirm_payment is not implemented yet')
