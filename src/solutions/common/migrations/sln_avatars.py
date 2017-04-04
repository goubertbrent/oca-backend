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

from rogerthat.bizz.job import run_job
from rogerthat.dal.profile import get_avatar_by_id, get_service_profile
from rogerthat.rpc import users
from rogerthat.utils.transactions import run_in_xg_transaction
from solutions.common.models import SolutionSettings, SolutionAvatar


def job():
    run_job(get_all_solution_settings_keys, [],
            migrate_avatar, [])


def get_all_solution_settings_keys():
    return SolutionSettings.all(keys_only=True)


def migrate_avatar(sln_settings_key):
    service_user = users.User(sln_settings_key.id_or_name())

    def trans():
        service_profile = get_service_profile(service_user)
        if not service_profile:
            return
        sln_avatar = SolutionAvatar(key=SolutionAvatar.create_key(service_user))
        sln_avatar.picture = get_avatar_by_id(service_profile.avatarId).picture
        sln_avatar.put()

    run_in_xg_transaction(trans)
