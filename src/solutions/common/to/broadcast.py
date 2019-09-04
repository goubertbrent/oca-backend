# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
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
# @@license_version:1.5@@

from mcfw.properties import unicode_property, typed_property, bool_property, long_property, unicode_list_property
from rogerthat.to import TO
from rogerthat.to.messaging import AttachmentTO
from rogerthat.to.news import ServiceNewsGroupTO
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


class RegionalNewsSettingsTO(TO):
    enabled = bool_property('enabled')
    map_url = unicode_property('map_url')


class BroadcastOptionsTO(TO):
    tags = unicode_list_property('tags')
    regional = typed_property('regional', RegionalNewsSettingsTO)
    groups = typed_property('groups', ServiceNewsGroupTO, True)
