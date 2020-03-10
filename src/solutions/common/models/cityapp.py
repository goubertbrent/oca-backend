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

from rogerthat.dal import parent_ndb_key
from rogerthat.models.common import NdbModel, TOProperty
from rogerthat.rpc import users
from solutions.common import SOLUTION_COMMON
from solutions.common.bizz import OrganizationType
from solutions.common.to.paddle import PaddleOrganizationUnitDetails


class CityAppProfile(NdbModel):
    # Run params in cron of CityAppSolutionGatherEvents
    gather_events_enabled = ndb.BooleanProperty(indexed=False, default=False)
    review_news = ndb.BooleanProperty(indexed=False, default=False)

    EVENTS_ORGANIZATION_TYPES = [OrganizationType.NON_PROFIT, OrganizationType.PROFIT, OrganizationType.CITY,
                                 OrganizationType.EMERGENCY]

    @property
    def service_user(self):
        return users.User(self.key.id())

    @classmethod
    def create_key(cls, service_user):
        return ndb.Key(cls, 'profile', parent=parent_ndb_key(service_user, SOLUTION_COMMON))


class UitdatabankSettings(NdbModel):
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
        return ndb.Key(cls, service_user.email(), parent=parent_ndb_key(service_user))

    @classmethod
    def list_enabled(cls):
        return cls.query().filter(cls.enabled == True)


class PaddleOrganizationalUnits(NdbModel):
    units = TOProperty(PaddleOrganizationUnitDetails, repeated=True)  # type: list[PaddleOrganizationUnitDetails]

    @classmethod
    def create_key(cls, service_user):
        return ndb.Key(cls, service_user.email(), parent=parent_ndb_key(service_user))


class PaddleMapping(NdbModel):
    paddle_id = ndb.StringProperty(indexed=False)
    title = ndb.StringProperty(indexed=False)
    service_email = ndb.StringProperty(indexed=False)


class PaddleSettings(NdbModel):
    base_url = ndb.StringProperty()
    mapping = ndb.StructuredProperty(PaddleMapping, indexed=False, repeated=True)  # type: list[PaddleMapping]
    synced_fields = ndb.TextProperty(repeated=True)

    @property
    def service_user(self):
        return users.User(self.key.parent().id())

    @classmethod
    def create_key(cls, service_user):
        return ndb.Key(cls, service_user.email(), parent=parent_ndb_key(service_user))
