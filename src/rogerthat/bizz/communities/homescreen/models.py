# -*- coding: utf-8 -*-
# Copyright 2020 Green Valley NV
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
from google.appengine.ext import ndb

from rogerthat.bizz.communities.models import Community
from rogerthat.models import NdbModel


class CommunityHomeScreen(NdbModel):
    data = ndb.JsonProperty()  # See oca.models.HomeScreen
    update_date = ndb.DateTimeProperty(auto_now=True)
    community_id = ndb.IntegerProperty()

    @property
    def id(self):
        return self.key.id()

    @classmethod
    def create_key(cls, community_id, home_screen_id):
        return ndb.Key(cls, home_screen_id, parent=Community.create_key(community_id))

    @classmethod
    def list_by_community(cls, community_id):
        return cls.query().filter(cls.community_id == community_id)


class HomeScreenTestUser(NdbModel):
    reset_date = ndb.DateTimeProperty(required=True)
    community_id = ndb.IntegerProperty(required=True)
    home_screen_id = ndb.StringProperty(required=True)

    @property
    def user_email(self):
        return self.key.id()

    @classmethod
    def create_key(cls, user_id):
        return ndb.Key(cls, user_id)

    @classmethod
    def list_expired(cls, date):
        return cls.query().filter(cls.reset_date < date)
