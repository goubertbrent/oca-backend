# -*- coding: utf-8 -*-
# Copyright 2016 Mobicage NV
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
# @@license_version:1.1@@
from google.appengine.ext import db

from rogerthat.dal import parent_key_unsafe
from rogerthat.models import KeyValueProperty
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
