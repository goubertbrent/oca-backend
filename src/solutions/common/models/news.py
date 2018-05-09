# -*- coding: utf-8 -*-
# Copyright 2017 Mobicage NV
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

from google.appengine.ext import db, ndb

from mcfw.utils import Enum
from rogerthat.dal import parent_key_unsafe, parent_ndb_key
from rogerthat.models import KeyValueProperty
from rogerthat.models.common import NdbModel
from rogerthat.rpc import users
from solutions import SOLUTION_COMMON


class NewsCoupon(db.Model):
    redeemed_by = KeyValueProperty()  # [{user: 'user1@example.com', 'redeemed_on': 1473674157}]
    news_id = db.IntegerProperty()
    content = db.StringProperty(indexed=False)  # Copy of NewsItem.qr_code_caption

    @property
    def id(self):
        return self.key().id()

    @classmethod
    def create_key(cls, coupon_id, service_identity_user):
        return db.Key.from_path(cls.kind(), coupon_id, parent=cls.create_parent_key(service_identity_user))

    @classmethod
    def create_parent_key(cls, service_identity_user):
        return parent_key_unsafe(service_identity_user, SOLUTION_COMMON)

    @classmethod
    def list_by_service(cls, service_identity_user):
        return cls.all().ancestor(cls.create_parent_key(service_identity_user))

    @classmethod
    def get_by_news_id(cls, service_identity_user, news_id):
        return cls.list_by_service(service_identity_user).filter('news_id', news_id).get()


class SolutionNewsItem(NdbModel):
    paid = ndb.BooleanProperty(default=False)
    publish_time = ndb.IntegerProperty()
    reach = ndb.IntegerProperty(default=0, indexed=False)
    app_ids = ndb.StringProperty(indexed=False, repeated=True)  # contains only regional apps (not rogerthat/main app)
    service_identity = ndb.StringProperty()

    @property
    def service_user(self):
        return users.User(self.key.parent().id())

    @classmethod
    def create_key(cls, news_id, user):
        return ndb.Key(cls, news_id, parent=parent_ndb_key(user, SOLUTION_COMMON))


class NewsSettingsTags(Enum):
    FREE_REGIONAL_NEWS = 'free_regional_news'


class NewsSettings(NdbModel):
    tags = ndb.StringProperty(repeated=True, choices=NewsSettingsTags.all())

    @classmethod
    def create_key(cls, service_user, service_identity):
        return ndb.Key(cls, service_identity, parent=parent_ndb_key(service_user, SOLUTION_COMMON))

    @classmethod
    def get_by_user(cls, service_user, service_identity):
        key = cls.create_key(service_user, service_identity)
        return key.get() or cls(key=key)
