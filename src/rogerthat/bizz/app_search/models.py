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

from google.appengine.ext import ndb

from rogerthat.bizz.communities.models import Community
from rogerthat.models.common import NdbModel


class AppSearchItemKeyword(NdbModel):
    PRIORITY_HIGH = 10
    PRIORITY_NORMAL = 5
    text = ndb.TextProperty()
    priority = ndb.IntegerProperty()


# todo multiple languages
class AppSearchItem(NdbModel):
    uid = ndb.TextProperty()
    title = ndb.TextProperty()
    description = ndb.TextProperty()
    icon = ndb.TextProperty()
    action = ndb.TextProperty()
    keywords = ndb.LocalStructuredProperty(AppSearchItemKeyword, repeated=True)


class AppSearch(NdbModel):
    items = ndb.LocalStructuredProperty(AppSearchItem, repeated=True)

    @property
    def community_id(self):
        return self.key.parent().id()

    @property
    def home_screen_id(self):
        return self.key.id()

    @classmethod
    def create_key(cls, community_id, home_screen_id):
        return ndb.Key(cls, home_screen_id, parent=Community.create_key(community_id))

    @classmethod
    def list_by_community(cls, community_id):
        return cls.query(ancestor=Community.create_key(community_id))

    def get_item_by_uid(self, uid):
        for item in self.items:
            if item.uid == uid:
                return item
        return None