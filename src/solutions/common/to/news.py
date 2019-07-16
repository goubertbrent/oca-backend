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

from mcfw.properties import unicode_property, long_property, bool_property, \
    typed_property, unicode_list_property, long_list_property
from rogerthat.to import TO, PaginatedResultTO

from rogerthat.to.news import NewsItemTO, NewsActionButtonTO, NewsTargetAudienceTO, BaseMediaTO, NewsLocationsTO


class SponsoredNewsItemCount(TO):
    app_id = unicode_property('app_id')
    count = long_property('cost')
    remaining_free = long_property('remaining_free')

    def __init__(self, app_id=None, count=0, remaining_free=0):
        self.app_id = app_id
        self.count = count
        self.remaining_free = remaining_free


class NewsAppTO(TO):
    name = unicode_property('name')
    type = long_property('type')
    id = unicode_property('id')

    @classmethod
    def from_model(cls, app):
        return cls(name=app.name, type=app.type, id=app.app_id)


class CreateNewsItemTO(TO):
    title = unicode_property('title')
    message = unicode_property('message')
    action_button = typed_property('action_button', NewsActionButtonTO)
    type = long_property('type')
    qr_code_caption = unicode_property('qr_code_caption')
    app_ids = unicode_list_property('app_ids')
    scheduled_at = long_property('scheduled_at')
    broadcast_on_facebook = bool_property('broadcast_on_facebook')
    broadcast_on_twitter = bool_property('broadcast_on_twitter')
    facebook_access_token = unicode_property('facebook_access_token')
    target_audience = typed_property('target_audience', NewsTargetAudienceTO)
    role_ids = long_list_property('role_ids')
    tag = unicode_property('tag')
    media = typed_property('media', BaseMediaTO)
    group_type = unicode_property('group_type')
    locations = typed_property('locations', NewsLocationsTO)
    group_visible_until = long_property('group_visible_until')


class NewsBroadcastItemTO(NewsItemTO):
    """This will represent any additional properties for news items."""

    broadcast_on_facebook = bool_property('301', default=False)
    broadcast_on_twitter = bool_property('302', default=False)

    @classmethod
    def create(cls, news_item, on_facebook, on_twitter):
        item = NewsBroadcastItemTO()
        for name, value in vars(news_item).iteritems():
            setattr(item, name, value)
        item.broadcast_on_facebook = on_facebook
        item.broadcast_on_twitter = on_twitter
        return item

    @staticmethod
    def from_news_item_to(news_item, scheduled_broadcast):
        """Create NewsBroadcastItemTO from NewsItemTO."""
        item = NewsBroadcastItemTO()
        for name, value in vars(news_item).iteritems():
            setattr(item, name, value)
        if scheduled_broadcast:
            item.broadcast_on_facebook = scheduled_broadcast.broadcast_on_facebook
            item.broadcast_on_twitter = scheduled_broadcast.broadcast_on_twitter
        return item


class NewsStatsTO(TO):
    news_item = typed_property('stats', NewsBroadcastItemTO)
    apps = typed_property('apps', NewsAppTO, True)


class NewsBroadcastItemListTO(PaginatedResultTO):
    results = typed_property('1', NewsBroadcastItemTO, True)


class NewsReviewTO(TO):
    inbox_message_key = unicode_property('1')
    key = unicode_property('2')

    @classmethod
    def from_model(cls, obj):
        return cls(inbox_message_key=obj.inbox_message_key, key=obj.key.urlsafe())
