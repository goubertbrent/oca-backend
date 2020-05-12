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

from mcfw.rpc import arguments, returns
from rogerthat.rpc.rpc import capi, PRIORITY_HIGH
from rogerthat.to.news import DisableNewsResponseTO, DisableNewsRequestTO, NewNewsResponseTO, NewNewsRequestTO, \
    CreateNotificationResponseTO, CreateNotificationRequestTO, \
    UpdateBadgeCountResponseTO, UpdateBadgeCountRequestTO


@capi('com.mobicage.capi.news.newNews', priority=PRIORITY_HIGH)
@returns(NewNewsResponseTO)
@arguments(request=NewNewsRequestTO)
def newNews(request):
    pass

@capi('com.mobicage.capi.news.disableNews')
@returns(DisableNewsResponseTO)
@arguments(request=DisableNewsRequestTO)
def disableNews(request):
    pass


@capi('com.mobicage.capi.news.createNotification')
@returns(CreateNotificationResponseTO)
@arguments(request=CreateNotificationRequestTO)
def createNotification(request):
    pass


@capi('com.mobicage.capi.news.updateBadgeCount')
@returns(UpdateBadgeCountResponseTO)
@arguments(request=UpdateBadgeCountRequestTO)
def updateBadgeCount(request):
    pass
