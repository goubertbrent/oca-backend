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


class DashboardNewsMediaType(Enum):
    VIDEO_YOUTUBE = 1
    IMAGE = 2


class DashboardNews(NdbModel):
    title = ndb.StringProperty(indexed=False, required=True)
    creation_time = ndb.DateTimeProperty(auto_now_add=True)
    content = ndb.TextProperty(required=True)
    media = ndb.StringProperty(indexed=False, required=True)  # either an id or an url
    media_type = ndb.IntegerProperty(indexed=False, required=True, choices=DashboardNewsMediaType.all())
    language = ndb.StringProperty()

    @property
    def id(self):
        return self.key.integer_id()

    @classmethod
    def create_key(cls, news_id):
        return ndb.Key(cls, news_id)

    @classmethod
    def list_by_language(cls, language):
        return sorted(cls.query(cls.language == language), key=lambda i: i.creation_time, reverse=True)


class NewsReview(NdbModel):
    service_identity_user = ndb.UserProperty()
    app_id = ndb.StringProperty(indexed=False)
    host = ndb.StringProperty(indexed=False)
    is_free_regional_news = ndb.BooleanProperty(indexed=False)
    order_items = ndb.PickleProperty()
    coupon_id = ndb.IntegerProperty(indexed=False)
    image_id = ndb.IntegerProperty(indexed=False)
    broadcast_on_facebook = ndb.BooleanProperty(indexed=False)
    broadcast_on_twitter = ndb.BooleanProperty(indexed=False)
    facebook_access_token = ndb.StringProperty(indexed=False)
    data = ndb.PickleProperty()

    approved = ndb.BooleanProperty()
    inbox_message_key = ndb.StringProperty(indexed=False)

    @property
    def parent_service_user(self):
        return users.User(self.key.parent().id().encode('utf-8'))

    @classmethod
    def create_key(cls, city_service_user):
        parent = parent_ndb_key(city_service_user, SOLUTION_COMMON)
        id_ = cls.allocate_ids(1)[0]
        return ndb.Key(cls, id_, parent=parent)
