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

from rogerthat.bizz.job import run_job
from google.appengine.ext import db
from solutions.common.migrations.flow_stats import get_all_solution_settings_keys
from solutions.common.bizz import SolutionModule, common_provision


TO_BE_MIGRATED = (SolutionModule.ASK_QUESTION,
                  SolutionModule.APPOINTMENT,
                  SolutionModule.PHARMACY_ORDER,
                  SolutionModule.REPAIR,
                  SolutionModule.SANDWICH_BAR,
                  )


def job():
    run_job(get_all_solution_settings_keys, [],
            migrate_flows, [])


def migrate_flows(sln_settings_key):
    sln_settings = db.get(sln_settings_key)
    if any(m in TO_BE_MIGRATED for m in sln_settings.modules):
        common_provision(sln_settings.service_user)
