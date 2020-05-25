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

from rogerthat.bizz.job import run_job
from rogerthat.models import ProfileHashIndex, Profile
from rogerthat.rpc import users


def job():
    run_job(get_all_profiles, list(),
            create_profile_hash_index, list())


def get_all_profiles():
    return Profile.all(keys_only=True)


def create_profile_hash_index(profile_key):
    ProfileHashIndex.create(users.User(profile_key.name())).put()