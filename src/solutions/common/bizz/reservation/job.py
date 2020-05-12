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

from rogerthat.bizz.job import run_job
from rogerthat.rpc import users
from rogerthat.utils import is_flag_set, set_flag, unset_flag
from rogerthat.utils.channel import send_message
from google.appengine.ext import db
from mcfw.rpc import arguments, returns
from solutions.common.dal.reservations import get_reservations_keys_qry
from solutions.common.models.reservation import RestaurantReservation
from solutions.common.models.reservation.properties import Shift


@returns(NoneType)
@arguments(service_user=users.User, service_identity=unicode, start=datetime, shifts=[Shift])
def handle_shift_updates(service_user, service_identity, start, shifts):
    run_job(get_reservations_keys_qry, [service_user, service_identity, start], _check_reservation, [shifts, service_user, service_identity])

def _check_reservation(reservation_key, shifts, service_user, service_identity):
    def trans():
        reservation = db.get(reservation_key)
        if is_flag_set(RestaurantReservation.STATUS_CANCELED, reservation.status) or is_flag_set(RestaurantReservation.STATUS_DELETED, reservation.status):
            return False
        current_start = reservation.shift_start.hour * 3600 + reservation.shift_start.minute * 60
        for shift in shifts:
            if not reservation.date.isoweekday() in shift.days:
                continue
            if current_start == shift.start:
                if is_flag_set(RestaurantReservation.STATUS_SHIFT_REMOVED, reservation.status):
                    reservation.status = unset_flag(RestaurantReservation.STATUS_SHIFT_REMOVED, reservation.status)
                    reservation.put()
                    return True
                return False
            if shift.start <= current_start <= shift.end:
                reservation.status = unset_flag(RestaurantReservation.STATUS_SHIFT_REMOVED, reservation.status)
                reservation.shift_start = datetime(reservation.shift_start.year, reservation.shift_start.month, reservation.shift_start.day, shift.start / 3600, (shift.start % 3600) / 60)
                reservation.put()
                return True
        if not is_flag_set(RestaurantReservation.STATUS_SHIFT_REMOVED, reservation.status):
            reservation.status = set_flag(RestaurantReservation.STATUS_SHIFT_REMOVED, reservation.status)
            reservation.put()
            return True
        return False
    if db.run_in_transaction(trans):
        send_message(service_user, u"solutions.restaurant.reservations.shift_changes_conflicts", service_identity=service_identity)
