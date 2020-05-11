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
from rogerthat.rpc.models import RpcCAPICall
from rogerthat.rpc.rpc import mapping
from rogerthat.to.payment import UpdatePaymentProvidersResponseTO, UpdatePaymentProviderResponseTO, \
    UpdatePaymentAssetsResponseTO, UpdatePaymentAssetResponseTO, UpdatePaymentStatusResponseTO


@mapping('com.mobicage.capi.payment.update_payment_providers_response_handler')
@returns()
@arguments(context=RpcCAPICall, result=UpdatePaymentProvidersResponseTO)
def update_payment_providers_response_handler(context, result):
    pass


@mapping('com.mobicage.capi.payment.update_payment_provider_response_handler')
@returns()
@arguments(context=RpcCAPICall, result=UpdatePaymentProviderResponseTO)
def update_payment_provider_response_handler(context, result):
    pass


@mapping('com.mobicage.capi.payment.update_payment_assets_response_handler')
@returns()
@arguments(context=RpcCAPICall, result=UpdatePaymentAssetsResponseTO)
def update_payment_assets_response_handler(context, result):
    pass


@mapping('com.mobicage.capi.payment.update_payment_asset_response_handler')
@returns()
@arguments(context=RpcCAPICall, result=UpdatePaymentAssetResponseTO)
def update_payment_asset_response_handler(context, result):
    pass


@mapping('com.mobicage.capi.payment.update_payment_status_response_handler')
@returns()
@arguments(context=RpcCAPICall, result=UpdatePaymentStatusResponseTO)
def update_payment_status_response_handler(context, result):
    pass
