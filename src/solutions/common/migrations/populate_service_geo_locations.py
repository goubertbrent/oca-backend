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

from google.appengine.ext import db

from rogerthat.bizz.job import run_job

from solutions.common.bizz import _get_location
from solutions.common.bizz.provisioning import populate_identity_and_publish
from solutions.common.dal import get_solution_settings, get_solution_settings_or_identity_settings, \
    get_solution_main_branding
from solutions.common.models import SolutionSettings


def all_solution_settings():
    return SolutionSettings.all(keys_only=True)


def job():
    run_job(all_solution_settings, [], try_to_set_location, [])



def try_to_set_location(settings_key):
    to_put = []

    def set_location(settings):
        if settings.address and not settings.location:
            try:
                lat, lon = _get_location(settings.address)
                settings.location = db.GeoPt(lat, lon)
                to_put.append(settings)
            except:
                logging.warning("Failed to resolve address of %s: %s", settings.service_user.email(), settings.address, exc_info=1)

    sln_settings = db.get(settings_key)
    if sln_settings:
        if sln_settings.identities:
            for identity in sln_settings.identities:
                identity_settings = get_solution_settings_or_identity_settings(sln_settings, identity)
                set_location(identity_settings)
        else:
             set_location(sln_settings)

        if to_put:
            db.put(to_put)
            service_user = sln_settings.service_user
            main_branding_key = get_solution_main_branding(service_user).branding_key
            populate_identity_and_publish(service_user, main_branding_key)
