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

from rogerthat.dal import parent_key, parent_key_unsafe
from rogerthat.rpc import users
from rogerthat.utils.service import get_identity_from_service_identity_user, \
    get_service_user_from_service_identity_user
from google.appengine.ext import db
from mcfw.rpc import returns, arguments
from solutions.common import SOLUTION_COMMON
from solutions.common.models.properties import SolutionUserProperty
from solutions.common.models.reservation.properties import ShiftsProperty


class RestaurantSettings(db.Model):
    shifts = ShiftsProperty()

    @property
    def service_identity_user(self):
        return users.User(self.parent_key().name())

    @property
    def service_user(self):
        return get_service_user_from_service_identity_user(self.service_identity_user)

    @property
    def service_identity(self):
        return get_identity_from_service_identity_user(self.service_identity_user)

    @staticmethod
    def create_key(service_identity_user):
        return db.Key.from_path(RestaurantSettings.kind(), 'settings', parent=parent_key_unsafe(service_identity_user, SOLUTION_COMMON))


class RestaurantProfile(db.Model):
    reserve_flow_part2 = db.StringProperty(required=True, indexed=False)

    @property
    def service_user(self):
        return users.User(self.parent_key().name())

    @staticmethod
    @returns(db.Key)
    @arguments(service_user=users.User)
    def create_key(service_user):
        return db.Key.from_path(RestaurantProfile.kind(), 'profile', parent=parent_key(service_user, SOLUTION_COMMON))


class RestaurantReservation(db.Model):
    STATUS_PLANNED = 1
    STATUS_CANCELED = 2
    STATUS_DELETED = 4
    STATUS_ARRIVED = 8
    STATUS_NOTIFIED = 16
    STATUS_SHIFT_REMOVED = 2147483648

    user = db.UserProperty(indexed=True)
    service_user = db.UserProperty(indexed=True)
    name = db.StringProperty(required=True, indexed=False)
    phone = db.StringProperty(indexed=False)
    date = db.DateTimeProperty(required=True, indexed=False)
    shift_start = db.DateTimeProperty(required=True)
    people = db.IntegerProperty(required=True, indexed=False)
    comment = db.StringProperty(multiline=True, indexed=False)
    status = db.IntegerProperty(required=True, default=STATUS_PLANNED)
    creation_date = db.DateTimeProperty(indexed=False)
    sender = SolutionUserProperty(default=None)
    tables = db.ListProperty(int, indexed=True)

    solution_inbox_message_key = db.StringProperty(indexed=False)

    @property
    def service_identity_user(self):
        return self.service_user

    @property
    def service_identity(self):
        return get_identity_from_service_identity_user(self.service_identity_user)


class RestaurantTable(db.Model):
    name = db.StringProperty(indexed=False)
    capacity = db.IntegerProperty(indexed=False)
    deleted = db.BooleanProperty(indexed=True)

    @property
    def service_identity_user(self):
        return users.User(self.parent_key().name())

    @property
    def service_user(self):
        return get_service_user_from_service_identity_user(self.service_identity_user)

    @property
    def service_identity(self):
        return get_identity_from_service_identity_user(self.service_identity_user)

    @property
    def id_(self):
        return self.key().id()
