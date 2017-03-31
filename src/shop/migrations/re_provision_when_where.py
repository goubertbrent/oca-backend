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

import logging

from rogerthat.bizz.job import run_job
from rogerthat.consts import MIGRATION_QUEUE
from rogerthat.utils.transactions import run_in_xg_transaction, allow_transaction_propagation
from solutions.common.bizz import common_provision, SolutionModule
from solutions.common.models import SolutionSettings


def job():
    run_job(get_all_solution_settings_keys, [SolutionModule.WHEN_WHERE],
            _re_provision, [], worker_queue=MIGRATION_QUEUE)


def get_all_solution_settings_keys(module):
    return SolutionSettings.all(keys_only=True).filter('modules', module)


def _re_provision(sln_settings_key):
    sln_settings = SolutionSettings.get(sln_settings_key)
    if sln_settings.updates_pending == False:
        logging.info('Provisioning %s', sln_settings.name)
        allow_transaction_propagation(run_in_xg_transaction, common_provision, sln_settings.service_user, sln_settings)
