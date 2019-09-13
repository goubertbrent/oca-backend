# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
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
# @@license_version:1.5@@

import logging

from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from rogerthat.rpc.users import get_current_user
from shop.bizz import get_invoices
from shop.dal import get_customer
from shop.models import Order
from shop.to import OrderTO, InvoiceTO
from solutions.common.models.budget import Budget, BudgetTransaction


@rest("/common/billing/orders/load_unsigned", "get", read_only_access=True)
@returns([OrderTO])
@arguments()
def load_unsinged_orders():
    service_user = users.get_current_user()
    customer = get_customer(service_user)
    if not customer:
        logging.error("Customer not found for %s", service_user)
        return []
    return [OrderTO.fromOrderModel(order) for order in Order.list_unsigned(customer) if order.order_number != Order.CUSTOMER_STORE_ORDER_NUMBER]

@rest("/common/billing/orders/load", "get", read_only_access=True)
@returns([OrderTO])
@arguments()
def load_orders():
    service_user = users.get_current_user()
    customer = get_customer(service_user)
    if not customer:
        logging.error("Customer not found for %s", service_user)
        return []
    return [OrderTO.fromOrderModel(order) for order in Order.list_signed(customer)]

@rest("/common/billing/invoices/load", "get", read_only_access=True)
@returns([InvoiceTO])
@arguments()
def load_invoices():
    service_user = users.get_current_user()
    customer = get_customer(service_user)
    if not customer:
        logging.error("Customer not found for %s", service_user)
        return []
    return [InvoiceTO.fromInvoiceModel(invoice) for invoice in get_invoices(customer)]

@rest("/common/billing/order/sign", "post")
@returns(unicode)
@arguments(customer_id=(int, long), order_number=unicode, signature=unicode)
def sign_order(customer_id, order_number, signature):
    try:
        from shop.bizz import sign_order as bizz_sign_order
        bizz_sign_order(customer_id, order_number, signature)
        return None
    except BusinessException as be:
        return be.message


@rest('/common/billing/budget', 'get')
@returns(dict)
@arguments()
def api_get_budget():
    budget = Budget.create_key(get_current_user()).get()
    return budget.to_dict() if budget else {'balance': 0}


@rest('/common/billing/budget/transactions', 'get')
@returns([dict])
@arguments()
def api_list_budget_transactions():
    return [t.to_dict() for t in BudgetTransaction.list_by_user(get_current_user())]
