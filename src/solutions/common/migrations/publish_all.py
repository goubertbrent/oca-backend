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

from google.appengine.ext import db

from rogerthat.bizz.job import run_job
from rogerthat.consts import MIGRATION_QUEUE
from solutions.common.bizz import common_provision
from solutions.common.models import SolutionSettings


def provision_all(module=None, dry_run=True):
    if dry_run:
        return _get_solution_settings_keys(module).count(None)
    run_job(_get_solution_settings_keys, [module], _publish, [], worker_queue=MIGRATION_QUEUE)


def _get_solution_settings_keys(module):
    q = SolutionSettings.all(keys_only=True)
    if module:
        q = q.filter('modules', module)
    return q


def _publish(sln_settings_key):
    sln_settings = db.get(sln_settings_key)  # type: SolutionSettings
    if not sln_settings.service_disabled:
        common_provision(sln_settings.service_user)
