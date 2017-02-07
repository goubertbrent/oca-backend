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

import logging

from rogerthat.bizz.job import run_job
from rogerthat.rpc import users
from rogerthat.service.api import system
from google.appengine.ext import deferred
from solutions.common.bizz import SolutionModule, get_coords_of_service_menu_item, common_provision
from solutions.common.bizz.messaging import POKE_TAG_NEW_EVENT
from solutions.common.models import SolutionSettings
from rogerthat.dal import put_and_invalidate_cache


def job():
    run_job(_get_agenda_solution_settings, [], _remove_new_event_item, [])


def _get_agenda_solution_settings():
    return SolutionSettings.all().filter("modules =", SolutionModule.AGENDA)


def _remove_new_event_item(sln_settings):
    users.set_user(sln_settings.service_user)
    try:
        service_menu = system.get_menu()
        current_coords = get_coords_of_service_menu_item(service_menu, POKE_TAG_NEW_EVENT)
        logging.info("remove new event item for %s coords %s", sln_settings.service_user, current_coords)
        if current_coords:
            system.delete_menu_item(current_coords)

        sln_settings.events_branding_hash = None
        put_and_invalidate_cache(sln_settings)
        deferred.defer(common_provision, sln_settings.service_user)
    finally:
        users.clear_user()
