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
import time

from rogerthat.bizz.job import run_job
from rogerthat.bizz.job.update_friends import schedule_update_a_friend_of_a_service_identity_user
from rogerthat.consts import HIGH_LOAD_CONTROLLER_QUEUE
from rogerthat.dal.service import get_all_service_friend_keys_query
from rogerthat.models import App
from rogerthat.rpc import users
from rogerthat.utils import now
from rogerthat.utils.app import get_app_id_from_app_user
from rogerthat.utils.service import create_service_identity_user
from google.appengine.ext import db, deferred
from solutions.common.bizz.provisioning import populate_identity
from solutions.common.dal import get_solution_settings, get_solution_main_branding
from solutions.common.models.loyalty import SolutionLoyaltySettings
from solutions.common.utils import is_default_service_identity


def job():
    run_job(_get_loyalty_settings, [], _migrate, [])


def _get_loyalty_settings():
    return SolutionLoyaltySettings.all(keys_only=True)


def _migrate(sls_key):
    def trans():
        sln_loyalty_settings = db.get(sls_key)
        sln_loyalty_settings.modification_time = now()
        sln_loyalty_settings.put()
        sln_settings = get_solution_settings(sln_loyalty_settings.service_user)
        if not sln_settings.updates_pending:
            deferred.defer(_set_content_branding, sln_settings, _transactional=True)
    db.run_in_transaction(trans)


def _set_content_branding(sln_settings):
    users.set_user(sln_settings.service_user)
    try:
        sln_main_branding = get_solution_main_branding(sln_settings.service_user)
        populate_identity(sln_settings, sln_main_branding.branding_key)

        identities = [None]
        if sln_settings.identities:
            identities.extend(sln_settings.identities)
        for service_identity in identities:
            if is_default_service_identity(service_identity):
                service_identity_user = create_service_identity_user(sln_settings.service_user)
            else:
                service_identity_user = create_service_identity_user(sln_settings.service_user, service_identity)
            deferred.defer(_update_tablets, service_identity_user, None, _queue=HIGH_LOAD_CONTROLLER_QUEUE)
    finally:
        users.clear_user()


def _update_tablets(service_identity_user, cursor):
    start = time.time()
    qry = get_all_service_friend_keys_query(service_identity_user)
    while True:
        qry.with_cursor(cursor)
        fsic_keys = qry.fetch(100)
        cursor = qry.cursor()
        logging.debug("Fetched %s FriendServiceIdentityConnection keys", len(fsic_keys))
        if not fsic_keys:  # Query reached its end
            return
        for fsic_key in fsic_keys:
            app_user = users.User(fsic_key.parent().name())
            app_id = get_app_id_from_app_user(app_user)
            if app_id != App.APP_ID_OSA_LOYALTY:
                continue

            deferred.defer(schedule_update_a_friend_of_a_service_identity_user,
                           service_identity_user, app_user, force=True)

        if time.time() - start > 500:
            deferred.defer(_update_tablets, service_identity_user, cursor, _queue=HIGH_LOAD_CONTROLLER_QUEUE)
            return
