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
# @@license_version:1.3@@

from datetime import datetime
from types import NoneType

from rogerthat.dal import generator, put_and_invalidate_cache, parent_key_unsafe
from rogerthat.rpc import users
from google.appengine.ext import db
from mcfw.cache import cached
from mcfw.rpc import returns, arguments
from solutions.common import SOLUTION_COMMON
from solutions.common.models.reservation import RestaurantSettings, RestaurantProfile, RestaurantReservation, RestaurantTable
from solutions.common.utils import create_service_identity_user_wo_default


@cached(1, memcache=False)
@returns(RestaurantSettings)
@arguments(service_user=users.User, service_identity=unicode)
def get_restaurant_settings(service_user, service_identity=None):
    service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
    return db.get(RestaurantSettings.create_key(service_identity_user))

@returns(RestaurantProfile)
@arguments(service_user=users.User)
def get_restaurant_profile(service_user):
    return db.get(RestaurantProfile.create_key(service_user))

@returns([RestaurantReservation])
@arguments(service_user=users.User, service_identity=unicode, shift_start=datetime)
def get_restaurant_reservation(service_user, service_identity, shift_start):
    service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
    return generator(RestaurantReservation.all().filter("service_user =", service_identity_user)
                     .filter('shift_start =', shift_start))

@returns([RestaurantReservation])
@arguments(service_user=users.User, service_identity=unicode, from_=datetime, until=datetime)
def get_reservations(service_user, service_identity, from_=None, until=None):
    service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
    filter_ = RestaurantReservation.all().filter("service_user =", service_identity_user)
    if from_:
        filter_ = filter_.filter('shift_start >=', from_)
    if until:
        filter_ = filter_.filter('shift_start <', until)
    return generator(filter_)

@returns(db.Query)
@arguments(service_user=users.User, service_identity=unicode, from_=datetime, until=datetime)
def get_reservations_keys_qry(service_user, service_identity, from_=None, until=None):
    service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
    filter_ = RestaurantReservation.all(keys_only=True).filter("service_user =", service_identity_user)
    if from_:
        filter_ = filter_.filter('shift_start >=', from_)
    if until:
        filter_ = filter_.filter('shift_start <', until)
    return filter_

@returns([RestaurantReservation])
@arguments(service_user=users.User, service_identity=unicode)
def get_broken_reservations(service_user, service_identity):
    service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
    filter_ = RestaurantReservation.all().filter("service_user =", service_identity_user)
    return generator(filter_.filter('status >=', RestaurantReservation.STATUS_SHIFT_REMOVED))

@returns([RestaurantReservation])
@arguments(service_user=users.User, service_identity=unicode, user=users.User, from_=datetime)
def get_planned_reservations_by_user(service_user, service_identity, user, from_):
    service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
    return generator(RestaurantReservation.all()
                     .filter("service_user =", service_identity_user)
                     .filter('user', user)
                     .filter('status', RestaurantReservation.STATUS_PLANNED)
                     .filter('shift_start >=', from_))

@returns([RestaurantReservation])
@arguments(service_user=users.User, service_identity=unicode, table_id=(int, long), from_=datetime)
def get_upcoming_planned_reservations_by_table(service_user, service_identity, table_id, from_):
    service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
    qry = RestaurantReservation.all().filter("service_user =", service_identity_user)
    qry.filter('tables =', table_id)
    qry.filter('status', RestaurantReservation.STATUS_PLANNED)
    qry.filter('shift_start >=', from_)
    return generator(qry)

@returns(NoneType)
@arguments(service_user=users.User, service_identity=unicode, table_id=(int, long))
def clear_table_id_in_reservations(service_user, service_identity, table_id):
    service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
    qry = RestaurantReservation.all().filter("service_user =", service_identity_user)
    qry.filter('tables =', table_id)
    reservations = qry.fetch(None)
    for r in reservations:
        r.tables.remove(table_id)
    put_and_invalidate_cache(*reservations)

@returns([RestaurantTable])
@arguments(service_user=users.User, service_identity=unicode)
def get_tables(service_user, service_identity):
    service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
    return generator(RestaurantTable.all().ancestor(parent_key_unsafe(service_identity_user, SOLUTION_COMMON)).filter("deleted =", False))
