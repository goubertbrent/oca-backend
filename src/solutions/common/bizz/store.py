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
import binascii
import logging
from StringIO import StringIO
from base64 import b64encode
from contextlib import closing
from hashlib import sha256

from google.appengine.ext import db
from google.appengine.ext.deferred import deferred

from mcfw.properties import azzert
from rogerthat.bizz.payment.providers.payconiq.api import _verify_sign
from rogerthat.consts import FAST_QUEUE
from rogerthat.dal.app import get_app_by_id
from rogerthat.models.utils import copy_model_properties, allocate_id
from rogerthat.rpc import users
from rogerthat.settings import get_server_settings
from rogerthat.utils import now, channel, today
from rogerthat.utils.transactions import run_in_xg_transaction
from shop.bizz import update_regiomanager_statistic, get_payed, generate_order_or_invoice_pdf, send_order_email, \
    create_task, broadcast_task_updates, create_invoice
from shop.business.prospect import create_prospect_from_customer
from shop.constants import STORE_MANAGER
from shop.dal import get_customer
from shop.models import Order, OrderItem, Product, Charge, OrderNumber, RegioManagerTeam, Customer, Prospect, ShopTask, \
    InvoiceNumber, Invoice
from shop.to import BoolReturnStatusTO
from solution_server_settings import get_solution_server_settings
from solutions import translate, SOLUTION_COMMON
from solutions.common.bizz.budget import update_budget
from solutions.common.dal import get_solution_settings
from solutions.common.models.payment import FINAL_STATUSES
from solutions.common.models.payment import PayconiqPayment, PayconiqPaymentStatus


def generate_payconiq_signature(merchant_id, currency, amount, secret_key, webhook_id):
    # type: (str, str, str, str, str) -> str
    shasum = sha256()
    signature = '{merchant_id}{webhook_id}{currency}{amount}{secret_key}'.format(merchant_id=merchant_id,
                                                                                 webhook_id=webhook_id,
                                                                                 currency=currency,
                                                                                 amount=amount,
                                                                                 secret_key=secret_key)
    shasum.update(signature.encode('utf-8'))
    signature_encoded = b64encode(shasum.digest())
    return signature_encoded


def get_payconiq_info(service_user):
    customer = get_customer(service_user)
    settings = get_solution_server_settings()
    order = db.get(Order.create_key(customer.id, Order.CUSTOMER_STORE_ORDER_NUMBER))  # type: Order
    currency = 'EUR'
    payment = PayconiqPayment(service_user=service_user.email(),
                              currency=currency,
                              amount=order.total_amount,
                              precision=2,
                              status=PayconiqPaymentStatus.INITIAL)
    payment.put()
    amount_str = str(order.total_amount)
    return {
        'webhookId': str(payment.id),
        'signature': generate_payconiq_signature(settings.payconiq_merchant_id, currency, amount_str,
                                                 settings.payconiq_secret, payment.id),
        'merchantId': settings.payconiq_merchant_id,
        'amount': amount_str,
        'currency': currency,
        'returnUrl': get_server_settings().baseUrl + '/payments/payconiq/callback'
    }


def verify_payconiq_signature(public_key, merchant_id, timestamp, body, signature):
    # From https://github.com/payconiq/merchant-callback-verification-python
    crc32 = '{:8x}'.format(binascii.crc32(body.encode('utf-8')) & 0xffffffff)
    expected_sig = '{}|{}|{}'.format(merchant_id, timestamp, crc32).encode('utf-8')
    return _verify_sign(public_key, signature, expected_sig)


def handle_payconiq_callback(webhook_id, transaction_id, status):
    payment = PayconiqPayment.create_key(webhook_id).get()  # type: PayconiqPayment
    payment.transaction_id = transaction_id
    if payment.status not in FINAL_STATUSES:
        logging.info('Updating status from %s to %s', payment.status, status)
        payment.status = status
    else:
        logging.warning('Not updating transaction %s status to %s: status is already %s', webhook_id, status,
                        payment.status)
        return
    if payment.status == PayconiqPaymentStatus.SUCCEEDED:
        process_order(False)


def process_order(charge_creditcard):
    # type: (bool) -> BoolReturnStatusTO
    service_user = users.get_current_user()
    language = get_solution_settings(service_user).main_language
    customer = get_customer(service_user)
    azzert(customer)

    app = get_app_by_id(customer.app_id)
    is_demo = app and app.demo
    if not is_demo and not customer.stripe_valid:
        return BoolReturnStatusTO.create(False,
                                         translate(language, SOLUTION_COMMON, u'link_cc_now'),
                                         True)

    # create a new order with the exact same order items.
    old_order_key = Order.create_key(customer.id, Order.CUSTOMER_STORE_ORDER_NUMBER)

    charge_id_cache = []

    CREATE_SHOPTASK_FOR_ITEMS = [Product.PRODUCT_ROLLUP_BANNER, Product.PRODUCT_CARDS]

    def trans():
        old_order, team = db.get((old_order_key, RegioManagerTeam.create_key(customer.team_id)))

        if not old_order:
            return BoolReturnStatusTO.create(False, translate(language, SOLUTION_COMMON, u'cart_empty'), False)

        # Duplicate the order
        to_put = []
        to_delete = []
        properties = copy_model_properties(old_order)
        properties['status'] = Order.STATUS_SIGNED
        properties['date_signed'] = now()
        properties['date'] = now()
        new_order_key = Order.create_key(customer.id, OrderNumber.next(team.legal_entity_key))
        new_order = Order(key=new_order_key, **properties)
        new_order.team_id = team.id
        to_delete.append(old_order)

        # duplicate all of the order items
        old_order_items = OrderItem.list_by_order(old_order_key)  # type: list[OrderItem]
        all_products = {product.code: product for product in db.get([Product.create_key(item.product_code)
                                                                     for item in old_order_items])}
        is_subscription_extension_order = False
        for product in all_products.itervalues():
            if product.is_subscription_extension:
                is_subscription_extension_order = True
                break
        new_order.is_subscription_extension_order = is_subscription_extension_order
        if is_subscription_extension_order:
            subscription_order = Order.get_by_order_number(customer.id, customer.subscription_order_number)
            new_order.next_charge_date = subscription_order.next_charge_date
        should_create_shoptask = False
        added_budget = 0
        budget_description = None
        for old_item in old_order_items:
            properties = copy_model_properties(old_item)
            new_item = OrderItem(parent=new_order_key, **properties)
            to_put.append(new_item)
            to_delete.append(old_item)
            if old_item.clean_product_code in CREATE_SHOPTASK_FOR_ITEMS:
                should_create_shoptask = True
            if old_item.clean_product_code == Product.PRODUCT_BUDGET:
                budget_description = all_products[old_item.product_code].description(language)
                added_budget += all_products[old_item.product_code].price * old_item.count
        if added_budget:
            deferred.defer(update_budget, service_user, added_budget, service_identity=None, context_type=None,
                           context_key=None, memo=budget_description, _transactional=True)
        to_put.append(new_order)
        db.put(to_put)
        db.delete(to_delete)

        deferred.defer(generate_and_put_order_pdf_and_send_mail, customer, new_order_key, service_user,
                       _transactional=True)

        # No need for signing here, immediately create a charge.
        azzert(new_order.total_amount > 0)
        if not is_demo:
            # Ensure same charge id is used when transaction is retried, else the customer might be charged twice
            if not charge_id_cache:
                charge_id_cache.append(allocate_id(Charge, parent=new_order_key))
            charge = Charge(key=Charge.create_key(charge_id_cache[0], new_order_key.name(), customer.id))
            charge.date = now()
            charge.type = Charge.TYPE_ORDER_DELIVERY
            charge.amount = new_order.amount
            charge.vat_pct = new_order.vat_pct
            charge.vat = new_order.vat
            charge.total_amount = new_order.total_amount
            charge.manager = new_order.manager
            charge.team_id = new_order.team_id
            if charge_creditcard:
                charge.status = Charge.STATUS_PENDING
            else:
                charge.status = Charge.STATUS_EXECUTED
            charge.date_executed = now()
            charge.currency_code = team.legal_entity.currency_code
            charge.put()

        # Update the regiomanager statistics so these kind of orders show up in the monthly statistics
        deferred.defer(update_regiomanager_statistic, gained_value=new_order.amount / 100,
                       manager=new_order.manager, _transactional=True)
        if charge_creditcard:
            if not is_demo:
                # charge the credit card
                get_payed(customer.id, new_order, charge)
        else:
            invoice_number = InvoiceNumber.next(customer.team.legal_entity_key)
            deferred.defer(create_invoice, customer.id, new_order_key.name(), charge_id_cache[0], invoice_number,
                           new_order.manager, Invoice.PAYMENT_PAYCONIQ, _transactional=True, _queue=FAST_QUEUE)

        channel.send_message(service_user, 'common.billing.orders.update')
        if should_create_shoptask:
            deferred.defer(create_task_for_order, customer.id, new_order.order_number, _countdown=5,
                           _transactional=True)
        return BoolReturnStatusTO.create(True, None)

    xg_on = db.create_transaction_options(xg=True)
    return db.run_in_transaction_options(xg_on, trans)


def generate_and_put_order_pdf_and_send_mail(customer, new_order_key, service_user):
    def trans():
        new_order = Order.get(new_order_key)
        with closing(StringIO()) as pdf:
            generate_order_or_invoice_pdf(pdf, customer, new_order)
            new_order.pdf = pdf.getvalue()

        new_order.put()
        deferred.defer(send_order_email, new_order_key, service_user, _transactional=True)

    run_in_xg_transaction(trans)


def create_task_for_order(customer_id, order_number):
    customer = Customer.get_by_id(customer_id)
    prospect_id = customer.prospect_id
    if prospect_id is None:
        prospect = create_prospect_from_customer(customer)
        prospect_id = prospect.id
    team, prospect = db.get(
        [RegioManagerTeam.create_key(customer.team_id), Prospect.create_key(prospect_id)])
    azzert(team.support_manager, u'No support manager found for team %s' % team.name)
    comment = u'Customer placed a new order: %s' % order_number
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
