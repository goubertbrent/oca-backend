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
from solutions.common.models import SolutionSettings


def job():
    run_job(_query, [], _worker, [], worker_queue=MIGRATION_QUEUE)


def _query():
    return SolutionSettings.all(keys_only=True)


def _worker(sln_settings_key):
    sln_settings = db.get(sln_settings_key)  # type: SolutionSettings
    if sln_settings.activated_modules_json:
        return
    data = {}
    for module in sln_settings.activated_modules:
        data[module.name] = module
    sln_settings.save_activated_modules(data)
    sln_settings.activated_modules = None
    sln_settings.put()