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

from datetime import datetime
from types import NoneType

from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from rogerthat.to import ReturnStatusTO, RETURNSTATUS_TO_SUCCESS
from rogerthat.utils import get_epoch_from_datetime
from mcfw.consts import MISSING
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from solutions.common.dal.reservations import get_restaurant_settings, get_restaurant_reservation
from solutions.common.to.reservation import RestaurantShiftTO, RestaurantSettingsTO, RestaurantShiftDetailsTO, \
    TimestampTO, RestaurantReservationTO, RestaurantReservationStatisticsTO, RestaurantBrokenReservationTO, TableTO, \
    DeleteTableStatusTO, DeleteTableReservationTO


@rest("/common/restaurant/settings/load", "get", read_only_access=True)
@returns(RestaurantSettingsTO)
@arguments()
def load_shifts():
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    settings = get_restaurant_settings(service_user, service_identity)
    return RestaurantSettingsTO.fromRestaurantSettingsObject(settings)


@rest("/common/restaurant/settings/shifts/save", "post")
@returns(ReturnStatusTO)
@arguments(shifts=[RestaurantShiftTO])
def save_shifts(shifts):
    from solutions.common.bizz.reservation import save_shifts as save_shifts_bizz
    try:
        service_user = users.get_current_user()
        session_ = users.get_current_session()
        service_identity = session_.service_identity
        save_shifts_bizz(service_user, service_identity, shifts)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException, e:
        return ReturnStatusTO.create(False, e.message)


@rest("/common/restaurant/reservations", "get", read_only_access=True)
@returns([RestaurantShiftDetailsTO])
@arguments(year=int, month=int, day=int, hour=int, minute=int)
def get_reservations(year, month, day, hour, minute):
    from solutions.common.bizz.reservation import get_shift_by_datetime, get_next_shift

    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    result = list()
    shift, start_time = get_shift_by_datetime(service_user, service_identity, datetime(year, month, day, hour, minute))
    if shift:
        details = RestaurantShiftDetailsTO()
        details.shift = RestaurantShiftTO.fromShift(shift)
        details.start_time = TimestampTO.fromDatetime(start_time)
        details.reservations = list()
        for reservation in get_restaurant_reservation(service_user, service_identity, start_time):
            details.reservations.append(RestaurantReservationTO.fromReservation(reservation))
        result.append(details)
        shift, start_time = get_next_shift(service_user, service_identity, shift, start_time)
        if shift:
            details = RestaurantShiftDetailsTO()
            details.shift = RestaurantShiftTO.fromShift(shift)
            details.start_time = TimestampTO.fromDatetime(start_time)
            details.reservations = list()
            for reservation in get_restaurant_reservation(service_user, service_identity, start_time):
                details.reservations.append(RestaurantReservationTO.fromReservation(reservation))
            result.append(details)
    return result

@rest("/common/restaurant/reservations/broken", "get", read_only_access=True)
@returns([RestaurantBrokenReservationTO])
@arguments()
def get_broken_reservations():
    from solutions.common.dal.reservations import get_broken_reservations as dal_get_broken_reservations
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    settings = get_restaurant_settings(service_user, service_identity)
    result = []
    for reservation in dal_get_broken_reservations(service_user, service_identity):
        alternative_shifts = [shift.name for shift in settings.shifts if reservation.date.isoweekday() in shift.days]
        result.append(RestaurantBrokenReservationTO.fromReservation(reservation, alternative_shifts))
    return result

@rest("/common/restaurant/reservations/move_shift", "post")
@returns(NoneType)
@arguments(reservation_key=unicode, shift_name=unicode)
def move_reservation_to_shift(reservation_key, shift_name):
    from solutions.common.bizz.reservation import move_reservation
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    move_reservation(service_user, service_identity, reservation_key, shift_name)

@rest("/common/restaurant/reservations/notified", "post")
@returns(NoneType)
@arguments(reservation_key=unicode)
def reservation_cancelled_notified(reservation_key):
    from solutions.common.bizz.reservation import cancel_reservation
    service_user = users.get_current_user()
    cancel_reservation(service_user, reservation_key, True)

@rest("/common/restaurant/reservations/send_cancel_via_app", "post")
@returns(NoneType)
@arguments(reservation_keys=[unicode])
def reservation_send_cancel_via_app(reservation_keys):
    from solutions.common.bizz.reservation import cancel_reservations
    service_user = users.get_current_user()
    cancel_reservations(service_user, reservation_keys)

@rest("/common/restaurant/reservations", "post")
@returns(unicode)
@arguments(year=int, month=int, day=int, hour=int, minute=int, name=unicode, people=int, comment=unicode, phone=unicode, force=bool)
def submit_reservation(year, month, day, hour, minute, name, people, comment, phone, force):
    from solutions.common.bizz.reservation import reserve_table
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    return reserve_table(service_user, service_identity, None, get_epoch_from_datetime(datetime(year, month, day, hour, minute)), people, name, phone, comment, force)

@rest("/common/restaurant/reservation-stats", "get", read_only_access=True)
@returns(RestaurantReservationStatisticsTO)
@arguments(year=int, month=int, day=int)
def get_statistics(year, month, day):
    from solutions.common.bizz.reservation import get_statistics as get_statistics_bizz
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    date = datetime(year, month, day)
    return get_statistics_bizz(service_user, service_identity, date)

@rest("/common/restaurant/reservation/arrived", "post")
@returns(RestaurantReservationTO)
@arguments(reservation_key=unicode)
def toggle_reservation_arrived(reservation_key):
    from solutions.common.bizz.reservation import toggle_reservation_arrived as toggle_reservation_arrived_bizz
    reservation = toggle_reservation_arrived_bizz(users.get_current_user(), reservation_key)
    return RestaurantReservationTO.fromReservation(reservation)

@rest("/common/restaurant/reservation/cancelled", "post")
@returns(RestaurantReservationTO)
@arguments(reservation_key=unicode)
def toggle_reservation_cancelled(reservation_key):
    from solutions.common.bizz.reservation import toggle_reservation_cancelled as toggle_reservation_cancelled_bizz
    reservation = toggle_reservation_cancelled_bizz(users.get_current_user(), reservation_key)
    return RestaurantReservationTO.fromReservation(reservation)

@rest("/common/restaurant/reservation/edit", "post")
@returns(unicode)
@arguments(reservation_key=unicode, people=int, comment=unicode, force=bool, new_date=TimestampTO)
def edit_reservation(reservation_key, people, comment, force=True, new_date=None):
    from solutions.common.bizz.reservation import edit_reservation as edit_reservation_bizz
    new_epoch = 0
    if new_date:
        new_epoch = get_epoch_from_datetime(datetime(new_date.year, new_date.month, new_date.day, new_date.hour, new_date.minute))
    return edit_reservation_bizz(users.get_current_user(), reservation_key, people, comment, force, True if new_date else False, new_epoch)

@rest("/common/restaurant/reservation/edit_tables", "post")
@returns(ReturnStatusTO)
@arguments(reservation_key=unicode, tables=[(int, long)])
def edit_reservation_tables(reservation_key, tables):
    from solutions.common.bizz.reservation import edit_reservation_tables as edit_reservation_tables_bizz
    try:
        edit_reservation_tables_bizz(users.get_current_user(), reservation_key, tables)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException, e:
        return ReturnStatusTO.create(False, e.message)

@rest("/common/restaurant/reservation/reply", "post")
@returns(ReturnStatusTO)
@arguments(email=unicode, app_id=unicode, message=unicode, reservation_key=unicode)
def reply_reservation(email, app_id, message, reservation_key=None):
    from solutions.common.bizz.reservation import reply_reservation as reply_reservation_bizz
    try:
        if reservation_key is MISSING:
            reservation_key = None
        reply_reservation_bizz(users.get_current_user(), email, app_id, message, reservation_key)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException, e:
        return ReturnStatusTO.create(False, e.message)


@rest("/common/restaurant/settings/tables/add", "post")
@returns(ReturnStatusTO)
@arguments(table=TableTO)
def add_table(table):
    from solutions.common.bizz.reservation import add_table as add_table_bizz
    try:
        service_user = users.get_current_user()
        session_ = users.get_current_session()
        service_identity = session_.service_identity
        add_table_bizz(service_user, service_identity, table)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException, e:
        return ReturnStatusTO.create(False, e.message)

@rest("/common/restaurant/settings/tables/update", "post")
@returns(ReturnStatusTO)
@arguments(table=TableTO)
def update_table(table):
    from solutions.common.bizz.reservation import update_table as update_table_bizz
    try:
        service_user = users.get_current_user()
        session_ = users.get_current_session()
        service_identity = session_.service_identity
        update_table_bizz(service_user, service_identity, table)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException, e:
        return ReturnStatusTO.create(False, e.message)

@rest("/common/restaurant/settings/tables/delete", "post")
@returns(DeleteTableStatusTO)
@arguments(table_id=(int, long), force=bool)
def delete_table(table_id, force):
    from solutions.common.bizz.reservation import get_shift_by_datetime, delete_table as delete_table_bizz
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    dtsTO = DeleteTableStatusTO()
    status, reservations = delete_table_bizz(service_user, service_identity, table_id, force)
    dtsTO.success = status
    dtsTO.reservations = list()
    if not status:
        for r in reservations:
            dtrTO = DeleteTableReservationTO()
            dtrTO.reservation = RestaurantReservationTO.fromReservation(r)

            shift, start_time = get_shift_by_datetime(service_user, service_identity, r.date)
            if shift:
                details = RestaurantShiftDetailsTO()
                details.shift = RestaurantShiftTO.fromShift(shift)
                details.start_time = TimestampTO.fromDatetime(start_time)
                details.reservations = list()
                for reservation in get_restaurant_reservation(service_user, service_identity, start_time):
                    details.reservations.append(RestaurantReservationTO.fromReservation(reservation))

                dtrTO.shift = details
            else:
                dtrTO.shift = None

            dtsTO.reservations.append(dtrTO)
    return dtsTO
