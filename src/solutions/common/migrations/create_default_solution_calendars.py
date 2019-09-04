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

import logging

from google.appengine.ext import db
from rogerthat.bizz.job import run_job
from rogerthat.consts import MIGRATION_QUEUE
from rogerthat.dal import parent_key, put_and_invalidate_cache
from solutions.common.bizz import SolutionModule
from solutions.common.models import SolutionSettings
from solutions.common.models.agenda import SolutionCalendar


def _put_calendar_model(sln_settings, key=None):
    kwargs = dict(name='Default', deleted=False)
    if key is None:
        kwargs['parent'] = parent_key(sln_settings.service_user, sln_settings.solution)
    else:
        kwargs['key'] = key
    sc = SolutionCalendar(**kwargs)
    sc.put()
    return sc


# partly copy/pasted from provisioning.put_agenda
def _create_default_calendar(sln_settings_key):
    sln_settings = db.get(sln_settings_key)

    if not sln_settings:
        return

    if SolutionModule.AGENDA not in sln_settings.modules:
        return

    if sln_settings.default_calendar:
        key = db.Key.from_path(SolutionCalendar.kind(), sln_settings.default_calendar,
                               parent=parent_key(sln_settings.service_user, sln_settings.solution))
        if not db.get(key):
            logging.debug('Default calendar of %s (%s) did not exist', sln_settings.name, sln_settings.service_user)
            _put_calendar_model(sln_settings, key).put()

    else:
        def trans():
            sc = _put_calendar_model(sln_settings, None)
            sln_settings.default_calendar = sc.calendar_id
            put_and_invalidate_cache(sln_settings)
            return sc

        logging.debug('Creating default calendar for: %s (%s)', sln_settings.name, sln_settings.service_user)
        xg_on = db.create_transaction_options(xg=True)
        db.run_in_transaction_options(xg_on, trans)


def _all_solution_settings():
    return SolutionSettings.all(keys_only=True)


def job():
    run_job(_all_solution_settings, [], _create_default_calendar, [], worker_queue=MIGRATION_QUEUE)
