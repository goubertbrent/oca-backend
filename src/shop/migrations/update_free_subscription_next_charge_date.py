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

from datetime import datetime
from dateutil.relativedelta import relativedelta

from rogerthat.bizz.job import run_job
from rogerthat.dal import put_and_invalidate_cache
from rogerthat.consts import MIGRATION_QUEUE

from shop.models import Order, Product

# was in shop.models.Order
NEVER_CHARGE_DATE = 253402300799  # 31 Dec 9999 23:59:59 GMT


def job():
    default_next_charge_date = Order.default_next_charge_date()
    run_job(_all_subscription_orders, [], _update_next_charge_date, [default_next_charge_date],
            worker_queue=MIGRATION_QUEUE)


def _all_subscription_orders():
    return Order.all(keys_only=True)\
        .filter('is_subscription_order =', True)\
        .filter('next_charge_date =', NEVER_CHARGE_DATE)


def _update_next_charge_date(order_key, default_next_charge_date):
    """Set next charge date to next month."""
    order = Order.get(order_key)

    def is_free_subscription(order_item):
        return order_item.product_code == Product.PRODUCT_FREE_SUBSCRIPTION

    order_items = order.list_items()
    if any([is_free_subscription(item) for item in order_items]):
        order.next_charge_date = default_next_charge_date
        put_and_invalidate_cache(order)
