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

from google.appengine.ext import db
from mcfw.properties import unicode_property, bool_property, long_list_property, long_property, typed_property
from rogerthat.to.friends import ServiceMenuItemTO, ServiceMenuTO


class ServicePanelMenuItemTO(ServiceMenuItemTO):
    iconName = unicode_property('50')
    iconColor = unicode_property('51')
    iconUrl = unicode_property('52')
    tag = unicode_property('53')
    staticFlowName = unicode_property('54')
    isBroadcastSettings = bool_property('55')
    roles = long_list_property('56')

    @classmethod
    def from_model(cls, helper, smd, language, target_user_profile, existence=0):
        smi = super(ServicePanelMenuItemTO, cls).from_model(helper, smd, language, [], target_user_profile, existence)
        smi.iconName = smd.iconName
        smi.iconColor = smd.iconColor
        smi.iconUrl = "/mobi/service/menu/icons/lib/" + smd.iconName
        smi.tag = smd.tag
        smi.staticFlowName = helper.get_message_flow(smd.staticFlowKey).name if smd.staticFlowKey else None
        smi.isBroadcastSettings = smd.isBroadcastSettings
        smi.roles = list() if smd.roles is None else smd.roles
        return smi


class WebServiceMenuTO(ServiceMenuTO):
    shareQRId = long_property('101')
    broadcastBranding = unicode_property('102')
    items = typed_property('54', ServicePanelMenuItemTO, True)

    @classmethod
    def from_model(cls, helper, language, target_user_profile=None, existence=0):
        actionMenu = super(WebServiceMenuTO, cls).from_model(helper, language, target_user_profile, existence)
        actionMenu.broadcastBranding = helper.get_service_profile().broadcastBranding
        return actionMenu

    def _populate(self, helper, language, target_user_profile, existence=0):
        super(WebServiceMenuTO, self)._populate(helper, language, target_user_profile, existence)
        service_identity = helper.get_profile_info()
        if service_identity.shareEnabled:
            self.shareQRId = db.Key(service_identity.shareSIDKey).id()
        else:
            self.shareQRId = None

    def _populate_items(self, helper, translator, language, staticFlowBrandings, target_user_profile, existence=0):
        self.items = sorted([ServicePanelMenuItemTO.from_model(helper, smd, language, target_user_profile, existence)
                             for smd in helper.list_service_menu_items()],
                            key=lambda i: (i.coords[2], i.coords[1], i.coords[0]))
