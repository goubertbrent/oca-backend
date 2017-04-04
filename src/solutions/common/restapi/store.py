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
# @@license_version:1.3@@

import datetime
import logging

from babel.dates import format_date
from google.appengine.ext import db
from google.appengine.ext.deferred import deferred

from mcfw.consts import MISSING
from mcfw.properties import azzert
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.bizz.service import re_index
from rogerthat.consts import MC_DASHBOARD
from rogerthat.dal.service import get_default_service_identity
from rogerthat.models import App
from rogerthat.models.utils import copy_model_properties
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from rogerthat.settings import get_server_settings
from rogerthat.to import RETURNSTATUS_TO_SUCCESS, ReturnStatusTO
from rogerthat.utils import now, channel, today, format_price
from rogerthat.utils.transactions import run_in_xg_transaction
from shop.bizz import send_order_email, update_regiomanager_statistic, generate_order_or_invoice_pdf, create_task, \
    get_payed, broadcast_task_updates
from shop.business.legal_entities import get_vat_pct
from shop.business.order import get_subscription_order_remaining_length
from shop.business.prospect import create_prospect_from_customer
from shop.constants import STORE_MANAGER
from shop.dal import get_customer
from shop.models import Order, OrderItem, Product, Charge, OrderNumber, ShopTask, Prospect, Customer, \
    RegioManagerTeam, Contact
from shop.to import OrderItemTO, ProductTO, ShopProductTO, OrderItemReturnStatusTO, BoolReturnStatusTO
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
        sln_settings = get_solution_settings(service_user)
        lang = sln_settings.main_language
        remaining_length, sub_order = get_subscription_order_remaining_length(customer.id,
                                                                              customer.subscription_order_number)
        subscription_order_charge_date = format_date(datetime.datetime.utcfromtimestamp(sub_order.next_charge_date),
                                                     locale=lang)
        order_items = list(OrderItem.list_by_order(order_key))
        order_items_updated = list()
        to_put = list()
        to_get = list(set([Product.create_key(o.product_code) for o in order_items] + [
            Product.create_key(Product.PRODUCT_EXTRA_CITY)]))
        products = {p.code: p for p in db.get(to_get)}
        # update the order items if necessary.
        for order_item in order_items:
            if products[order_item.product_code].is_subscription_extension and order_item.count != remaining_length:
                order_item.count = remaining_length
                to_put.append(order_item)
            order_items_updated.append(order_item)
        if to_put:
            db.put(to_put)
        extra_city_price = format_price(products[Product.PRODUCT_EXTRA_CITY].price, sln_settings.currency)
        service_visible_in_translation = translate(lang, SOLUTION_COMMON, 'service_visible_in_app',
                                                   subscription_expiration_date=subscription_order_charge_date,
                                                   amount_of_months=remaining_length, extra_city_price=extra_city_price,
                                                   app_name='%(app_name)s')
        return [OrderItemTO.create(i, service_visible_in_translation) for i in order_items_updated]
    else:
        return []


@rest("/common/store/products", "get", read_only_access=True)
@returns([ProductTO])
@arguments()
def get_products():
    service_user = users.get_current_user()
    sln_settings = get_solution_settings(service_user)
    keys = [Product.create_key('BEAC'),
            Product.create_key('POSM'),
            Product.create_key(Product.PRODUCT_CARDS)]
    if SolutionModule.CITY_APP not in sln_settings.modules:  # city apps cannot order more city apps
        keys.append(Product.create_key(Product.PRODUCT_EXTRA_CITY))
    else:
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
    sln_settings = get_solution_settings(service_user)
    lang = sln_settings.main_language

    # Check if the customer his service isn't already enabled in this city
    if item.app_id in customer.app_ids:
        raise BusinessException(translate(lang, SOLUTION_COMMON, u'service_already_active'))

    def trans():
        to_put = list()
        customer_store_order_key = Order.create_key(customer.id, Order.CUSTOMER_STORE_ORDER_NUMBER)
        subscription_order_key = Order.create_key(customer.id, customer.subscription_order_number)
        team_key = RegioManagerTeam.create_key(customer.team_id)
        product_key = Product.create_key(item.code)

        if item.app_id is not MISSING:
            app_key = App.create_key(item.app_id)
            product, customer_store_order, sub_order, app, team = db.get(
                [product_key, customer_store_order_key, subscription_order_key, app_key, team_key])
            if sub_order.status != Order.STATUS_SIGNED:
                raise BusinessException(translate(lang, SOLUTION_COMMON, u'no_unsigned_order'))
            # check if the provided app does exist
            azzert(app)
        else:
            product, customer_store_order, team = db.get([product_key, customer_store_order_key, team_key])

        # Check if the item has a correct count.
        # Should never happen unless the user manually recreates the ajax request..
        azzert(
            not product.possible_counts or item.count in product.possible_counts or item.code == Product.PRODUCT_EXTRA_CITY,
               u'Invalid amount of items supplied')
        number = 0
        existing_order_items = list()
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
                # Check if this city isn't already in the possible pending order.
                if hasattr(i, 'app_id') and (i.app_id == item.app_id or item.app_id in customer.app_ids):
                    raise BusinessException(translate(lang, SOLUTION_COMMON, u'item_already_added'))
                else:
                    # Check if there already is an orderitem with the same product code.
                    # If so, add the count of this new item to the existing item.
                    for it in order_items:
                        if it.product_code == item.code and it.product_code not in (
                        Product.PRODUCT_EXTRA_CITY, Product.PRODUCT_NEWS_PROMOTION):
                            if (it.count + item.count) in product.possible_counts or not product.possible_counts:
                                it.count += item.count
                                item_already_added = True
                                to_put.append(it)
                                order_item = it
                            elif len(product.possible_counts) != 0:
                                raise BusinessException(
                                        translate(lang, SOLUTION_COMMON, u'cant_order_more_than_specified',
                                                  allowed_items=max(product.possible_counts)))

        if item.app_id is not MISSING:
            remaining_length, _ = get_subscription_order_remaining_length(customer.id,
                                                                          customer.subscription_order_number)
            subscription_order_charge_date = format_date(datetime.datetime.utcfromtimestamp(sub_order.next_charge_date),
                                                         locale=lang)
            total = remaining_length * product.price
        else:
            total = product.price * item.count
        vat = total * vat_pct / 100
        total_price = total + vat
        customer_store_order.amount += total
        customer_store_order.vat += vat
        azzert(customer_store_order.total_amount >= 0)
        customer_store_order.total_amount += total_price
        service_visible_in_translation = None
        if not item_already_added:
            order_item = OrderItem(parent=customer_store_order.key())
            order_item.number = number
            order_item.comment = product.default_comment(customer.language)
            order_item.product_code = product.code
            if item.app_id is not MISSING:
                order_item.count = remaining_length
                service_visible_in_translation = translate(lang, SOLUTION_COMMON, 'service_visible_in_app',
                                                           subscription_expiration_date=subscription_order_charge_date,
                                                           amount_of_months=remaining_length,
                                                           extra_city_price=product.price_in_euro,
                                                           app_name=app.name)
            else:
                order_item.count = item.count
            order_item.price = product.price

            if item.app_id is not MISSING:
                order_item.app_id = item.app_id
            to_put.append(order_item)
        to_put.append(customer_store_order)
        db.put(to_put)
        return order_item, service_visible_in_translation

    try:
        order_item, service_visible_in_translation = run_in_xg_transaction(trans)
        return OrderItemReturnStatusTO.create(True, None, order_item, service_visible_in_translation)
    except BusinessException, exception:
        return OrderItemReturnStatusTO.create(False, exception.message, None)

@rest("/common/store/order/pay", "post", read_only_access=False)
@returns(BoolReturnStatusTO)
@arguments()
def pay_order():
    service_user = users.get_current_user()
    customer = get_customer(service_user)
    azzert(customer)

    if not customer.stripe_valid:
        # Create a shoptask after 1 hour
        deferred.defer(create_task_if_not_order, customer.id, _countdown=3600)
        return BoolReturnStatusTO.create(False,
                                         translate(get_solution_settings(service_user).main_language,
                                                   SOLUTION_COMMON,
                                                   u'no_credit_card_contact_support'),
                                         True)

    # create a new order with the exact same order items.
    old_order_key = Order.create_key(customer.id, Order.CUSTOMER_STORE_ORDER_NUMBER)

    def trans():
        old_order, team = db.get((old_order_key, RegioManagerTeam.create_key(customer.team_id)))

        if not old_order:
            return BoolReturnStatusTO.create(False,
                                             translate(get_solution_settings(service_user).main_language,
                                                       SOLUTION_COMMON,
                                                       u'cart_empty'),
                                             False)

        # Duplicate the order
        to_put = list()
        to_delete = list()
        properties = copy_model_properties(old_order)
        properties['status'] = Order.STATUS_SIGNED
        properties['date_signed'] = now()
        new_order_key = Order.create_key(customer.id, OrderNumber.next(team.legal_entity_key))
        new_order = Order(key=new_order_key, **properties)
        new_order.team_id = team.id
        to_delete.append(old_order)

        # duplicate all of the order items
        old_order_items = OrderItem.list_by_order(old_order_key)
        all_products = db.get([Product.create_key(item.product_code) for item in old_order_items])
        is_subscription_extension_order = False
        for product in all_products:
            if product.is_subscription_extension:
                is_subscription_extension_order = True
                break
        new_order.is_subscription_extension_order = is_subscription_extension_order
        if is_subscription_extension_order:
            subscription_order = Order.get_by_order_number(customer.id, customer.subscription_order_number)
            new_order.next_charge_date = subscription_order.next_charge_date
        added_apps = list()
        should_create_shoptask = False
        for old_item in old_order_items:
            properties = copy_model_properties(old_item)
            new_item = OrderItem(parent=new_order_key, **properties)
            to_put.append(new_item)
            to_delete.append(old_item)
            if hasattr(old_item, 'app_id'):
                added_apps.append(old_item.app_id)
            else:
                should_create_shoptask = True
        to_put.append(new_order)
        db.put(to_put)
        db.delete(to_delete)

        deferred.defer(generate_and_put_order_pdf_and_send_mail, customer, new_order_key, service_user,
                       _transactional=True)

        # No need for signing here, immediately create a charge.
        azzert(new_order.total_amount > 0)
        charge = Charge(parent=new_order_key)
        charge.date = now()
        charge.type = Charge.TYPE_ORDER_DELIVERY
        charge.amount = new_order.amount
        charge.vat_pct = new_order.vat_pct
        charge.vat = new_order.vat
        charge.total_amount = new_order.total_amount
        charge.manager = new_order.manager
        charge.team_id = new_order.team_id
        charge.status = Charge.STATUS_PENDING
        charge.date_executed = now()
        charge.currency_code = team.legal_entity.currency_code
        charge.put()

        # Update the regiomanager statistics so these kind of orders show up in the monthly statistics
        deferred.defer(update_regiomanager_statistic, gained_value=new_order.amount / 100,
                       manager=new_order.manager, _transactional=True)

        # Update the customer service
        si = get_default_service_identity(users.User(customer.service_email))
        si.appIds.extend(added_apps)
        si.put()
        deferred.defer(re_index, si.user, _transactional=True)

        # Update the customer object so the newly added apps are added.
        customer.app_ids.extend(added_apps)
        customer.extra_apps_count += len(added_apps)
        customer.put()

        get_payed(customer.id, new_order, charge)
        # charge the credit card
        channel.send_message(service_user, 'common.billing.orders.update')
        channel_data = {
            'customer': customer.name,
            'no_manager': True,
            'amount': charge.amount / 100,
            'currency': charge.currency
        }
        server_settings = get_server_settings()
        send_to = server_settings.supportWorkers
        send_to.append(MC_DASHBOARD.email())
        channel.send_message(map(users.User, send_to), 'shop.monitoring.signed_order',
                             info=channel_data)
        if should_create_shoptask:
            prospect_id = customer.prospect_id
            if prospect_id is None:
                prospect = create_prospect_from_customer(customer)
                prospect_id = prospect.id
            deferred.defer(create_task_for_order, customer.team_id, prospect_id, new_order.order_number,
                           _transactional=True)
        return BoolReturnStatusTO.create(True, None)

    xg_on = db.create_transaction_options(xg=True)
    return db.run_in_transaction_options(xg_on, trans)


def generate_and_put_order_pdf_and_send_mail(customer, new_order_key, service_user):
    def trans():
        new_order = Order.get(new_order_key)
        pdf = StringIO()
        generate_order_or_invoice_pdf(pdf, customer, new_order)
        new_order.pdf = pdf.getvalue()
        pdf.close()
        new_order.put()
        deferred.defer(send_order_email, new_order_key, service_user, _transactional=True)
    run_in_xg_transaction(trans)


def create_task_for_order(customer_team_id, prospect_id, order_number):
    team, prospect = db.get(
        [RegioManagerTeam.create_key(customer_team_id), Prospect.create_key(prospect_id)])
    azzert(team.support_manager, u'No support manager found for team %s' % team.name)
    comment = u'Customer placed a new order: %s' % (order_number)
    task = create_task(
        created_by=STORE_MANAGER.email(),
        prospect_or_key=prospect,
        app_id=prospect.app_id,
        status=ShopTask.STATUS_NEW,
        task_type=ShopTask.TYPE_SUPPORT_NEEDED,
        address=None,
        assignee=team.support_manager,
        comment=comment,
        execution_time=today() + 86400 + 11 * 3600,  # tomorrow at 11:00
        notify_by_email=True
    )
    task.put()
    broadcast_task_updates([team.support_manager])

def create_task_if_not_order(customer_id):
    customer = Customer.get_by_id(customer_id)
    # Check if the customer has linked his credit card after he clicked the 'pay' button
    # If he didn't (one hour after the last time he tried to pay), create a new ShopTask to call this customer.
    if not customer.stripe_valid and customer.team_id:
        if customer.prospect_id:
            rmt, prospect = db.get(
                [RegioManagerTeam.create_key(customer.team_id), Prospect.create_key(customer.prospect_id)])
        else:
            prospect = create_prospect_from_customer(customer)
            rmt = RegioManagerTeam.get(RegioManagerTeam.create_key(customer.team_id))
        azzert(rmt.support_manager, 'No support manager found for team %s' % rmt.name)
        task = create_task(prospect_or_key=prospect,
                           status=ShopTask.STATUS_NEW,
                           task_type=ShopTask.TYPE_SUPPORT_NEEDED,
                           address=None,
                           created_by=STORE_MANAGER.email(),
                           assignee=rmt.support_manager,
                           execution_time=today() + 86400 + 11 * 3600,  # tomorrow, 11:00,
                           app_id=prospect.app_id,
                           comment=u"Customer wanted to pay an order in the customer store, "
                           "but didn't succeed because he did not link his creditcard.",
                           notify_by_email=True)
        task.put()
