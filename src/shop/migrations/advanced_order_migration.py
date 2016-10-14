# -*- coding: utf-8 -*-
# Copyright 2016 Mobicage NV
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
# @@license_version:1.1@@

from rogerthat.bizz.job import run_job
from solutions.common.bizz import common_provision
from solutions.common.models import SolutionSettings, RestaurantMenu


def job():
    run_job(get_all_solution_settings_keys, [],
            _re_provision, [])


def get_all_solution_settings_keys():
    return SolutionSettings.all(keys_only=True)


def _re_provision(sln_settings_key):
    sln_settings = SolutionSettings.get(sln_settings_key)
    if 'order' in sln_settings.modules and not sln_settings.updates_pending:
        menu = RestaurantMenu.get(RestaurantMenu.create_key(sln_settings.service_user, sln_settings.solution))
        if menu:
            for category in menu.categories:
                for item in category.items:
                    if not item.has_price:
                        common_provision(sln_settings.service_user)
                        return
