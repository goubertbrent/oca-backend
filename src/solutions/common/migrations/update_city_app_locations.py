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

from solutions.common.models.news import CityAppLocations, Street
from rogerthat.bizz.job import run_job


def job():
    run_job(list_city_app_locations, [], update_city_app_location, [])


def list_city_app_locations():
    return CityAppLocations.query()


def update_city_app_location(location_key):
    # Remove duplicate streets
    location = location_key.get()
    for locality in location.localities:
        street_tuples = {(street.name, street.id) for street in locality.streets}
        locality.streets = [Street(name=street_name, id=street_id)
                            for (street_name, street_id) in sorted(street_tuples, key=lambda (name, _): name.upper())]
    location.put()
