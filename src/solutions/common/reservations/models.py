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

from rogerthat.dal import parent_ndb_key
from rogerthat.models import NdbModel
from rogerthat.rpc import users
from rogerthat.utils.service import get_service_user_from_service_identity_user, get_identity_from_service_identity_user
from solutions import SOLUTION_COMMON
from solutions.common.utils import create_service_identity_user_wo_default


class RestaurantShift(NdbModel):
    # Name of the shift. Eg Lunch, Dinner
    name = ndb.TextProperty()
    # Start of the shift expressed in a number of seconds since midnight.
    start = ndb.IntegerProperty(indexed=False)
    # End of the shift expressed in a number of seconds since midnight.
    end = ndb.IntegerProperty(indexed=False)
    # The time preceding the shift in which the customer cannot automatically make a reservation anymore, in minutes.
    leap_time = ndb.IntegerProperty(indexed=False)
    # Max number of people attending the restaurant for this shift.
    capacity = ndb.IntegerProperty(indexed=False)
    # Percentage of the capacity that allows auto-booking of reservations.
    threshold = ndb.IntegerProperty(indexed=False)
    # Max number of people in one reservation.
    max_group_size = ndb.IntegerProperty(indexed=False)
    # Days on which this shift applies. 1=Monday, 7=Sunday
    days = ndb.IntegerProperty(repeated=True, indexed=False)


class RestaurantConfiguration(NdbModel):
    shifts = ndb.LocalStructuredProperty(RestaurantShift, repeated=True, indexed=False)

    @property
    def service_identity_user(self):
        return users.User(self.key.parent().id())

    @property
    def service_user(self):
        return get_service_user_from_service_identity_user(self.service_identity_user)

    @property
    def service_identity(self):
        return get_identity_from_service_identity_user(self.service_identity_user)

    @classmethod
    def create_key(cls, service_user, service_identity):
        parent = parent_ndb_key(create_service_identity_user_wo_default(service_user, service_identity),
                                SOLUTION_COMMON)
        return ndb.Key(cls, 'settings', parent=parent)

    def get_shift_by_name(self, shift_name):
        for shift in self.shifts:
            if shift.name == shift_name:
                return shift


class RestaurantProfile(NdbModel):
    reserve_flow_part2 = ndb.TextProperty(required=True)

    @property
    def service_user(self):
        return users.User(self.key.parent().id())

    @classmethod
    def create_key(cls, service_user):
        return ndb.Key(cls, 'profile', parent=parent_ndb_key(service_user, SOLUTION_COMMON))


class RestaurantReservation(NdbModel):
    STATUS_PLANNED = 1
    STATUS_CANCELED = 2
    STATUS_DELETED = 4
    STATUS_ARRIVED = 8
    STATUS_NOTIFIED = 16
    STATUS_SHIFT_REMOVED = 2147483648

    user = ndb.UserProperty()
    service_user = ndb.UserProperty()
    name = ndb.TextProperty(required=True, indexed=False)
    phone = ndb.TextProperty()
    date = ndb.DateTimeProperty(required=True, indexed=False)
    shift_start = ndb.DateTimeProperty(required=True)
    people = ndb.IntegerProperty(required=True, indexed=False)
    comment = ndb.TextProperty()
    status = ndb.IntegerProperty(required=True, default=STATUS_PLANNED)
    creation_date = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    tables = ndb.IntegerProperty(repeated=True)
    solution_inbox_message_key = ndb.StringProperty(indexed=False)

    @property
    def service_identity_user(self):
        return self.service_user

    @property
    def service_identity(self):
        return get_identity_from_service_identity_user(self.service_identity_user)

    @classmethod
    def list_by_service(cls, service_user, service_identity):
        service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
        return cls.query().filter(cls.service_user == service_identity_user)

    @classmethod
    def list_by_table(cls, service_user, service_identity, table_id):
        return cls.list_by_service(service_user, service_identity) \
            .filter(cls.tables == table_id)

    @classmethod
    def list_by_status(cls, service_user, service_identity, status):
        return cls.list_by_service(service_user, service_identity) \
            .filter(cls.status >= status)

    @classmethod
    def list_planned_reservations_by_user(cls, service_user, service_identity, user, shift_start):
        return cls.list_by_service(service_user, service_identity) \
            .filter(cls.user == user) \
            .filter(cls.status == cls.STATUS_PLANNED) \
            .filter(cls.shift_start >= shift_start)

    @classmethod
    def list_planned_reservations_by_table(cls, service_user, service_identity, table_id, shift_start):
        return cls.list_by_service(service_user, service_identity) \
            .filter(cls.tables == table_id) \
            .filter(cls.status == cls.STATUS_PLANNED) \
            .filter(cls.shift_start >= shift_start)

    @classmethod
    def list_from(cls, service_user, service_identity, from_):
        return cls.list_by_service(service_user, service_identity) \
            .filter(cls.shift_start >= from_)

    @classmethod
    def list_until(cls, service_user, service_identity, until):
        return cls.list_by_service(service_user, service_identity) \
            .filter(cls.shift_start < until)

    @classmethod
    def list_by_shift_start(cls, service_user, service_identity, shift_start):
        return cls.list_by_service(service_user, service_identity).filter(cls.shift_start == shift_start)


class RestaurantTable(NdbModel):
    name = ndb.TextProperty()
    capacity = ndb.IntegerProperty(indexed=False)
    deleted = ndb.BooleanProperty()

    @property
    def service_identity_user(self):
        return users.User(self.key.parent().id())

    @property
    def service_user(self):
        return get_service_user_from_service_identity_user(self.service_identity_user)

    @property
    def service_identity(self):
        return get_identity_from_service_identity_user(self.service_identity_user)

    @property
    def id_(self):
        return self.key.id()

    @classmethod
    def create_key(cls, table_id, service_user, service_identity):
        return ndb.Key(cls, table_id, parent=cls.create_parent_key(service_user, service_identity))

    @classmethod
    def create_parent_key(cls, service_user, service_identity):
        return parent_ndb_key(create_service_identity_user_wo_default(service_user, service_identity), SOLUTION_COMMON)

    @classmethod
    def list_by_service(cls, service_user, service_identity):
        return cls.query(ancestor=cls.create_parent_key(service_user, service_identity)) \
            .filter(cls.deleted == False)
