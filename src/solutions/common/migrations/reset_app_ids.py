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

from rogerthat.bizz.job import run_job
from rogerthat.bizz.service import re_index
from rogerthat.consts import MIGRATION_QUEUE
from rogerthat.dal import put_and_invalidate_cache
from rogerthat.dal.service import get_default_service_identity
from rogerthat.models import App
from rogerthat.utils.transactions import run_in_xg_transaction
from shop.bizz import re_index_customer
from shop.dal import get_customer
from shop.models import Customer
from solutions.common.models import SolutionSettings
from solutions.flex import SOLUTION_FLEX


def job(dry_run=True):
    run_job(_qry, [], _worker, [dry_run])


def _qry():
    return SolutionSettings.all(keys_only=True)


def _worker(sln_settings_key, dry_run):
    sln_settings = db.get(sln_settings_key)
    if sln_settings.solution != SOLUTION_FLEX:
        return
    service_user = sln_settings.service_user
    c = get_customer(service_user)
    if not c:
        logging.error("Failed to reset app ids for customer 'None' for service user '%s'", service_user,
                      _suppress=False)
        return
    if c.app_id in (App.APP_ID_ROGERTHAT, App.APP_ID_OSA_LOYALTY):
        logging.error("Failed to reset app ids for customer '%s' (%s) since default app is %s...", c.name, c.id,
                      c.app_id, _suppress=False)
        return

    def trans(customer_id):
        customer = Customer.get_by_id(customer_id)
        if not customer:
            return

        app_ids = list(customer.sorted_app_ids)
        has_rogerthat = App.APP_ID_ROGERTHAT in app_ids
        has_osa_loyalty = App.APP_ID_OSA_LOYALTY in app_ids
        if has_rogerthat:
            app_ids.remove(App.APP_ID_ROGERTHAT)
        if has_osa_loyalty:
            app_ids.remove(App.APP_ID_OSA_LOYALTY)
        logging.debug("Removing the following app_ids %s from %s for customer '%s' (%s)", app_ids[1:],
                      customer.sorted_app_ids, customer.name, customer.id)
        if not app_ids[1:]:
            return
        customer.app_ids = app_ids[:1]
        if has_rogerthat:
            customer.app_ids.append(App.APP_ID_ROGERTHAT)
        if has_osa_loyalty:
            customer.app_ids.append(App.APP_ID_OSA_LOYALTY)

        logging.debug('app_ids updated to %s', customer.app_ids)
        service_identity = get_default_service_identity(service_user)
        service_identity.appIds = customer.app_ids

        if not dry_run:
            to_put = [customer, service_identity]

            deferred.defer(re_index, service_identity.service_identity_user, _queue=MIGRATION_QUEUE,
                           _transactional=True)
            deferred.defer(re_index_customer, customer.key(), _queue=MIGRATION_QUEUE, _transactional=True)

            put_and_invalidate_cache(*to_put)

    run_in_xg_transaction(trans, c.id)
