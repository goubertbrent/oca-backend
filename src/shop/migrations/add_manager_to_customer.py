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
from shop.models import Customer, Order


def job():
    run_job(_all_customers, [],
            _add_manager, [])


def _all_customers():
    return Customer.all()


def _add_manager(customer):
    order_number = customer.subscription_order_number
    if not order_number:
        return

    def trans(customer_key):
        customer, order = db.get([customer_key, Order.create_key(customer_key.id(), order_number)])
        if order.manager:
            customer.manager = order.manager
            customer.put()
    db.run_in_transaction(trans, customer.key())
