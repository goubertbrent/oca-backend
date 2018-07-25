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

import datetime

from dateutil.relativedelta import relativedelta
from google.appengine.ext import db

from rogerthat.utils import now, get_epoch_from_datetime
from mcfw.rpc import arguments, returns
from shop.models import Charge, Order, OrderItem, Customer


@returns()
@arguments(customer_id=(int, long), order_number=unicode, charge_id=(int, long))
def cancel_charge(customer_id, order_number, charge_id):
    """Cancels a charge so adjustments can be made to the order. Rolls back the next charge date of the subscription order.

    Args:
        customer_id:
        order_number:
        charge_id:

    Returns:
        None
    """
    to_put = list()
    now_ = now()
    charge, order, customer = db.get([Charge.create_key(charge_id, order_number, customer_id),
                                      Order.create_key(customer_id, order_number),
                                      Customer.create_key(customer_id)])
    charge.date_cancelled = now_
    charge.status = Charge.STATUS_CANCELLED
    to_put.append(charge)
    order_items = list(OrderItem.list_by_order(order.key()))
    if order.is_subscription_order:
        months = 0
        for item in order_items:
            product = item.product
            if product.is_subscription and product.price > 0:
                months += item.count
            if not product.is_subscription and product.extra_subscription_months > 0:
                months += product.extra_subscription_months

        if months > 0:
            next_charge_datetime = datetime.datetime.utcfromtimestamp(now()) - relativedelta(months=months)
            order.next_charge_date = get_epoch_from_datetime(next_charge_datetime)
        else:
            order.next_charge_date = Order.default_next_charge_date()
    else:
        extra_months = 0
        for item in order_items:
            product = item.product
            if not product.is_subscription and product.extra_subscription_months > 0:
                extra_months += product.extra_subscription_months

        if extra_months > 0:
            sub_order = Order.get_by_order_number(customer_id, customer.subscription_order_number)
            next_charge_datetime = datetime.datetime.utcfromtimestamp(sub_order.next_charge_date) - relativedelta(
                months=extra_months)
            sub_order.next_charge_date = get_epoch_from_datetime(next_charge_datetime)
            to_put.append(sub_order)
    db.put(to_put)
