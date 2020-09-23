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

from mcfw.properties import unicode_property, long_property, typed_property, long_list_property
from rogerthat.to import TO

from rogerthat.to.news import NewsItemTO, NewsActionButtonTO, NewsTargetAudienceTO, BaseMediaTO, NewsLocationsTO, \
    NewsItemBasicStatisticsTO


class CreateNewsItemTO(TO):
    title = unicode_property('title')
    message = unicode_property('message')
    action_button = typed_property('action_button', NewsActionButtonTO)
    type = long_property('type')
    qr_code_caption = unicode_property('qr_code_caption')
    community_ids = long_list_property('community_ids')
    scheduled_at = long_property('scheduled_at')
    target_audience = typed_property('target_audience', NewsTargetAudienceTO)
    tag = unicode_property('tag')
    media = typed_property('media', BaseMediaTO)
    group_type = unicode_property('group_type')
    locations = typed_property('locations', NewsLocationsTO)
    group_visible_until = long_property('group_visible_until')


class NewsStatsTO(TO):
    news_item = typed_property('news_item', NewsItemTO)
    statistics = typed_property('statistics', NewsItemBasicStatisticsTO)


class NewsReviewTO(TO):
    inbox_message_key = unicode_property('1')
    key = unicode_property('2')

    @classmethod
    def from_model(cls, obj):
        return cls(inbox_message_key=obj.inbox_message_key, key=obj.key.urlsafe())
