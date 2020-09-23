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

from google.appengine.ext import db

from rogerthat.bizz.job import run_job
from rogerthat.consts import MIGRATION_QUEUE
from rogerthat.models import OpeningHours, OpeningPeriod, OpeningHour, ServiceIdentity
from solutions.common.bizz.google_places import get_place_details
from solutions.common.bizz.settings import get_service_info
from solutions.common.models import SolutionSettings


def _all_solution_settings():
    return SolutionSettings.all(keys_only=True)


def sync_opening_hours():
    # TODO run in cron
    run_job(_all_solution_settings, [], _sync_opening_hours, [], worker_queue=MIGRATION_QUEUE)


def _sync_opening_hours(sln_settings_key):
    sln_settings = db.get(sln_settings_key)
    if not sln_settings:
        return

    identities = [ServiceIdentity.DEFAULT]
    if sln_settings.identities:
        identities.extend(sln_settings.identities)

    for service_identity in identities:
        service_info = get_service_info(sln_settings.service_user, service_identity)
        if service_info.addresses:
            place_id = service_info.addresses[0].google_maps_place_id
            if place_id:
                _sync_opening_hours_location(place_id, sln_settings.service_user, service_identity)


def _sync_opening_hours_location(google_place_id, service_user, service_identity):
    fields = ['opening_hours']
    data = get_place_details(google_place_id, fields)
    if 'opening_hours' not in data:
        return
    if 'periods' not in data['opening_hours']:
        return

    key = OpeningHours.create_key(service_user, service_identity)
    opening_hours = key.get() or OpeningHours(key=key, type=OpeningHours.TYPE_STRUCTURED)
    opening_hours.periods = [OpeningPeriod(open=OpeningHour(day=period['open']['day'],
                                                            time=period['open']['time']),
                                           close=OpeningHour(day=period['close']['day'],
                                                             time=period['close']['time']))
                             for period in data['opening_hours']['periods']]

    if opening_hours.periods:
        opening_hours.put()
