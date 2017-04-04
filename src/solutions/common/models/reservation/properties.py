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

from google.appengine.ext import db
from mcfw.properties import unicode_property, long_property, \
    long_list_property
from mcfw.serialization import s_long, s_unicode, ds_long, ds_unicode, \
    get_list_serializer, get_list_deserializer, s_long_list, ds_long_list
from rogerthat.models.properties.messaging import SpecializedList
from rogerthat.rpc.service import BusinessException
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

class DuplicateShiftException(BusinessException):
    pass

class Shift(object):
    name = unicode_property('1', 'Name of the shift. Eg Lunch, Dinner')
    start = long_property('2', 'Start of the shift expressed in a number of seconds since midnight.')
    end = long_property('3', 'End of the shift expressed in a number of seconds since midnight.')
    leap_time = long_property('4', 'The time preceding the shift in which the customer cannot automatically make a reservation anymore expressed in minutes.')
    capacity = long_property('5', 'Max number of people attending the restaurant for this shift.')
    threshold = long_property('6', 'Percentage of the capacity that allows auto-booking of reservations.')
    max_group_size = long_property('7', 'Max number of people in one reservation.')
    days = long_list_property('8', 'Days on which this shift applies. 1=Monday, 7=Sunday')

    def __eq__(self, other):
        if not isinstance(other, Shift):
            return False
        return self.start == other.start and self.end == other.end and self.days == other.days

class Shifts(SpecializedList):

    def add(self, shift):
        if shift.name in self._table:
            raise DuplicateShiftException("Two shifts cannot have the same name!")
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
        stream = StringIO.StringIO()
        _serialize_shifts(stream, super(ShiftsProperty, self).get_value_for_datastore(model_instance))
        return db.Blob(stream.getvalue())

    # For reading from datastore.
    def make_value_from_datastore(self, value):
        if value is None:
            return None
        return _deserialize_shifts(StringIO.StringIO(value))

    def validate(self, value):
        if value is not None and not isinstance(value, Shifts):
            raise ValueError('Property %s must be convertible to a Shifts instance (%s)' % (self.name, value))
        return super(ShiftsProperty, self).validate(value)

    def empty(self, value):
        return not value
