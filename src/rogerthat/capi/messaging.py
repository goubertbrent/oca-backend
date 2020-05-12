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
from rogerthat.to.messaging import NewMessageResponseTO, NewMessageRequestTO, MemberStatusUpdateRequestTO, \
    MemberStatusUpdateResponseTO, MessageLockedRequestTO, MessageLockedResponseTO, ConversationDeletedRequestTO, \
    ConversationDeletedResponseTO, EndMessageFlowResponseTO, EndMessageFlowRequestTO, TransferCompletedResponseTO, \
    TransferCompletedRequestTO, StartFlowResponseTO, StartFlowRequestTO, UpdateMessageResponseTO, UpdateMessageRequestTO
from rogerthat.to.messaging.forms import NewTextLineFormResponseTO, NewTextLineFormRequestTO, \
    NewTextBlockFormResponseTO, NewTextBlockFormRequestTO, NewAutoCompleteFormResponseTO, NewAutoCompleteFormRequestTO, \
    NewSingleSelectFormResponseTO, NewSingleSelectFormRequestTO, NewMultiSelectFormResponseTO, \
    NewMultiSelectFormRequestTO, \
    NewSingleSliderFormResponseTO, NewSingleSliderFormRequestTO, NewRangeSliderFormResponseTO, \
    NewRangeSliderFormRequestTO, \
    UpdateTextLineFormResponseTO, UpdateTextLineFormRequestTO, UpdateTextBlockFormResponseTO, \
    UpdateTextBlockFormRequestTO, \
    UpdateAutoCompleteFormResponseTO, UpdateAutoCompleteFormRequestTO, UpdateSingleSelectFormResponseTO, \
    UpdateSingleSelectFormRequestTO, UpdateMultiSelectFormResponseTO, UpdateMultiSelectFormRequestTO, \
    UpdateSingleSliderFormResponseTO, UpdateSingleSliderFormRequestTO, UpdateRangeSliderFormResponseTO, \
    UpdateRangeSliderFormRequestTO, NewDateSelectFormResponseTO, NewDateSelectFormRequestTO, \
    UpdateDateSelectFormResponseTO, \
    UpdateDateSelectFormRequestTO, NewPhotoUploadFormResponseTO, NewPhotoUploadFormRequestTO, \
    UpdatePhotoUploadFormResponseTO, UpdatePhotoUploadFormRequestTO, NewGPSLocationFormRequestTO, \
    NewGPSLocationFormResponseTO, UpdateGPSLocationFormResponseTO, UpdateGPSLocationFormRequestTO, \
    NewMyDigiPassFormResponseTO, NewMyDigiPassFormRequestTO, UpdateMyDigiPassFormResponseTO, \
    UpdateMyDigiPassFormRequestTO, NewAdvancedOrderFormResponseTO, NewAdvancedOrderFormRequestTO, \
    UpdateAdvancedOrderFormResponseTO, UpdateAdvancedOrderFormRequestTO, NewFriendSelectFormResponseTO, \
    NewFriendSelectFormRequestTO, UpdateFriendSelectFormResponseTO, UpdateFriendSelectFormRequestTO, \
    UpdateSignFormResponseTO, UpdateSignFormRequestTO, NewSignFormResponseTO, NewSignFormRequestTO, \
    NewOauthFormResponseTO, NewOauthFormRequestTO, UpdateOauthFormResponseTO, UpdateOauthFormRequestTO, \
    NewPayFormResponseTO, NewPayFormRequestTO, UpdatePayFormResponseTO, UpdatePayFormRequestTO, NewOpenIdFormResponseTO, \
    NewOpenIdFormRequestTO, UpdateOpenIdFormResponseTO, UpdateOpenIdFormRequestTO


@capi('com.mobicage.capi.messaging.newMessage', priority=PRIORITY_HIGH)
@returns(NewMessageResponseTO)
@arguments(request=NewMessageRequestTO)
def newMessage(request):
    pass


@capi('com.mobicage.capi.messaging.updateMessage')
@returns(UpdateMessageResponseTO)
@arguments(request=UpdateMessageRequestTO)
def updateMessage(request):
    pass


@capi('com.mobicage.capi.messaging.updateMessageMemberStatus')
@returns(MemberStatusUpdateResponseTO)
@arguments(request=MemberStatusUpdateRequestTO)
def updateMessageMemberStatus(request):
    pass


@capi('com.mobicage.capi.messaging.messageLocked')
@returns(MessageLockedResponseTO)
@arguments(request=MessageLockedRequestTO)
def messageLocked(request):
    pass


@capi('com.mobicage.capi.messaging.conversationDeleted')
@returns(ConversationDeletedResponseTO)
@arguments(request=ConversationDeletedRequestTO)
def conversationDeleted(request):
    pass


@capi('com.mobicage.capi.messaging.newTextLineForm', accept_sub_types=True, priority=PRIORITY_HIGH)
@returns(NewTextLineFormResponseTO)
@arguments(request=NewTextLineFormRequestTO)
def newTextLineForm(request):
    pass


@capi('com.mobicage.capi.messaging.newTextBlockForm', accept_sub_types=True, priority=PRIORITY_HIGH)
@returns(NewTextBlockFormResponseTO)
@arguments(request=NewTextBlockFormRequestTO)
def newTextBlockForm(request):
    pass


@capi('com.mobicage.capi.messaging.newAutoCompleteForm', accept_sub_types=True, priority=PRIORITY_HIGH)
@returns(NewAutoCompleteFormResponseTO)
@arguments(request=NewAutoCompleteFormRequestTO)
def newAutoCompleteForm(request):
    pass


@capi('com.mobicage.capi.messaging.newFriendSelectForm', accept_sub_types=True, priority=PRIORITY_HIGH)
@returns(NewFriendSelectFormResponseTO)
@arguments(request=NewFriendSelectFormRequestTO)
def newFriendSelectForm(request):
    pass


@capi('com.mobicage.capi.messaging.newSingleSelectForm', accept_sub_types=True, priority=PRIORITY_HIGH)
@returns(NewSingleSelectFormResponseTO)
@arguments(request=NewSingleSelectFormRequestTO)
def newSingleSelectForm(request):
    pass


@capi('com.mobicage.capi.messaging.newMultiSelectForm', accept_sub_types=True, priority=PRIORITY_HIGH)
@returns(NewMultiSelectFormResponseTO)
@arguments(request=NewMultiSelectFormRequestTO)
def newMultiSelectForm(request):
    pass


@capi('com.mobicage.capi.messaging.newDateSelectForm', accept_sub_types=True, priority=PRIORITY_HIGH)
@returns(NewDateSelectFormResponseTO)
@arguments(request=NewDateSelectFormRequestTO)
def newDateSelectForm(request):
    pass


@capi('com.mobicage.capi.messaging.newSingleSliderForm', accept_sub_types=True, priority=PRIORITY_HIGH)
@returns(NewSingleSliderFormResponseTO)
@arguments(request=NewSingleSliderFormRequestTO)
def newSingleSliderForm(request):
    pass


@capi('com.mobicage.capi.messaging.newRangeSliderForm', accept_sub_types=True, priority=PRIORITY_HIGH)
@returns(NewRangeSliderFormResponseTO)
@arguments(request=NewRangeSliderFormRequestTO)
def newRangeSliderForm(request):
    pass


@capi('com.mobicage.capi.messaging.newPhotoUploadForm', accept_sub_types=True, priority=PRIORITY_HIGH)
@returns(NewPhotoUploadFormResponseTO)
@arguments(request=NewPhotoUploadFormRequestTO)
def newPhotoUploadForm(request):
    pass


@capi('com.mobicage.capi.messaging.newGPSLocationForm', accept_sub_types=True, priority=PRIORITY_HIGH)
@returns(NewGPSLocationFormResponseTO)
@arguments(request=NewGPSLocationFormRequestTO)
def newGPSLocationForm(request):
    pass


@capi('com.mobicage.capi.messaging.newMyDigiPassForm', accept_sub_types=True, priority=PRIORITY_HIGH)
@returns(NewMyDigiPassFormResponseTO)
@arguments(request=NewMyDigiPassFormRequestTO)
def newMyDigiPassForm(request):
    pass


@capi('com.mobicage.capi.messaging.newOpenIdForm', accept_sub_types=True, priority=PRIORITY_HIGH)
@returns(NewOpenIdFormResponseTO)
@arguments(request=NewOpenIdFormRequestTO)
def newOpenIdForm(request):
    pass


@capi('com.mobicage.capi.messaging.newAdvancedOrderForm', accept_sub_types=True, priority=PRIORITY_HIGH)
@returns(NewAdvancedOrderFormResponseTO)
@arguments(request=NewAdvancedOrderFormRequestTO)
def newAdvancedOrderForm(request):
    pass


@capi('com.mobicage.capi.messaging.newSignForm', accept_sub_types=True, priority=PRIORITY_HIGH)
@returns(NewSignFormResponseTO)
@arguments(request=NewSignFormRequestTO)
def newSignForm(request):
    pass


@capi('com.mobicage.capi.messaging.newOauthForm', accept_sub_types=True, priority=PRIORITY_HIGH)
@returns(NewOauthFormResponseTO)
@arguments(request=NewOauthFormRequestTO)
def newOauthForm(request):
    pass


@capi('com.mobicage.capi.messaging.newPayForm', accept_sub_types=True, priority=PRIORITY_HIGH)
@returns(NewPayFormResponseTO)
@arguments(request=NewPayFormRequestTO)
def newPayForm(request):
    pass


@capi('com.mobicage.capi.messaging.updateTextLineForm', accept_sub_types=True)
@returns(UpdateTextLineFormResponseTO)
@arguments(request=UpdateTextLineFormRequestTO)
def updateTextLineForm(request):
    pass


@capi('com.mobicage.capi.messaging.updateTextBlockForm', accept_sub_types=True)
@returns(UpdateTextBlockFormResponseTO)
@arguments(request=UpdateTextBlockFormRequestTO)
def updateTextBlockForm(request):
    pass


@capi('com.mobicage.capi.messaging.updateAutoCompleteForm', accept_sub_types=True)
@returns(UpdateAutoCompleteFormResponseTO)
@arguments(request=UpdateAutoCompleteFormRequestTO)
def updateAutoCompleteForm(request):
    pass


@capi('com.mobicage.capi.messaging.updateFriendSelectForm', accept_sub_types=True)
@returns(UpdateFriendSelectFormResponseTO)
@arguments(request=UpdateFriendSelectFormRequestTO)
def updateFriendSelectForm(request):
    pass


@capi('com.mobicage.capi.messaging.updateSingleSelectForm', accept_sub_types=True)
@returns(UpdateSingleSelectFormResponseTO)
@arguments(request=UpdateSingleSelectFormRequestTO)
def updateSingleSelectForm(request):
    pass


@capi('com.mobicage.capi.messaging.updateMultiSelectForm', accept_sub_types=True)
@returns(UpdateMultiSelectFormResponseTO)
@arguments(request=UpdateMultiSelectFormRequestTO)
def updateMultiSelectForm(request):
    pass


@capi('com.mobicage.capi.messaging.updateDateSelectForm', accept_sub_types=True)
@returns(UpdateDateSelectFormResponseTO)
@arguments(request=UpdateDateSelectFormRequestTO)
def updateDateSelectForm(request):
    pass


@capi('com.mobicage.capi.messaging.updateSingleSliderForm', accept_sub_types=True)
@returns(UpdateSingleSliderFormResponseTO)
@arguments(request=UpdateSingleSliderFormRequestTO)
def updateSingleSliderForm(request):
    pass


@capi('com.mobicage.capi.messaging.updateRangeSliderForm', accept_sub_types=True)
@returns(UpdateRangeSliderFormResponseTO)
@arguments(request=UpdateRangeSliderFormRequestTO)
def updateRangeSliderForm(request):
    pass


@capi('com.mobicage.capi.messaging.updatePhotoUploadForm', accept_sub_types=True)
@returns(UpdatePhotoUploadFormResponseTO)
@arguments(request=UpdatePhotoUploadFormRequestTO)
def updatePhotoUploadForm(request):
    pass


@capi('com.mobicage.capi.messaging.updateGPSLocationForm', accept_sub_types=True)
@returns(UpdateGPSLocationFormResponseTO)
@arguments(request=UpdateGPSLocationFormRequestTO)
def updateGPSLocationForm(request):
    pass


@capi('com.mobicage.capi.messaging.updateMyDigiPassForm', accept_sub_types=True)
@returns(UpdateMyDigiPassFormResponseTO)
@arguments(request=UpdateMyDigiPassFormRequestTO)
def updateMyDigiPassForm(request):
    pass


@capi('com.mobicage.capi.messaging.updateOpenIdForm', accept_sub_types=True)
@returns(UpdateOpenIdFormResponseTO)
@arguments(request=UpdateOpenIdFormRequestTO)
def updateOpenIdForm(request):
    pass


@capi('com.mobicage.capi.messaging.updateAdvancedOrderForm', accept_sub_types=True)
@returns(UpdateAdvancedOrderFormResponseTO)
@arguments(request=UpdateAdvancedOrderFormRequestTO)
def updateAdvancedOrderForm(request):
    pass


@capi('com.mobicage.capi.messaging.updateSignForm', accept_sub_types=True)
@returns(UpdateSignFormResponseTO)
@arguments(request=UpdateSignFormRequestTO)
def updateSignForm(request):
    pass


@capi('com.mobicage.capi.messaging.updateOauthForm', accept_sub_types=True)
@returns(UpdateOauthFormResponseTO)
@arguments(request=UpdateOauthFormRequestTO)
def updateOauthForm(request):
    pass


@capi('com.mobicage.capi.messaging.updatePayForm', accept_sub_types=True)
@returns(UpdatePayFormResponseTO)
@arguments(request=UpdatePayFormRequestTO)
def updatePayForm(request):
    pass


@capi('com.mobicage.capi.messaging.endMessageFlow', accept_sub_types=True)
@returns(EndMessageFlowResponseTO)
@arguments(request=EndMessageFlowRequestTO)
def endMessageFlow(request):
    pass


@capi('com.mobicage.capi.messaging.transferCompleted', accept_sub_types=True)
@returns(TransferCompletedResponseTO)
@arguments(request=TransferCompletedRequestTO)
def transferCompleted(request):
    pass


@capi('com.mobicage.capi.messaging.startFlow', accept_sub_types=True)
@returns(StartFlowResponseTO)
@arguments(request=StartFlowRequestTO)
def startFlow(request):
    pass
