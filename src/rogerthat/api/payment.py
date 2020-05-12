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

from mcfw.consts import MISSING
from mcfw.rpc import returns, arguments
from rogerthat.bizz.payment import receive_payment, get_pending_payment_details, confirm_payment, cancel_payment, \
    get_payment_assets, create_payment_asset, get_pending_payment_signature_data, verify_payment_asset, \
    get_payment_transactions, get_payment_profile, get_target_info, create_transaction, get_payment_methods
from rogerthat.bizz.user import get_lang
from rogerthat.exceptions.payment import PaymentException
from rogerthat.rpc import users
from rogerthat.rpc.rpc import expose
from rogerthat.to.payment import GetPaymentProvidersResponseTO, GetPaymentProvidersRequestTO, \
    GetPaymentProfileResponseTO, GetPaymentProfileRequestTO, GetPaymentAssetsResponseTO, GetPaymentAssetsRequestTO, \
    GetPaymentTransactionsResponseTO, GetPaymentTransactionsRequestTO, VerifyPaymentAssetResponseTO, \
    VerifyPaymentAssetRequestTO, ReceivePaymentResponseTO, ReceivePaymentRequestTO, GetPendingPaymentDetailsResponseTO, \
    GetPendingPaymentDetailsRequestTO, ConfirmPaymentResponseTO, ConfirmPaymentRequestTO, CancelPaymentResponseTO, \
    CancelPaymentRequestTO, ErrorPaymentTO, CreateAssetResponseTO, CreateAssetRequestTO, \
    GetPendingPaymentSignatureDataResponseTO, GetPendingPaymentSignatureDataRequestTO, GetTargetInfoResponseTO, \
    GetTargetInfoRequestTO, CreateTransactionResponseTO, CreateTransactionRequestTO, GetPaymentMethodsRequestTO, \
    GetPaymentMethodsResponseTO
from rogerthat.translations import localize


@expose(('api',))
@returns(GetPaymentProvidersResponseTO)
@arguments(request=GetPaymentProvidersRequestTO)
def getPaymentProviders(request):
    from rogerthat.bizz.payment import get_payment_providers_for_user
    app_user = users.get_current_user()
    to = GetPaymentProvidersResponseTO()
    to.payment_providers = get_payment_providers_for_user(app_user)
    return to


@expose(('api',))
@returns(GetPaymentProfileResponseTO)
@arguments(request=GetPaymentProfileRequestTO)
def getPaymentProfile(request):
    app_user = users.get_current_user()
    return get_payment_profile(app_user, request.provider_id)


@expose(('api',))
@returns(GetPaymentAssetsResponseTO)
@arguments(request=GetPaymentAssetsRequestTO)
def getPaymentAssets(request):
    app_user = users.get_current_user()
    to = GetPaymentAssetsResponseTO()
    to.assets = get_payment_assets(app_user, request.provider_id)
    return to


@expose(('api',))
@returns(GetPaymentTransactionsResponseTO)
@arguments(request=GetPaymentTransactionsRequestTO)
def getPaymentTransactions(request):
    app_user = users.get_current_user()
    to = GetPaymentTransactionsResponseTO()
    to.transactions, to.cursor = get_payment_transactions(app_user, request.provider_id, request.asset_id,
                                                          request.cursor, request.type)
    return to


@expose(('api',))
@returns(VerifyPaymentAssetResponseTO)
@arguments(request=VerifyPaymentAssetRequestTO)
def verifyPaymentAsset(request):
    app_user = users.get_current_user()
    return _do_call(verify_payment_asset, VerifyPaymentAssetResponseTO, app_user, request.asset_id, request.code)


@expose(('api',))
@returns(ReceivePaymentResponseTO)
@arguments(request=ReceivePaymentRequestTO)
def receivePayment(request):
    app_user = users.get_current_user()
    precision = 2 if request.precision is MISSING else request.precision
    return _do_call(receive_payment, ReceivePaymentResponseTO, app_user, request.provider_id, request.asset_id,
                    request.amount, request.memo, precision)


@expose(('api',))
@returns(CancelPaymentResponseTO)
@arguments(request=CancelPaymentRequestTO)
def cancelPayment(request):
    app_user = users.get_current_user()
    return _do_call(cancel_payment, CancelPaymentResponseTO, app_user, request.transaction_id)


@expose(('api',))
@returns(GetPendingPaymentDetailsResponseTO)
@arguments(request=GetPendingPaymentDetailsRequestTO)
def getPendingPaymentDetails(request):
    app_user = users.get_current_user()
    return _do_call(get_pending_payment_details, GetPendingPaymentDetailsResponseTO, app_user, request.transaction_id)


@expose(('api',))
@returns(GetPendingPaymentSignatureDataResponseTO)
@arguments(request=GetPendingPaymentSignatureDataRequestTO)
def getPendingPaymentSignatureData(request):
    app_user = users.get_current_user()
    return _do_call(get_pending_payment_signature_data, GetPendingPaymentSignatureDataResponseTO, app_user,
                    request.transaction_id, request.asset_id)


@expose(('api',))
@returns(ConfirmPaymentResponseTO)
@arguments(request=ConfirmPaymentRequestTO)
def confirmPayment(request):
    app_user = users.get_current_user()
    return _do_call(confirm_payment, ConfirmPaymentResponseTO, app_user, request.transaction_id,
                    request.crypto_transaction)


@expose(('api',))
@returns(CreateAssetResponseTO)
@arguments(request=CreateAssetRequestTO)
def createAsset(request):
    app_user = users.get_current_user()
    return _do_call(create_payment_asset, CreateAssetResponseTO, app_user, request)


@expose(('api',))
@returns(GetTargetInfoResponseTO)
@arguments(request=GetTargetInfoRequestTO)
def getTargetInfo(request):
    app_user = users.get_current_user()
    return _do_call(get_target_info, GetTargetInfoResponseTO, app_user, request.provider_id, request.target,
                    request.currency)


@expose(('api',))
@returns(CreateTransactionResponseTO)
@arguments(request=CreateTransactionRequestTO)
def createTransaction(request):
    app_user = users.get_current_user()
    return _do_call(create_transaction, CreateTransactionResponseTO, app_user, request.provider_id, request.params)


@expose(('api',))
@returns(GetPaymentMethodsResponseTO)
@arguments(request=GetPaymentMethodsRequestTO)
def getPaymentMethods(request):
    # type: (GetPaymentMethodsRequestTO) -> GetPaymentMethodsResponseTO
    app_user = users.get_current_user()
    return get_payment_methods(request, app_user)


def _do_call(call, result_type, app_user, *args, **kwargs):
    response = result_type()
    try:
        result = call(app_user, *args, **kwargs)
        response.success = True
        if hasattr(response, 'result'):
            response.result = result
    except PaymentException as e:
        logging.warn('Handled payments error', exc_info=True)
        response.success = False
        response.error = e.error
    except Exception:
        logging.exception('Unhandled payments error')
        key = 'payments.%s' % ErrorPaymentTO.UNKNOWN
        response.error = ErrorPaymentTO(ErrorPaymentTO.UNKNOWN, localize(get_lang(app_user), key))
        response.success = False
    return response
