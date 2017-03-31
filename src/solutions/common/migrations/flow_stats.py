# -*- coding: utf-8 -*-
# Copyright 2017 GIG Technology NV
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

from rogerthat.bizz.job import run_job
from rogerthat.bizz.job.update_friends import schedule_update_all_friends_of_service_user
from rogerthat.bizz.service.mfd import render_js_for_message_flow_designs
from rogerthat.dal import put_and_invalidate_cache
from rogerthat.dal.mfd import get_message_flow_designs_by_status
from rogerthat.models import MessageFlowDesign
from rogerthat.rpc import users
from mcfw.utils import chunks
from solutions.common.models import SolutionSettings
from rogerthat.utils.transactions import run_in_xg_transaction


def job():
    run_job(get_all_solution_settings_keys, [],
            start_migration_for_solution_services, [])


def get_all_solution_settings_keys():
    return SolutionSettings.all(keys_only=True)


def start_migration_for_solution_services(sln_settings_key):
    service_user = users.User(sln_settings_key.id_or_name())

    def trans():
        mfd_list = [mfd for mfd in get_message_flow_designs_by_status(service_user, MessageFlowDesign.STATUS_VALID)
                    if mfd.xml and not mfd.definition]  # XML-only flows
        render_js_for_message_flow_designs(mfd_list,
                                           notify_friends=False)
        for chunk in chunks(mfd_list, 200):
            put_and_invalidate_cache(*chunk)
        schedule_update_all_friends_of_service_user(service_user)

    run_in_xg_transaction(trans)
