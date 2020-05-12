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

from google.appengine.ext import db

from rogerthat.bizz.job import run_job, MODE_BATCH
from rogerthat.dal import put_and_invalidate_cache
from rogerthat.models import ServiceProfile


def migrate():
    run_job(_get_profiles, [], _migrate_profile, [], MODE_BATCH, batch_size=500)


def _get_profiles():
    return ServiceProfile.all(keys_only=True)


def _migrate_profile(profile_keys):
    profiles = db.get(profile_keys)  # type: list[ServiceProfile]
    to_put = []
    for profile in profiles:
        if not profile.callBackURI:
            logging.info('Updating callBackURI from %s to %s', profile.callBackURI, 'mobidick')
            profile.callBackURI = 'mobidick'
            profile.testCallNeeded = False
            profile.enabled = True
            to_put.append(profile)
    if to_put:
        put_and_invalidate_cache(*to_put)
