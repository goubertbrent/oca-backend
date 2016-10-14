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

import logging

from google.appengine.ext.deferred import deferred

from rogerthat.bizz.job import run_job
from rogerthat.consts import MIGRATION_QUEUE
from rogerthat.utils.transactions import run_in_xg_transaction, allow_transaction_propagation
from solutions.common.bizz import common_provision
from solutions.common.models import SolutionSettings


def job():
    run_job(get_all_solution_settings_keys, [],
            _deferred_re_provision, [])


def get_all_solution_settings_keys():
    return SolutionSettings.all(keys_only=True).filter('modules', 'when_where')


def _deferred_re_provision(sln_settings_key):
    deferred.defer(_re_provision_when_where, sln_settings_key, _queue=MIGRATION_QUEUE)


def _re_provision_when_where(sln_settings_key):
    sln_settings = SolutionSettings.get(sln_settings_key)
    if sln_settings.updates_pending == False and len(sln_settings.holidays) != 0:
        logging.info('Provisioning %s', sln_settings.name)
        allow_transaction_propagation(run_in_xg_transaction, common_provision, sln_settings.service_user, sln_settings)
