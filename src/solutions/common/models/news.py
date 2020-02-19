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

from google.appengine.ext import ndb
from typing import List

from mcfw.utils import Enum
from rogerthat.dal import parent_ndb_key, parent_ndb_key_unsafe
from rogerthat.models.common import NdbModel
from rogerthat.rpc import users
from solutions import SOLUTION_COMMON


class RedeemedBy(NdbModel):
    user = ndb.StringProperty()
    redeemed_on = ndb.IntegerProperty()


class NewsCoupon(NdbModel):
    content = ndb.StringProperty(indexed=False)  # Copy of NewsItem.qr_code_caption
    news_id = ndb.IntegerProperty()
    redeemed_by = ndb.LocalStructuredProperty(RedeemedBy, compressed=True, repeated=True)  # type: list[RedeemedBy]

    @property
    def id(self):
        return self.key.id()

    @classmethod
    def create_key(cls, coupon_id, service_identity_user):
        return ndb.Key(cls, coupon_id, parent=cls.create_parent_key(service_identity_user))

    @classmethod
    def create_parent_key(cls, service_identity_user):
        return parent_ndb_key_unsafe(service_identity_user, SOLUTION_COMMON)

    @classmethod
    def list_by_service(cls, service_identity_user):
        return cls.query(ancestor=cls.create_parent_key(service_identity_user))

    @classmethod
    def get_by_news_id(cls, service_identity_user, news_id):
        return cls.list_by_service(service_identity_user).filter(cls.news_id == news_id).get()


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
    FREE_REGIONAL_NEWS = u'free_regional_news'


class NewsSettings(NdbModel):
    tags = ndb.StringProperty(repeated=True, choices=NewsSettingsTags.all())  # type: List[str]

    @classmethod
    def create_key(cls, service_user, service_identity):
        return ndb.Key(cls, service_identity, parent=parent_ndb_key(service_user, SOLUTION_COMMON))


class NewsReview(NdbModel):
    service_identity_user = ndb.UserProperty()
    app_id = ndb.StringProperty(indexed=False)
    is_free_regional_news = ndb.BooleanProperty(indexed=False)
    coupon_id = ndb.IntegerProperty(indexed=False)
    image_id = ndb.IntegerProperty(indexed=False)
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


class Street(NdbModel):
    name = ndb.StringProperty()
    id = ndb.IntegerProperty()


class LocationBounds(NdbModel):
    northeast = ndb.GeoPtProperty()
    southwest = ndb.GeoPtProperty()


class Locality(NdbModel):
    postal_code = ndb.StringProperty()
    name = ndb.StringProperty()
    location = ndb.GeoPtProperty()
    bounds = ndb.StructuredProperty(LocationBounds)
    streets = ndb.StructuredProperty(Street, repeated=True)


class CityAppLocations(NdbModel):
    country_code = ndb.StringProperty()
    official_id = ndb.IntegerProperty()  # NIS code for belgium
    localities = ndb.LocalStructuredProperty(Locality, repeated=True)

    @property
    def app_id(self):
        return self.key.id().encode('utf-8')

    @classmethod
    def create_key(cls, app_id):
        return ndb.Key(cls, app_id)
