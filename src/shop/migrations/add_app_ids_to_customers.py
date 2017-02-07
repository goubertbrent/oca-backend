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

from google.appengine.ext import db

from rogerthat.bizz.job import run_job
from rogerthat.dal.service import get_default_service_identity
from rogerthat.rpc import users
from shop.models import Customer


def job():
    run_job(_all_customers, [],
            _add_app_ids, [])


def _all_customers():
    return Customer.all()


def _add_app_ids(customer):
    if customer.service_email is None:
        return
    si = get_default_service_identity(users.User(customer.service_email))

    def trans(customer_key):
        customer = db.get(customer_key)
        customer.app_ids = si.appIds
        customer.extra_apps_count = len(si.appIds) - 2
        if customer.extra_apps_count < 0:
            customer.extra_apps_count = 0
        customer.put()

    db.run_in_transaction(trans, customer.key())
