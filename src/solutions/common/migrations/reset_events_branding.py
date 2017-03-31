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

from google.appengine.ext import deferred, db

from rogerthat.bizz.job import run_job
from rogerthat.consts import MIGRATION_QUEUE
from solutions.common.bizz import SolutionModule, common_provision
from solutions.common.models import SolutionSettings


def job(provision=True):
    run_job(_get_agenda_solution_settings, [], _update_settings, [provision])


def _get_agenda_solution_settings():
    return SolutionSettings.all(keys_only=True).filter("modules =", SolutionModule.AGENDA)


def _update_settings(sln_settings_key, provision):
    def trans():
        sln_settings = db.get(sln_settings_key)
        sln_settings.events_branding_hash = None
        sln_settings.put()
        if provision:
            deferred.defer(common_provision, sln_settings.service_user, _queue=MIGRATION_QUEUE, _countdown=1,
                           _transactional=True)

    db.run_in_transaction(trans)
