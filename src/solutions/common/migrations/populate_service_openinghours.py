# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
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
# @@license_version:1.5@@

from google.appengine.ext import db

from rogerthat.bizz.job import run_job
from rogerthat.bizz.opening_hours import save_textual_opening_hours
from shop.constants import MAPS_QUEUE
from solutions.common.dal import get_solution_settings_or_identity_settings
from solutions.common.models import SolutionSettings
from solutions.common.utils import is_default_service_identity


def all_solution_settings():
    return SolutionSettings.all(keys_only=True)


def job():
    run_job(all_solution_settings, [], try_to_set_openinghours, [], worker_queue=MAPS_QUEUE)


def try_to_set_openinghours(settings_key):
    sln_settings = db.get(settings_key)
    if sln_settings:
        if sln_settings.identities:
            for identity in sln_settings.identities:
                identity_settings = get_solution_settings_or_identity_settings(sln_settings, identity)
                if is_default_service_identity(identity):
                    save_textual_opening_hours(identity_settings.service_user.email(), identity_settings.opening_hours)
                else:
                    save_textual_opening_hours(identity_settings.service_identity_user.email(), identity_settings.opening_hours)
        else:
            save_textual_opening_hours(sln_settings.service_user.email(), sln_settings.opening_hours)

