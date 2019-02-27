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

from mcfw.properties import unicode_property, typed_property, bool_property, long_property, unicode_list_property
from rogerthat.to import TO
from rogerthat.to.messaging import AttachmentTO
from rogerthat.to.roles import RoleTO
from shop.to import ProductTO
from solutions.common.to import TimestampTO, UrlTO


class SolutionScheduledBroadcastTO(object):
    key = unicode_property('1')
    scheduled = typed_property('2', TimestampTO, False)
    broadcast_type = unicode_property('3')
    message = unicode_property('4')
    target_audience_enabled = bool_property('5')
    target_audience_min_age = long_property('6')
    target_audience_max_age = long_property('7')
    target_audience_gender = unicode_property('8')
    attachments = typed_property('9', AttachmentTO, True)
    urls = typed_property('10', UrlTO, True)

    @staticmethod
    def fromModel(model):
        ssb = SolutionScheduledBroadcastTO()
        ssb.key = unicode(model.key_str)
        ssb.scheduled = TimestampTO.fromEpoch(model.broadcast_epoch)
        ssb.broadcast_type = model.broadcast_type
        ssb.message = model.message
        ssb.target_audience_enabled = model.target_audience_enabled
        ssb.target_audience_min_age = model.target_audience_min_age
        ssb.target_audience_max_age = model.target_audience_max_age
        ssb.target_audience_gender = model.target_audience_gender
        ssb.attachments = model.attachments
        ssb.urls = model.urls or list()
        return ssb


class BroadcastOptionsTO(TO):
    broadcast_types = unicode_list_property('1')
    editable_broadcast_types = unicode_list_property('2')
    news_promotion_product = typed_property('3', ProductTO, False)
    news_enabled = bool_property('5')
    roles = typed_property('8', RoleTO, True)
    news_settings = typed_property('9', dict)
    regional_news_enabled = bool_property('regional_news_enabled')

    def __init__(self, broadcast_types=None, editable_broadcast_types=None, news_promotion_product=None,
                 news_enabled=False, roles=None, news_settings=None, regional_news_enabled=False):
        if editable_broadcast_types is None:
            editable_broadcast_types = []
        if broadcast_types is None:
            broadcast_types = []
        if roles is None:
            roles = []

        self.broadcast_types = broadcast_types
        self.editable_broadcast_types = editable_broadcast_types
        self.news_promotion_product = news_promotion_product
        self.news_enabled = news_enabled
        self.roles = roles
        self.news_settings = news_settings.to_dict() if news_settings else {}
        self.regional_news_enabled = regional_news_enabled
