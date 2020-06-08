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
from typing import List

from mcfw.utils import Enum
from rogerthat.dal import parent_ndb_key
from rogerthat.models import NdbModel
from rogerthat.rpc import users
from solutions.common import SOLUTION_COMMON


class VoucherProviderId(Enum):
    CIRKLO = 'cirklo'


class VoucherSettings(NdbModel):
    app_id = ndb.StringProperty()
    providers = ndb.StringProperty(choices=VoucherProviderId.all(), repeated=True)  # type: List[str]
    customer_id = ndb.IntegerProperty()

    @property
    def service_user(self):
        return users.User(self.key.parent().id())

    @classmethod
    def create_key(cls, service_user):
        # type: (users.User) -> ndb.Key
        return ndb.Key(cls, service_user.email(), parent=parent_ndb_key(service_user, SOLUTION_COMMON))

    @classmethod
    def list_by_provider_and_app(cls, provider, app_id):
        return cls.query() \
            .filter(cls.app_id == app_id) \
            .filter(cls.providers == provider)


class CirkloUserVouchers(NdbModel):
    voucher_ids = ndb.TextProperty(repeated=True)  # type: List[str]

    @classmethod
    def create_key(cls, app_user):
        return ndb.Key(cls, app_user.email(), parent=parent_ndb_key(app_user))


class CirkloCity(NdbModel):
    service_user_email = ndb.StringProperty()

    @property
    def city_id(self):
        return self.key.id().decode('utf-8')

    @classmethod
    def create_key(cls, city_id):
        return ndb.Key(cls, city_id)

    @classmethod
    def get_by_service_email(cls, service_email):
        return cls.query(cls.service_user_email == service_email).get()
