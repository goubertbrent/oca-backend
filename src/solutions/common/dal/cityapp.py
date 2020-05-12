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

import logging

from google.appengine.ext import ndb

from mcfw.cache import invalidate_cache, cached
from mcfw.rpc import arguments, returns
from rogerthat.rpc import users
from shop.models import Customer
from solutions.common.bizz import SolutionModule, OrganizationType
from solutions.common.dal import get_solution_settings
from solutions.common.models.cityapp import CityAppProfile, UitdatabankSettings


@ndb.transactional()
@returns(CityAppProfile)
@arguments(service_user=users.User)
def get_cityapp_profile(service_user):
    key = CityAppProfile.create_key(service_user)
    cityapp_profile = key.get()
    if not cityapp_profile:
        cityapp_profile = CityAppProfile(key=key)
        cityapp_profile.put()
    return cityapp_profile


@returns(UitdatabankSettings)
@arguments(service_user=users.User)
def get_uitdatabank_settings(service_user):
    # type: (users.User) -> UitdatabankSettings
    key = UitdatabankSettings.create_key(service_user)
    settings = key.get()
    if settings:
        return settings
    return UitdatabankSettings(key=key)


@returns()
@arguments(app_id=unicode)
def invalidate_service_user_for_city(app_id):
    invalidate_cache(get_service_users_for_city, app_id=app_id)


@cached(1, lifetime=0, request=True, memcache=False, datastore=u"get_service_users_for_city")
@returns([users.User])
@arguments(app_id=unicode)
def get_service_users_for_city(app_id):
    result = []
    for customer in Customer.all().filter('organization_type =', OrganizationType.CITY):
        if customer.app_ids and app_id == customer.app_id:
            if customer.service_email:
                sln_settings = get_solution_settings(customer.service_user)
                if SolutionModule.CITY_APP in sln_settings.modules:
                    result.append(customer.service_user)
        elif not customer.app_ids:
            logging.debug("get_service_user_for_city failed for customer_id: %s", customer.id)

    return result


@returns(users.User)
@arguments(app_id=unicode)
def get_service_user_for_city(app_id):
    service_users = get_service_users_for_city(app_id)
    if not service_users:
        return None

    if len(service_users) > 1:
        logging.warn('Found multiple community services with module CITY_APP. Just taking the first user from %s.',
                     [u.email() for u in service_users])
    return service_users[0]
