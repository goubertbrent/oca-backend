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

from google.appengine.ext import db, ndb

from mcfw.rpc import arguments, returns
from rogerthat.dal import parent_key, parent_ndb_key
from rogerthat.models.common import NdbModel
from rogerthat.rpc import users
from solutions.common import SOLUTION_COMMON
from solutions.common.bizz import OrganizationType


class CityAppProfile(db.Model):

    # Run params in cron of CityAppSolutionGatherEvents
    gather_events_enabled = db.BooleanProperty(indexed=False, default=False)

    review_news = db.BooleanProperty(indexed=False)

    EVENTS_ORGANIZATION_TYPES = [OrganizationType.NON_PROFIT, OrganizationType.PROFIT, OrganizationType.CITY,
                                 OrganizationType.EMERGENCY]

    @property
    def service_user(self):
        return users.User(self.parent_key().name())

    @staticmethod
    @returns(db.Key)
    @arguments(service_user=users.User)
    def create_key(service_user):
        return db.Key.from_path(CityAppProfile.kind(), 'profile', parent=parent_key(service_user, SOLUTION_COMMON))


class UitdatabankSettings(NdbModel):
    VERSION_1 = u'1'
    VERSION_2 = u'2'
    VERSION_3 = u'3'

    enabled = ndb.BooleanProperty(indexed=True, default=False)
    version = ndb.StringProperty(indexed=False, default=VERSION_3)
    params = ndb.JsonProperty(indexed=False)

    cron_run_time = ndb.IntegerProperty(indexed=False)
    cron_sync_time = ndb.IntegerProperty(indexed=False)

    @property
    def service_user(self):
        return users.User(self.key.parent().id().decode('utf8'))

    @classmethod
    def create_key(cls, service_user):
        return ndb.Key(cls, service_user.email(), parent=parent_ndb_key(service_user, namespace=cls.NAMESPACE))

    @classmethod
    def list_enabled(cls):
        return cls.query().filter(cls.enabled == True)
