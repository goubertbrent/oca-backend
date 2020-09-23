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

from google.appengine.api import users
from google.appengine.ext import db, ndb

from statistics.models import NdbModel


STATISTICS_NAMESPACE = u'service-statistics'

class ServiceLog(db.Model):
    TYPE_CALLBACK = 1
    TYPE_CALL = 2

    STATUS_SUCCESS = 1
    STATUS_ERROR = 2
    STATUS_WAITING_FOR_RESPONSE = 3

    user = db.UserProperty()
    timestamp = db.IntegerProperty()
    type = db.IntegerProperty(indexed=False)  # @ReservedAssignment
    status = db.IntegerProperty(indexed=False)
    function = db.StringProperty(indexed=False)
    request = db.TextProperty()
    response = db.TextProperty()
    error_code = db.IntegerProperty(indexed=False)
    error_message = db.TextProperty()

    @property
    def rpc_id(self):
        return self.parent_key().name()


class NdbServiceLog(NdbModel):
    _use_memcache = False
    _use_cache = False

    TYPE_CALLBACK = 1
    TYPE_CALL = 2

    STATUS_SUCCESS = 1
    STATUS_ERROR = 2
    STATUS_WAITING_FOR_RESPONSE = 3

    user = ndb.UserProperty()
    timestamp = ndb.IntegerProperty()
    type = ndb.IntegerProperty(indexed=False)  # @ReservedAssignment
    status = ndb.IntegerProperty(indexed=False)
    function = ndb.StringProperty(indexed=False)
    request = ndb.TextProperty()
    response = ndb.TextProperty()
    error_code = ndb.IntegerProperty(indexed=False)
    error_message = ndb.TextProperty()

    @classmethod
    def _get_kind(cls):
        return ServiceLog.kind()

    @property
    def rpc_id(self):
        return self.key.parent().name()


class StatsExport(NdbModel):
    NAMESPACE = STATISTICS_NAMESPACE
    start_date = ndb.DateProperty(indexed=False)
    # TODO communities (refactor to community_id when needed, for now only used for testing)
    default_app_id = ndb.StringProperty(indexed=False)

    @property
    def service_user(self):
        return users.User(self.key.id())

    @classmethod
    def create_key(cls, service_user):
        return ndb.Key(cls, service_user.email(), namespace=cls.NAMESPACE)


class StatsExportDailyData(NdbModel):
    tag = ndb.StringProperty(indexed=False)
    count = ndb.IntegerProperty(indexed=False)


class StatsExportDailyAppStats(NdbModel):
    app_id = ndb.StringProperty(indexed=False)
    data = ndb.LocalStructuredProperty(StatsExportDailyData, repeated=True)

    def get_tag_data(self, tag):
        for d in self.data:
            if d.tag == tag:
                return d
        return None


class StatsExportDaily(NdbModel):
    NAMESPACE = STATISTICS_NAMESPACE

    date = ndb.DateProperty(indexed=True)
    app_stats = ndb.LocalStructuredProperty(StatsExportDailyAppStats, repeated=True)

    def get_app_stats(self, app_id):
        for stats in self.app_stats:
            if stats.app_id == app_id:
                return stats
        return None

    @property
    def date_str(self):
        return self.key.id()

    @property
    def service_user_email(self):
        return self.key.parent().parent().id()

    @property
    def service_identity(self):
        return self.key.parent().id()

    @classmethod
    def create_service_parent_key(cls, service_user):
        return ndb.Key(cls, service_user.email(), namespace=cls.NAMESPACE)

    @classmethod
    def create_parent_key(cls, service_user, service_identity):
        return ndb.Key(cls, service_identity, parent=cls.create_service_parent_key(service_user))

    @classmethod
    def create_key(cls, year, month, day, service_user, service_identity):
        return ndb.Key(cls, '%s-%s-%s' % (year, month, day), parent=cls.create_parent_key(service_user, service_identity))
