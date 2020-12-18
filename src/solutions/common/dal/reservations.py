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

from google.appengine.ext import ndb
from typing import List, Optional, Iterable

from rogerthat.rpc import users
from solutions.common.reservations.models import RestaurantConfiguration, RestaurantProfile, RestaurantTable, \
    RestaurantReservation


def get_restaurant_settings(service_user, service_identity=None):
    # type: (users.User, Optional[unicode]) -> RestaurantConfiguration
    return RestaurantConfiguration.create_key(service_user, service_identity).get()


def get_restaurant_profile(service_user):
    # type: (users.User) -> RestaurantProfile
    return RestaurantProfile.create_key(service_user).get()


def get_restaurant_reservation(service_user, service_identity, shift_start):
    # type: (users.User, Optional[unicode], datetime) -> List[RestaurantReservation]
    return RestaurantReservation.list_by_shift_start(service_user, service_identity, shift_start)


def get_reservations(service_user, service_identity, from_=None, until=None):
    # type: (users.User, Optional[unicode], Optional[datetime], Optional[datetime]) -> Iterable[RestaurantReservation]
    if from_:
        return RestaurantReservation.list_from(service_user, service_identity, from_)
    if until:
        return RestaurantReservation.list_until(service_user, service_identity, until)
    return RestaurantReservation.list_by_service(service_user, service_identity)


def get_broken_reservations(service_user, service_identity):
    # type: (users.User, Optional[unicode]) -> Iterable[RestaurantReservation]
    return RestaurantReservation.list_by_status(service_user, service_identity,
                                                RestaurantReservation.STATUS_SHIFT_REMOVED)


def get_planned_reservations_by_user(service_user, service_identity, user, from_):
    # type: (users.User, Optional[unicode], users.User, datetime) -> Iterable[RestaurantReservation]
    return RestaurantReservation.list_planned_reservations_by_user(service_user, service_identity, user, from_)


def get_upcoming_planned_reservations_by_table(service_user, service_identity, table_id, from_):
    # type: (users.User, unicode, long, datetime) -> Iterable[RestaurantReservation]
    return RestaurantReservation.list_planned_reservations_by_table(service_user, service_identity, table_id, from_)


def clear_table_id_in_reservations(service_user, service_identity, table_id):
    # type: (users.User, unicode, long) -> None
    reservations = RestaurantReservation.list_by_table(service_user, service_identity, table_id).fetch(None)
    for r in reservations:
        r.tables.remove(table_id)
    ndb.put_multi(reservations)


def get_tables(service_user, service_identity):
    # type: (users.User, unicode) -> List[RestaurantTable]
    return RestaurantTable.list_by_service(service_user, service_identity)
