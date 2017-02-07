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

from rogerthat.bizz.job import run_job
from rogerthat.dal import parent_key
from google.appengine.ext import db
from solutions.common import SOLUTION_COMMON
from solutions.common.bizz import SolutionModule
from solutions.common.models import SolutionSettings
from solutions.common.models.order import SolutionOrder

def job():
    run_job(_get_order_solution_settings, [], _set_deleted_status, [])

def _get_order_solution_settings():
    return SolutionSettings.all().filter("modules =", SolutionModule.ORDER)

def _set_deleted_status(sln_settings):
    to_put = []
    for sc in SolutionOrder.all().ancestor(parent_key(sln_settings.service_user, SOLUTION_COMMON)):
        if not sc.deleted:
            if sc.status == SolutionOrder.STATUS_COMPLETED:
                sc.deleted = True
            else:
                sc.deleted = False
            to_put.append(sc)

    logging.info("updated '%s' order for user %s", len(to_put), sln_settings.service_user)
    db.put(to_put)
