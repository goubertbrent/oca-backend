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
from StringIO import StringIO

from google.appengine.api import users
from google.appengine.ext import ndb, db

from mcfw.serialization import s_long, s_unicode, ds_unicode, get_list_serializer, get_list_deserializer, s_long_list, \
    ds_long_list, ds_long
from rogerthat.dal import parent_key_unsafe
from rogerthat.models.properties.messaging import SpecializedList
from rogerthat.utils.service import get_service_user_from_service_identity_user, get_identity_from_service_identity_user
from solutions import SOLUTION_COMMON
from solutions.common.reservations.models import RestaurantShift, RestaurantConfiguration
from solutions.common.reservations.to import Shift


class Shifts(SpecializedList):

    def add(self, shift):
        self._table[shift.name] = shift


def _serialize_shift(stream, s):
    s_unicode(stream, s.name)
    s_long(stream, s.start)
    s_long(stream, s.end)
    s_long(stream, s.leap_time)
    s_long(stream, s.capacity)
    s_long(stream, s.threshold)
    s_long(stream, s.max_group_size)
    s_long_list(stream, s.days)


def _deserialize_shift(stream, version):
    s = Shift()
    s.name = ds_unicode(stream)
    s.start = ds_long(stream)
    s.end = ds_long(stream)
    s.leap_time = ds_long(stream)
    s.capacity = ds_long(stream)
    s.threshold = ds_long(stream)
    s.max_group_size = ds_long(stream)
    s.days = ds_long_list(stream)
    return s


_serialize_shift_list = get_list_serializer(_serialize_shift)
_deserialize_shift_list = get_list_deserializer(_deserialize_shift, True)


def _serialize_shifts(stream, shifts):
    s_long(stream, 1)  # version in case we need to adjust the shifts structure
    _serialize_shift_list(stream, shifts.values())


def _deserialize_shifts(stream):
    version = ds_long(stream)
    shifts = Shifts()
    for s in _deserialize_shift_list(stream, version):
        shifts.add(s)
    return shifts


class ShiftsProperty(db.UnindexedProperty):
    # Tell what the user type is.
    data_type = Shifts

    # For writing to datastore.
    def get_value_for_datastore(self, model_instance):
        stream = StringIO()
        _serialize_shifts(stream, super(ShiftsProperty, self).get_value_for_datastore(model_instance))
        return db.Blob(stream.getvalue())

    # For reading from datastore.
    def make_value_from_datastore(self, value):
        if value is None:
            return None
        return _deserialize_shifts(StringIO(value))

    def validate(self, value):
        if value is not None and not isinstance(value, Shifts):
            raise ValueError('Property %s must be convertible to a Shifts instance (%s)' % (self.name, value))
        return super(ShiftsProperty, self).validate(value)

    def empty(self, value):
        return not value


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
        return db.Key.from_path(RestaurantSettings.kind(), 'settings',
                                parent=parent_key_unsafe(service_identity_user, SOLUTION_COMMON))


def migrate():
    to_put = []
    for setting in RestaurantSettings.all():  # type: RestaurantSettings
        to_put.append(RestaurantConfiguration(
            key=RestaurantConfiguration.create_key(setting.service_user, setting.service_identity),
            shifts=[RestaurantShift(**shift.to_dict()) for shift in setting.shifts]
        ))
    ndb.put_multi(to_put)


def cleanup():
    # Execute this after migration & after new code is live for everyone
    # there are only 350-ish models of this kind
    db.delete(RestaurantSettings.all(keys_only=True).fetch(None))
