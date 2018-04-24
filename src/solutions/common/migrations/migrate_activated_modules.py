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
# @@license_version:1.3@@

from google.appengine.ext import db

from rogerthat.bizz.job import run_job
from rogerthat.consts import MIGRATION_QUEUE
from solutions.common.models import SolutionSettings
from solutions.common.models.properties import ActivatedModules, ActivatedModule


def job():
    run_job(_query, [], _worker, [], worker_queue=MIGRATION_QUEUE)


def _query():
    return SolutionSettings.all(keys_only=True)


def _worker(ss_key):

    def trans():
        sln_settings = db.get(ss_key)
        if sln_settings.activated_modules:
            return
        sln_settings.activated_modules = ActivatedModules()
        for module in sln_settings.provisioned_modules:
            activated_module = ActivatedModule()
            activated_module.name = module
            activated_module.timestamp = 0
            sln_settings.activated_modules.add(activated_module)
        sln_settings.put()

    db.run_in_transaction(trans)
