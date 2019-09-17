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

from contextlib import closing
import logging

from google.appengine.ext import db
from google.appengine.ext.deferred import deferred

from mcfw.properties import azzert
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from rogerthat.settings import get_server_settings
from rogerthat.to import RETURNSTATUS_TO_SUCCESS, ReturnStatusTO
from rogerthat.translations import DEFAULT_LANGUAGE
from rogerthat.utils import now, today
from rogerthat.utils.transactions import run_in_xg_transaction
from shop.bizz import send_order_email, generate_order_or_invoice_pdf, create_task, broadcast_task_updates
from shop.business.legal_entities import get_vat_pct
from shop.business.prospect import create_prospect_from_customer
from shop.constants import STORE_MANAGER
from shop.dal import get_customer
from shop.models import Order, OrderItem, Product, ShopTask, Prospect, Customer, \
    RegioManagerTeam, Contact, StripePayment, StripePaymentItem
from shop.to import OrderItemTO, ProductTO, ShopProductTO, OrderItemReturnStatusTO
from solution_server_settings import get_solution_server_settings
from solutions import translate, SOLUTION_COMMON
from solutions.common.bizz import SolutionModule
from solutions.common.dal import get_solution_settings

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


@rest("/common/store/order_items", "get", read_only_access=True)
@returns([OrderItemTO])
@arguments()
def get_order_items():
    # get the order items for this customer from the latest order that isn't signed yet
    service_user = users.get_current_user()
    customer = get_customer(service_user)
    if not customer:
        return []
    order_key = Order.create_key(customer.id, Order.CUSTOMER_STORE_ORDER_NUMBER)
    order = Order.get(order_key)
    if order:
        return [OrderItemTO.create(i) for i in OrderItem.list_by_order(order_key)]
    else:
        return []


@rest("/common/store/products", "get", read_only_access=True)
@returns([ProductTO])
@arguments()
def get_products():
    service_user = users.get_current_user()
    sln_settings = get_solution_settings(service_user)
    keys = [Product.create_key(Product.PRODUCT_BUDGET)]
    if SolutionModule.CITY_APP in sln_settings.modules:
        keys.append(Product.create_key(Product.PRODUCT_ROLLUP_BANNER))
    return [ProductTO.create(p, sln_settings.main_language) for p in Product.get(keys)]


@rest("/common/store/order/item/delete", "post", read_only_access=False)
@returns(ReturnStatusTO)
@arguments(item_id=(int, long))
def remove_from_order(item_id):
    service_user = users.get_current_user()
    customer = get_customer(service_user)
    azzert(customer)
    customer_store_order_key = Order.create_key(customer.id, Order.CUSTOMER_STORE_ORDER_NUMBER)
    order_item_key = OrderItem.create_key(customer.id, Order.CUSTOMER_STORE_ORDER_NUMBER, item_id)
    order_item, order = db.get([order_item_key, customer_store_order_key])

    if not order_item:
        logging.warn("Customer %s tried to delete an already deleted item (%s)", service_user.email(), item_id)
        return RETURNSTATUS_TO_SUCCESS
    azzert(order)

    # Subtract the price from this product, then remove the product.
    vat = order_item.count * order_item.price * order.vat_pct / 100
    total = order_item.count * order_item.price
    total_inc_vat = total + vat
    order.amount -= total
    order.total_amount -= total_inc_vat
    order.vat -= vat
    order_item.delete()
    order.put()
    return RETURNSTATUS_TO_SUCCESS


@rest("/common/store/order/item/add", "post", read_only_access=False)
@returns(OrderItemReturnStatusTO)
@arguments(item=ShopProductTO)
def add_item_to_order(item):
    service_user = users.get_current_user()
    customer = get_customer(service_user)
    azzert(customer)
    contact = Contact.get_one(customer)
    azzert(contact)

    def trans():
        to_put = []
        customer_store_order_key = Order.create_key(customer.id, Order.CUSTOMER_STORE_ORDER_NUMBER)
        team_key = RegioManagerTeam.create_key(customer.team_id)
        product_key = Product.create_key(item.code)

        product, customer_store_order, team = db.get([product_key, customer_store_order_key, team_key])

        # Check if the item has a correct count.
        # Should never happen unless the user manually recreates the ajax request..
        azzert(
            not product.possible_counts or item.count in product.possible_counts, u'Invalid amount of items supplied')
        number = 0
        existing_order_items = []
        vat_pct = get_vat_pct(customer, team)
        item_already_added = False
        if not customer_store_order:
            # create new order
            customer_store_order = Order(key=customer_store_order_key)
            customer_store_order.contact_id = contact.key().id()
            customer_store_order.date = now()
            customer_store_order.vat_pct = 0
            customer_store_order.amount = 0
            customer_store_order.vat = 0
            customer_store_order.vat_pct = vat_pct
            customer_store_order.total_amount = 0
            customer_store_order.is_subscription_order = False
            customer_store_order.manager = STORE_MANAGER
            customer_store_order.team_id = None
        else:
            order_items = OrderItem.list_by_order(customer_store_order.key())
            for i in order_items:
                number = i.number if i.number > number else number
                existing_order_items.append(i)
                # Check if there already is an orderitem with the same product code.
                # If so, add the count of this new item to the existing item.
                for it in order_items:
                    if it.product_code == item.code and it.product_code != Product.PRODUCT_NEWS_PROMOTION:
                        if (it.count + item.count) in product.possible_counts or not product.possible_counts:
                            it.count += item.count
                            item_already_added = True
                            to_put.append(it)
                            order_item = it
                        elif len(product.possible_counts) != 0:
                            raise BusinessException(
                                translate(customer.language, SOLUTION_COMMON, u'cant_order_more_than_specified',
                                          allowed_items=max(product.possible_counts)))
        total = product.price * item.count
        vat = total * vat_pct / 100
        total_price = total + vat
        customer_store_order.amount += total
        customer_store_order.vat += vat
        azzert(customer_store_order.total_amount >= 0)
        customer_store_order.total_amount += total_price
        if not item_already_added:
            order_item = OrderItem(parent=customer_store_order.key())
            order_item.number = number
            order_item.comment = product.default_comment(customer.language)
            order_item.product_code = product.code
            order_item.count = item.count
            order_item.price = product.price
            to_put.append(order_item)
        to_put.append(customer_store_order)
        db.put(to_put)
        return order_item

    try:
        new_item = run_in_xg_transaction(trans)
        return OrderItemReturnStatusTO.create(True, None, new_item)
    except BusinessException as exception:
        return OrderItemReturnStatusTO.create(False, exception.message, None)


@rest("/common/store/order/pay/url", "get", read_only_access=False)
@returns(unicode)
@arguments()
def get_pay_order_url():
    import stripe

    service_user = users.get_current_user()
    sln_settings = get_solution_settings(service_user)
    if not sln_settings:
        return None
    customer = get_customer(service_user)
    if not customer:
        return None
    order_key = Order.create_key(customer.id, Order.CUSTOMER_STORE_ORDER_NUMBER)
    order = Order.get(order_key)
    if not order:
        return None
    team = RegioManagerTeam.get(RegioManagerTeam.create_key(customer.team_id))
    if not team:
        return None

    items = []
    product_keys = []
    product_dict = {}
    for i in OrderItem.list_by_order(order_key):
        items.append(StripePaymentItem(product_code=i.product_code,
                                       count=i.count))
        product_dict[i.product_code] = i.count
        product_keys.append(Product.create_key(i.product_code))

    if not items:
        return None

    vat_pct = get_vat_pct(customer, team)
    language = sln_settings.main_language or DEFAULT_LANGUAGE

    line_items = []
    for p in Product.get(product_keys):
        name = p.description(language)
        total = p.price
        vat = total * vat_pct / 100

        line_items.append({
            'name': name,
            'amount': total + vat,
            'currency': u'eur',
            'quantity': product_dict[p.code],
        })

    solution_server_settings = get_solution_server_settings()
    stripe.api_key = solution_server_settings.stripe_secret_key

    base_url = get_server_settings().baseUrl

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=line_items,
        success_url='%s/unauthenticated/payments/stripe/success' % base_url,
        cancel_url='%s/unauthenticated/payments/stripe/cancel' % base_url,
    )

    session_id = session['id']

    payment = StripePayment(key=StripePayment.create_key(session_id),
                            items=items)
    payment.service_user = service_user
    payment.status = StripePayment.STATUS_CREATED
    payment.put()

    return '%s/unauthenticated/payments/stripe?session_id=%s' % (get_server_settings().baseUrl, session_id)
