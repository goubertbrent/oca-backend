# -*- coding: utf-8 -*-
# Copyright 2018 GIG Technology NV
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
# @@license_version:1.4@@
import time

from google.appengine.ext import db

from shop.models import OrderItem, Order, Product


def f_date(timestamp):
    return time.strftime('%Y/%m/%d', time.localtime(timestamp))


def migrate(dry_run=True):
    order_items = OrderItem.all().filter('last_charge_timestamp >', 0).fetch(None)  # type: list[OrderItem]
    order_keys = [item.parent_key() for item in order_items]
    customer_orders = {order.order_number: order for order in db.get(order_keys)}  # type: dict[str, Order]
    to_put = []
    apple_product = Product.get_by_key_name('APPL')
    seconds_in_year = 365 * 24 * 3600
    info = []
    for order_item in order_items:
        order = customer_orders[order_item.order_number]
        order.charge_interval = 12
        new_charge_date = int(order_item.last_charge_timestamp + seconds_in_year)
        info.append('%s: created %s - signed %s - setting from %s => %s - %s' % (
            order.order_number, f_date(order.date), f_date(order.date_signed), f_date(order.next_charge_date),
            f_date(new_charge_date),
            'https://rogerthat-server.appspot.com/internal/shop/order/pdf?customer_id=%s&order_number=%s' % (
                order.customer_id, order.order_number)))
        order.next_charge_date = new_charge_date
        delattr(order_item, 'last_charge_timestamp')
        if order_item.product_code != 'APPL':
            raise Exception('Invalid product code %s' % order_item.product_code)
        order_item.price = apple_product.price
        to_put.append(order)
        to_put.append(order_item)
    if not dry_run:
        db.put(to_put)
    return len(to_put), info
