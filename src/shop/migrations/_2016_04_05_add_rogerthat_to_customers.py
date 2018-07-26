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

from google.appengine.ext.deferred import deferred

from rogerthat.bizz.job import run_job
from rogerthat.bizz.service import re_index
from rogerthat.consts import MIGRATION_QUEUE
from rogerthat.dal import put_and_invalidate_cache
from rogerthat.dal.service import get_default_service_identity
from rogerthat.models import App
from rogerthat.utils.transactions import run_in_xg_transaction
from shop.bizz import re_index_customer
from shop.models import Customer


def job():
    run_job(qry, [], _job, [], worker_queue=MIGRATION_QUEUE)


def qry():
    return Customer.all(keys_only=True)


def _job(customer_key):
    def trans():
        to_put = list()
        customer = Customer.get(customer_key)
        if App.APP_ID_ROGERTHAT not in customer.app_ids and customer.service_email:
            customer.app_ids.append(App.APP_ID_ROGERTHAT)
            to_put.append(customer)
            service_identity = get_default_service_identity(customer.service_user)
            if App.APP_ID_ROGERTHAT not in service_identity.appIds:
                service_identity.appIds.append(App.APP_ID_ROGERTHAT)
                deferred.defer(re_index, service_identity.service_identity_user, _queue=MIGRATION_QUEUE,
                               _transactional=True)
                to_put.append(service_identity)
            deferred.defer(re_index_customer, customer.key(), _queue=MIGRATION_QUEUE, _transactional=True)
            put_and_invalidate_cache(*to_put)

    run_in_xg_transaction(trans)
