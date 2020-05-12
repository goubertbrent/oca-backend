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

from mcfw.rpc import returns, arguments
from rogerthat.rpc.rpc import capi, PRIORITY_HIGH
from rogerthat.to.payment import UpdatePaymentProviderResponseTO, UpdatePaymentProviderRequestTO, \
    UpdatePaymentStatusResponseTO, UpdatePaymentStatusRequestTO, UpdatePaymentAssetResponseTO, \
    UpdatePaymentAssetRequestTO, UpdatePaymentProvidersResponseTO, UpdatePaymentProvidersRequestTO, \
    UpdatePaymentAssetsResponseTO, UpdatePaymentAssetsRequestTO


@capi('com.mobicage.capi.payment.updatePaymentProviders', priority=PRIORITY_HIGH)
@returns(UpdatePaymentProvidersResponseTO)
@arguments(request=UpdatePaymentProvidersRequestTO)
def updatePaymentProviders(request):
    pass

@capi('com.mobicage.capi.payment.updatePaymentProvider', priority=PRIORITY_HIGH)
@returns(UpdatePaymentProviderResponseTO)
@arguments(request=UpdatePaymentProviderRequestTO)
def updatePaymentProvider(request):
    pass


@capi('com.mobicage.capi.payment.updatePaymentAssets', priority=PRIORITY_HIGH)
@returns(UpdatePaymentAssetsResponseTO)
@arguments(request=UpdatePaymentAssetsRequestTO)
def updatePaymentAssets(request):
    pass


@capi('com.mobicage.capi.payment.updatePaymentAsset', priority=PRIORITY_HIGH)
@returns(UpdatePaymentAssetResponseTO)
@arguments(request=UpdatePaymentAssetRequestTO)
def updatePaymentAsset(request):
    pass


@capi('com.mobicage.capi.payment.updatePaymentStatus', priority=PRIORITY_HIGH)
@returns(UpdatePaymentStatusResponseTO)
@arguments(request=UpdatePaymentStatusRequestTO)
def updatePaymentStatus(request):
    pass
