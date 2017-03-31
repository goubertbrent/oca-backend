# -*- coding: utf-8 -*-
# Copyright 2017 GIG Technology NV
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

from mcfw.properties import unicode_property, typed_property, long_list_property, long_property, unicode_list_property, \
    bool_property
from solutions.common.dal.reservations import get_tables
from solutions.common.models.reservation.properties import Shift
from solutions.common.to import TimestampTO


class RestaurantShiftTO(Shift):

    @staticmethod
    def fromShift(obj):
        rs = RestaurantShiftTO()
        rs.__dict__ = obj.__dict__
        return rs

class TableTO(object):
    key = long_property('1')
    name = unicode_property('2')
    capacity = long_property('3')

    @staticmethod
    def fromTable(obj):
        t = TableTO()
        t.key = obj.id_
        t.name = obj.name
        t.capacity = obj.capacity
        return t

class RestaurantSettingsTO(object):
    shifts = typed_property('1', RestaurantShiftTO, True)
    tables = typed_property('2', TableTO, True)

    @staticmethod
    def fromRestaurantSettingsObject(obj):
        settings = RestaurantSettingsTO()
        settings.shifts = list()
        for shift_obj in obj.shifts:
            settings.shifts.append(RestaurantShiftTO.fromShift(shift_obj))
        settings.tables = map(TableTO.fromTable, get_tables(obj.service_user, obj.service_identity))
        return settings

class RestaurantReservationSenderTO(object):
    email = unicode_property('0')
    name = unicode_property('1')
    app_id = unicode_property('2')
    avatar_url = unicode_property('3')

    @staticmethod
    def fromRestaurantReservationSenderObject(obj):
        sender = RestaurantReservationSenderTO()
        sender.email = obj.email
        sender.name = obj.name
        sender.app_id = obj.app_id
        sender.avatar_url = obj.avatar_url
        return sender

class RestaurantReservationTO(object):
    key = unicode_property('0')
    name = unicode_property('1')
    phone = unicode_property('2')
    timestamp = typed_property('3', TimestampTO)
    people = long_property('4')
    comment = unicode_property('5')
    status = long_property('6')
    sender = typed_property('7', RestaurantReservationSenderTO)
    tables = long_list_property('8')

    @staticmethod
    def fromReservation(obj):
        rr = RestaurantReservationTO()
        rr.key = unicode(obj.key())
        rr.name = obj.name
        rr.phone = obj.phone
        rr.timestamp = TimestampTO.fromDatetime(obj.date)
        rr.people = obj.people
        rr.comment = obj.comment
        rr.status = obj.status
        if obj.sender:
            rr.sender = RestaurantReservationSenderTO.fromRestaurantReservationSenderObject(obj.sender)
        else:
            rr.sender = None
        if obj.tables:
            rr.tables = obj.tables
        else:
            rr.tables = list()
        return rr

class RestaurantBrokenReservationTO(RestaurantReservationTO):
    alternative_shifts = unicode_list_property('100')
    via_rogerthat = bool_property('101')

    @staticmethod
    def fromReservation(obj, alternative_shifts):
        rbr = RestaurantBrokenReservationTO()
        rbr.__dict__ = RestaurantReservationTO.fromReservation(obj).__dict__
        rbr.alternative_shifts = alternative_shifts
        rbr.via_rogerthat = obj.user != None
        return rbr

class RestaurantShiftDetailsTO(object):
    shift = typed_property('1', RestaurantShiftTO)
    start_time = typed_property('2', TimestampTO)
    reservations = typed_property('3', RestaurantReservationTO, True)

class RestaurantReservationStatisticTO(object):
    capacity = long_property('1')
    capacity_threshold = long_property('2')
    reservations = long_property('3')

    def __init__(self):
        self.capacity = 0
        self.capacity_threshold = 0
        self.reservations = 0

class RestaurantReservationStatisticsTO(object):
    today = typed_property('1', RestaurantReservationStatisticTO)
    tomorrow = typed_property('2', RestaurantReservationStatisticTO)
    next_week = typed_property('3', RestaurantReservationStatisticTO)
    start = typed_property('4', TimestampTO)
    end = typed_property('5', TimestampTO)


class DeleteTableReservationTO(object):
    reservation = typed_property('1', RestaurantReservationTO)
    shift = typed_property('2', RestaurantShiftDetailsTO)

class DeleteTableStatusTO(object):
    success = bool_property('1')
    reservations = typed_property('2', DeleteTableReservationTO, True)
