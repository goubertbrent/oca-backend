# -*- coding: utf-8 -*-
# Copyright 2018 Mobicage NV
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

import logging

from google.appengine.ext import db, deferred

from rogerthat.dal.profile import get_service_profile
from rogerthat.bizz.job import run_job
from rogerthat.consts import MIGRATION_QUEUE
from rogerthat.utils.transactions import run_in_xg_transaction

from solutions.common.bizz import SolutionModule, common_provision
from solutions.common.models import SolutionSettings


def job(dry_run=True):
    run_job(all_settings, [], update_service_profile, [dry_run])


def all_settings():
    return SolutionSettings.all(keys_only=True).filter("modules =", SolutionModule.BROADCAST)


def update_service_profile(sln_settings_key, dry_run):

    def trans():
        sln_settings = db.get(sln_settings_key)
        service_user = sln_settings.service_user
        if sln_settings.broadcast_types:
            service_profile = get_service_profile(service_user)
            if service_profile and not service_profile.broadcastTypes:
                if dry_run:
                    logging.debug('Should provision (a service profile with no broadcast types): %s', service_user)
                else:
                    deferred.defer(common_provision, service_user, _queue=MIGRATION_QUEUE, _transactional=True)

    run_in_xg_transaction(trans)
