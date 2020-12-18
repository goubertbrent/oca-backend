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

from datetime import datetime
import logging

from dateutil.relativedelta import relativedelta
from google.appengine.ext import db, deferred

from mcfw.properties import azzert
from rogerthat.bizz.job import run_job
from rogerthat.dal import put_and_invalidate_cache
from rogerthat.utils import now
from rogerthat.utils.transactions import run_in_xg_transaction
from shop.business.audit import audit_log
from shop.business.order import cancel_order
from shop.business.service import set_service_disabled
from shop.exceptions import OrderAlreadyCanceledException
from shop.models import Order, Charge, OrderItem, Customer, Product


def schedule_recurrent_billing():
    deferred.defer(_recurrent_billing, _transactional=db.is_in_transaction())


def _recurrent_billing():
    today = now()
    products = Product.get_products_dict()
    run_job(_qry, [today], _create_charge, [today, products])


def _qry(today):
    # next_charge_date is unset for free subscriptions
    return Order.all(keys_only=True) \
        .filter("is_subscription_order =", True) \
        .filter("next_charge_date <", today) \
        .filter("status =", Order.STATUS_SIGNED)


def _create_charge(order_key, today, products):

    def trans():
        customer_id = order_key.parent().id()
        order, customer = db.get([order_key, Customer.create_key(customer_id)])
        if not order.next_charge_date:
            logging.warning('Not creating recurrent charge for order %s (%s: %s) because no next charge date is set',
                            order.order_number, customer_id, customer.name)
            return None
        elif order.next_charge_date > today:
            # Scenario: this job fails today, tomorrow this job runs again and fails again
            # -> 2 jobs for the same order would create 2 charges when the bug is fixed
            logging.warning('This order has already been charged this month, skipping... %s (%s: %s)',
                            order.order_number, customer_id, customer.name)
            return None
        elif customer.subscription_cancel_pending_date:
            logging.info('Disabling service from customer %s (%d)', customer.name, customer.id)
            try:
                cancel_order(customer, order.order_number)
            except OrderAlreadyCanceledException as exception:
                logging.info('Order %s already canceled, continuing...', exception.order.order_number)

            set_service_disabled(customer, Customer.DISABLED_OTHER)
            return None

        logging.info("Creating recurrent charge for order %s (%s: %s)", order.order_number, customer_id, customer.name)
        azzert(12 >= order.charge_interval >= 1, 'Expected charge interval to be between 1 and 12')
        subscription_extension_orders = list(Order.all()
                                             .ancestor(customer)
                                             .filter("next_charge_date <", today)
                                             .filter("is_subscription_order =", False)
                                             .filter('is_subscription_extension_order =', True)
                                             .filter("status =", Order.STATUS_SIGNED))  # type: list[Order]
        subscription_extension_order_keys = [o.key() for o in subscription_extension_orders]
        order_item_qry = OrderItem.all().ancestor(customer if subscription_extension_order_keys else order)

        subscription_extension_order_item_keys = []
        total_amount = 0
        subscription_length = 0
        to_put = []

        def _get_item_price(order_item):
            return order_item.price * order.charge_interval

        orders = {order.order_number: order}
        for order_item in order_item_qry:  # type: OrderItem
            product = products.get(order_item.product_code)
            if not product:
                logging.info('Product with code %s does not exist anymore, skipping', order_item.product_code)
                continue

            o = orders.get(order_item.order_number)
            if not o:
                o = Order.get_by_order_number(customer_id, order_item.order_number)
                orders[o.order_number] = o
            if o.status == Order.STATUS_CANCELED:
                logging.debug('Skipping order item %s of canceled order %s',
                              order_item.product_code, order_item.order_number)
                continue

            if order_item.order_number == order.order_number:
                if product.is_subscription:
                    subscription_length = order_item.count
                    total_amount += _get_item_price(order_item)
                elif product.is_subscription_discount or product.is_subscription_extension:
                    total_amount += _get_item_price(order_item)
            elif order_item.parent().key() in subscription_extension_order_keys:
                if product.is_subscription_extension:
                    total_amount += _get_item_price(order_item)
                    subscription_extension_order_item_keys.append(order_item.key())

        if total_amount == 0:
            order.next_charge_date = Order.default_next_charge_date()
            order.put()
            logging.info("Skipping, cannot calculate recurrent charge of 0 euros for order %s (%s: %s)",
                         order.order_number, customer_id, customer.name)
            return None

        if subscription_length == 0:
            raise Exception('subscription_length is 0')

        if subscription_length != 1:
            logging.debug('Tried to bill customer, but no credit card info was found')
            audit_log(customer.id, 'Tried to bill customer, but no credit card info was found')
            return None

        @db.non_transactional  # prevent contention on entity group RegioManagerTeam
        def get_currency_code():
            return customer.team.legal_entity.currency_code

        charge = Charge(parent=order_key)
        charge.date = now()
        charge.type = Charge.TYPE_RECURRING_SUBSCRIPTION
        charge.subscription_extension_length = order.charge_interval
        charge.subscription_extension_order_item_keys = subscription_extension_order_item_keys
        charge.currency_code = get_currency_code()
        charge.team_id = customer.team_id
        charge.amount = total_amount
        charge.vat_pct = order.vat_pct
        charge.vat = int(total_amount * order.vat_pct / 100)
        charge.total_amount = charge.amount + charge.vat
        to_put.append(charge)

        next_charge_datetime = datetime.utcfromtimestamp(order.next_charge_date) + relativedelta(
            months=order.charge_interval)
        next_charge_date_int = int((next_charge_datetime - datetime.utcfromtimestamp(0)).total_seconds())
        order.next_charge_date = next_charge_date_int
        to_put.append(order)
        for extension_order in subscription_extension_orders:
            extension_order.next_charge_date = next_charge_date_int
            to_put.append(extension_order)

        put_and_invalidate_cache(*to_put)
        return charge

    try:
        return run_in_xg_transaction(trans)
    except Exception as e:
        logging.exception("Failed to create new charge: %s" % e.message, _suppress=False)
