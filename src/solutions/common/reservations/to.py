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
from mcfw.properties import unicode_property, long_property, long_list_property, typed_property, unicode_list_property, \
    bool_property
from rogerthat.models import UserProfile
from rogerthat.to import TO
from rogerthat.utils.app import get_app_user_tuple
from solutions.common.dal.reservations import get_tables
from solutions.common.to import TimestampTO


class Shift(TO):
    name = unicode_property('1', 'Name of the shift. Eg Lunch, Dinner')
    start = long_property('2', 'Start of the shift expressed in a number of seconds since midnight.')
    end = long_property('3', 'End of the shift expressed in a number of seconds since midnight.')
    leap_time = long_property('4',
                              'The time preceding the shift in which the customer cannot automatically make a reservation anymore expressed in minutes.')
    capacity = long_property('5', 'Max number of people attending the restaurant for this shift.')
    threshold = long_property('6', 'Percentage of the capacity that allows auto-booking of reservations.')
    max_group_size = long_property('7', 'Max number of people in one reservation.')
    days = long_list_property('8', 'Days on which this shift applies. 1=Monday, 7=Sunday')

    def __eq__(self, other):
        if not isinstance(other, Shift):
            return False
        return self.start == other.start and self.end == other.end and self.days == other.days


class TableTO(TO):
    key = long_property('1')
    name = unicode_property('2')
    capacity = long_property('3')

    @classmethod
    def fromTable(cls, obj):
        t = TableTO()
        t.key = obj.id_
        t.name = obj.name
        t.capacity = obj.capacity
        return t


class RestaurantSettingsTO(TO):
    shifts = typed_property('1', Shift, True)
    tables = typed_property('2', TableTO, True)

    @classmethod
    def fromRestaurantSettingsObject(cls, obj):
        settings = RestaurantSettingsTO()
        settings.shifts = [Shift.from_model(shift) for shift in obj.shifts]
        settings.tables = map(TableTO.fromTable, get_tables(obj.service_user, obj.service_identity))
        return settings


class RestaurantReservationSenderTO(TO):
    email = unicode_property('0')
    name = unicode_property('1')
    app_id = unicode_property('2')
    avatar_url = unicode_property('3')

    @classmethod
    def from_user_profile(cls, user_profile, base_url):
        # type: (UserProfile, unicode) -> RestaurantReservationSenderTO
        to = cls()
        email, app_id = get_app_user_tuple(user_profile.user)
        to.email = email.email()
        to.app_id = app_id
        to.name = user_profile.name
        to.avatar_url = user_profile.get_avatar_url(base_url)
        return to


class RestaurantReservationTO(TO):
    key = unicode_property('0')
    name = unicode_property('1')
    phone = unicode_property('2')
    timestamp = typed_property('3', TimestampTO)
    people = long_property('4')
    comment = unicode_property('5')
    status = long_property('6')
    sender = typed_property('7', RestaurantReservationSenderTO)
    tables = long_list_property('8')

    @classmethod
    def fromReservation(cls, obj, sender):
        rr = RestaurantReservationTO()
        rr.key = unicode(obj.key.urlsafe())
        rr.name = obj.name
        rr.phone = obj.phone
        rr.timestamp = TimestampTO.fromDatetime(obj.date)
        rr.people = obj.people
        rr.comment = obj.comment
        rr.status = obj.status
        rr.sender = sender
        if obj.tables:
            rr.tables = obj.tables
        else:
            rr.tables = []
        return rr


class RestaurantBrokenReservationTO(RestaurantReservationTO):
    alternative_shifts = unicode_list_property('100')
    via_rogerthat = bool_property('101')

    @classmethod
    def fromReservation(cls, obj, alternative_shifts, sender):
        rbr = RestaurantBrokenReservationTO()
        rbr.__dict__ = RestaurantReservationTO.fromReservation(obj, sender).__dict__
        rbr.alternative_shifts = alternative_shifts
        rbr.via_rogerthat = obj.user is not None
        return rbr


class RestaurantShiftDetailsTO(TO):
    shift = typed_property('1', Shift)
    start_time = typed_property('2', TimestampTO)
    reservations = typed_property('3', RestaurantReservationTO, True)


class RestaurantReservationStatisticTO(TO):
    capacity = long_property('1', default=0)
    capacity_threshold = long_property('2', default=0)
    reservations = long_property('3', default=0)


class RestaurantReservationStatisticsTO(TO):
    today = typed_property('1', RestaurantReservationStatisticTO)
    tomorrow = typed_property('2', RestaurantReservationStatisticTO)
    next_week = typed_property('3', RestaurantReservationStatisticTO)
    start = typed_property('4', TimestampTO)
    end = typed_property('5', TimestampTO)


class DeleteTableReservationTO(TO):
    reservation = typed_property('1', RestaurantReservationTO)
    shift = typed_property('2', RestaurantShiftDetailsTO)


class DeleteTableStatusTO(TO):
    success = bool_property('1')
    reservations = typed_property('2', DeleteTableReservationTO, True)
