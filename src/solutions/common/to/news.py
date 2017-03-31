# -*- coding: utf-8 -*-
# Copyright 2017 GIG Technology NV
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
# @@license_version:1.2@@

from mcfw.properties import unicode_property, long_property, bool_property, \
    typed_property

from rogerthat.to.news import NewsItemTO

class SponsoredNewsItemCount(object):
    app_id = unicode_property('app_id')
    count = long_property('cost')
    remaining_free = long_property('remaining_free')

    def __init__(self, app_id=None, count=0, remaining_free=0):
        self.app_id = app_id
        self.count = count
        self.remaining_free = remaining_free


class NewsBroadcastItemTO(NewsItemTO):
    """This will represent any additional properties for news items."""

    broadcast_on_facebook = bool_property('301')
    broadcast_on_twitter = bool_property('302')

    @staticmethod
    def from_news_item_to(news_item, on_facebook=False, on_twitter=False):
        """Create NewsBroadcastItemTO from NewsItemTO."""
        item = NewsBroadcastItemTO()
        for name, value in vars(news_item).iteritems():
            setattr(item, name, value)

        item.broadcast_on_facebook = on_facebook
        item.broadcast_on_twitter = on_twitter
        return item


class NewsBroadcastItemListTO(object):
    """A list of NewsBroadcastItemTO."""
    result = typed_property('1', NewsBroadcastItemTO, True)
    cursor = unicode_property('2')
