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

from rogerthat.bizz.job import run_job
from rogerthat.consts import MIGRATION_QUEUE
from google.appengine.ext import db
from google.appengine.ext.deferred import deferred
from mcfw.utils import chunks
from shop.models import OrderItem, Product, Order


def job():
    deferred.defer(_job, _queue=MIGRATION_QUEUE)


def _job():
    products = {p.code: p for p in Product.all()}
    order_keys = set()
    for order_item in OrderItem.all():
        if products[order_item.product_code].is_subscription_extension:
            order_keys.add(order_item.order_key)

    orders = db.get(order_keys)
    to_put = list()
    for order in orders:
        if not order.is_subscription_extension_order:
            order.is_subscription_extension_order = True
            customer = order.parent()
            subscription_order = Order.get_by_order_number(customer.id, customer.subscription_order_number)
            order.next_charge_date = subscription_order.next_charge_date
            to_put.append(order)

    for chunk in chunks(to_put, 200):
        db.put(chunk)


def job2():
    run_job(_qry2, [], _worker2, [])


def _qry2():
    return Order.all(keys_only=True).filter('next_charge_date', None)


def _worker2(order_key):
    def t():
        order = db.get(order_key)
        order.next_charge_date = Order.NEVER_CHARGE_DATE
        order.put()
    db.run_in_transaction(t)
