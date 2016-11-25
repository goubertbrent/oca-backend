# -*- coding: utf-8 -*-
# Copyright 2016 Mobicage NV
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
# @@license_version:1.1@@

import datetime
import logging

import dateutil

from mcfw.rpc import returns, arguments
from rogerthat.consts import DAY
from rogerthat.rpc.service import BusinessException
from rogerthat.utils import now
from rogerthat.utils.transactions import run_in_xg_transaction
from shop.bizz import cancel_order
from shop.business.service import set_service_disabled
from shop.exceptions import NoSubscriptionException, EmptyValueException, \
    OrderAlreadyCanceledException, NoSubscriptionFoundException
from shop.models import Customer, Order


@returns(int)
@arguments(customer_id=(int, long))
def get_customer_subscription_length(customer_id):
    customer = Customer.get_by_id(customer_id)
    if not customer.subscription_order_number:
        raise NoSubscriptionFoundException(customer)
    months_till_charge, _ = get_subscription_order_remaining_length(customer_id, customer.subscription_order_number)
    return months_till_charge


@returns(Order)
@arguments(customer_id=(int, long))
def get_subscription_order(customer_id):
    customer = Customer.get_by_id(customer_id)
    if not customer.subscription_order_number:
        raise NoSubscriptionException(customer)
    order = Order.get_by_order_number(customer.id, customer.subscription_order_number)
    if not order.status == Order.STATUS_SIGNED:
        raise BusinessException('The customer his subscription order has not been signed yet.')
    return order


@returns()
@arguments(customer_id=(int, long), next_charge_date=(int, long))
def set_next_charge_date(customer_id, next_charge_date):
    customer = Customer.get_by_id(customer_id)
    if not customer.subscription_order_number:
        raise NoSubscriptionException(customer)
    order = Order.get_by_order_number(customer_id, customer.subscription_order_number)
    if not order.status == Order.STATUS_SIGNED:
        raise BusinessException('The customer his subscription order has not been signed yet.')
    order.next_charge_date = next_charge_date
    order.put()


@returns(tuple)
@arguments(customer_id=(int, long), subscription_order_number=unicode)
def get_subscription_order_remaining_length(customer_id, subscription_order_number):
    subscription_order = Order.get(Order.create_key(customer_id, subscription_order_number))
    if subscription_order.next_charge_date:
        if subscription_order.next_charge_date == Order.NEVER_CHARGE_DATE:
            next_charge_date = subscription_order.next_charge_date
        else:
            next_charge_date = subscription_order.next_charge_date + DAY * 14
        next_charge_datetime = datetime.datetime.utcfromtimestamp(next_charge_date)
        timedelta = dateutil.relativedelta.relativedelta(next_charge_datetime, datetime.datetime.now())
        months_till_charge = timedelta.years * 12 + timedelta.months
        if months_till_charge < 1:
            months_till_charge = 1
    else:
        months_till_charge = 1
    return months_till_charge, subscription_order


@returns()
@arguments(customer_id=(int, long), cancel_reason=unicode, immediately=bool)
def cancel_subscription(customer_id, cancel_reason, immediately=False):
    """
    Marks the customer his subscription as disabled.
    Recurrent billing will disable the service and disconnect all users after the subscription has ended.
    When the 'immediately' parameter is set, the service will be disabled immediately.

    Args:
        customer_id (int, long): Customer id
        cancel_reason (unicode): Reason why the subscription has been canceled.
        immediately (bool): Set to True to disable the service immediately

    Returns: None

    Raises:
        EmptyValueException
        CustomerNotFoundException
        NoSubscriptionException
    """
    if not cancel_reason:
        raise EmptyValueException('cancel_reason')

    customer = Customer.get_by_id(customer_id)

    if not customer.subscription_order_number:
        raise NoSubscriptionException(customer)

    if immediately:
        def trans():
            try:
                cancel_order(customer, customer.subscription_order_number)
            except OrderAlreadyCanceledException as exception:
                logging.info('Order %s already canceled, continueing...' % exception.order.order_number)

            customer.disabled_reason = cancel_reason
            set_service_disabled(customer, Customer.DISABLED_OTHER)

        run_in_xg_transaction(trans)
    else:
        customer.disabled_reason = cancel_reason
        customer.subscription_cancel_pending_date = now()
        customer.put()
