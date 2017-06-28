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

import base64
import datetime
from test import set_current_user

from dateutil import relativedelta

from google.appengine.ext import db
import mc_unittest
from rogerthat.bizz.profile import create_user_profile, UNKNOWN_AVATAR
from rogerthat.models import App
from rogerthat.rpc import users
from rogerthat.translations import DEFAULT_LANGUAGE
from rogerthat.utils import today, now
from rogerthat.utils.transactions import run_in_transaction
from shop.bizz import create_or_update_customer, create_contact, create_order, sign_order, put_service, \
    _after_service_saved, create_invoice
from shop.business.expired_subscription import set_expired_subscription_status
from shop.dal import get_mobicage_legal_entity
from shop.handlers import export_invoices
from shop.jobs import recurrentbilling
from shop.jobs.recurrentbilling import _create_charge
from shop.models import Product, ShopTask, ExpiredSubscription, RegioManagerTeam, Charge, Order, InvoiceNumber, Invoice
from shop.to import OrderItemTO, CustomerServiceTO
from solutions.common.bizz import OrganizationType, SolutionModule


class TestCase(mc_unittest.TestCase):

    def setUp(self, datastore_hr_probability=0):
        mc_unittest.TestCase.setUp(self, datastore_hr_probability=datastore_hr_probability)

        self.current_user = users.User('test@example.com')
        create_user_profile(self.current_user, u'test', DEFAULT_LANGUAGE)
        set_current_user(self.current_user)

    def _create_customer_and_subscription_order(self, products):
        customer = create_or_update_customer(self.current_user,
                                             customer_id=None,
                                             vat=u'BE4863 456 123',
                                             name=u'Test customer',
                                             address1=u'',
                                             address2=None,
                                             zip_code=u'9080',
                                             city=u'Lochristi',
                                             country=u'BE',
                                             language=DEFAULT_LANGUAGE,
                                             organization_type=OrganizationType.PROFIT,
                                             prospect_id=None,
                                             team_id=RegioManagerTeam.all().get().id)

        contact = create_contact(customer.id, u'Bart', u'example', u'bart@example.com', u'+32 9 324 25 64')
        items = self._create_items(customer, products)
        return self._create_order(customer, contact.id, items)

    def _create_items(self, customer, products):
        items = list()
        for x, product_info in enumerate(products):
            if isinstance(product_info, tuple):
                product_code, product_count = product_info
            else:
                product_code = product_info
                product_count = None

            product = Product.get_by_code(product_code)
            order_item = OrderItemTO()
            order_item.comment = product.default_comment(customer.language)
            order_item.count = product.default_count if product_count is None else product_count
            if product_code == u'MSUP' and product_count is None:
                order_item.count *= 2
            order_item.number = x
            order_item.product = product_code
            items.append(order_item)
        return items

    def _create_order(self, customer, contact_id, items, replace=False):
        order = create_order(customer.id, contact_id, items, replace=replace)
        sign_order(customer.id, order.order_number, 'image/png,%s' % base64.b64encode(UNKNOWN_AVATAR))
        return db.get((order.key(), customer.key()))


    def test_next_charge_date(self):
        self.set_datastore_hr_probability(1)

        order, _ = self._create_customer_and_subscription_order([u'MSUP', u'BEAC', u'KSUP', u'ILOS'])

        next_charge_dt = datetime.datetime.utcfromtimestamp(order.next_charge_date)
        self.assertGreater(next_charge_dt, datetime.datetime.utcfromtimestamp(today() + 2 * 363 * 86400))
        self.assertLess(next_charge_dt, datetime.datetime.utcfromtimestamp(today() + 2 * 366 * 86400))

        order_key = recurrentbilling._qry(order.next_charge_date + 86400).get()
        self.assertEqual(order.key(), order_key)

    def _create_service(self, customer, apps=None):
        service = CustomerServiceTO()
        service.address = u'antwerpsesteenweg 19 lochristi'
        service.apps = apps or [App.APP_ID_ROGERTHAT, u'be-loc']
        service.broadcast_types = [u'broadcast']
        service.currency = u'euro'
        service.email = u'test@example.com'
        service.language = u'en'
        mods = [m for m in SolutionModule.MANDATORY_MODULES]
        service.modules = list(set(mods))
        service.name = customer.name
        service.organization_type = OrganizationType.PROFIT
        service.phone_number = u'00248498498494'
        service.app_infos = []
        service.current_user_app_infos = []
        service.managed_organization_types = []
        provision_response = put_service(customer, service)
        # deferred functions seem to get ignored in unit tests..
        _after_service_saved(customer.key(), service.email, provision_response, True, service.apps, [])

    def test_recurrent_billing(self):
        self.set_datastore_hr_probability(1)
        products_to_order = [(u'MSUP', 12), (Product.PRODUCT_BEACON, 1)]
        subscription_order, customer = self._create_customer_and_subscription_order(products_to_order)
        self._create_service(customer)
        # Turn back next_charge_date more than 12 months
        subscription_order.next_charge_date -= 367 * 86400
        subscription_order.put()
        # execute recurrent billing code
        _create_charge(subscription_order.key(), now(), Product.get_products_dict())
        # check if a ShopTask was created
        task = ShopTask.all().get()
        self.assertEqual(task.type, ShopTask.TYPE_SUPPORT_NEEDED)
        task.delete()
        # Check if an expiredsubscription was created
        expired_subscription = ExpiredSubscription.get_by_customer_id(customer.id)
        self.assertIsNotNone(expired_subscription)

        # first set the expired subscription as 'customer will link his credit card'
        set_expired_subscription_status(customer.id, ExpiredSubscription.STATUS_WILL_LINK_CREDIT_CARD)
        task = ShopTask.all().get()
        self.assertIsNotNone(task)
        self.assertEqual(task.type, ShopTask.TYPE_CHECK_CREDIT_CARD)
        task.delete()

        # extend the customer's (expired) subscription
        charge = set_expired_subscription_status(customer.id, ExpiredSubscription.STATUS_EXTEND_SUBSCRIPTION)
        subscription_order, \
        expired_subscription = db.get((Order.create_key(customer.id, customer.subscription_order_number),
                                       ExpiredSubscription.create_key(customer.id)))
        self.assertEqual(expired_subscription, None)
        product_subscription = Product.get_by_code(u'MSUP')
        charge_total = product_subscription.price * 12  # subscription extensions should always be 12 months long
        self.assertIsNotNone(charge)
        self.assertEqual(Charge.TYPE_SUBSCRIPTION_EXTENSION, charge.type)
        self.assertEqual(charge_total, charge.amount)
        one_year_from_now_plus_one_day = datetime.datetime.utcfromtimestamp(now()) + relativedelta.relativedelta(
            months=12, days=1)
        one_year_from_now_minus_one_day = datetime.datetime.utcfromtimestamp(now()) + relativedelta.relativedelta(
            months=12, days=-1)
        self.assertLess(subscription_order.next_charge_date, int(one_year_from_now_plus_one_day.strftime('%s')))
        self.assertGreater(subscription_order.next_charge_date, int(one_year_from_now_minus_one_day.strftime('%s')))

    def test_change_order_to_free(self):
        self.set_datastore_hr_probability(1)
        products_to_order = [(u'MSUP', 1),  # monthly subscription, $50.00
                             (u'KFUP', 1),  # subscription discount, -$15.00
                             (Product.PRODUCT_EXTRA_CITY, 1),  # extra city, $5.00
                             (Product.PRODUCT_EXTRA_CITY, 1),  # extra city, $5.00
                             (Product.PRODUCT_EXTRA_CITY, 1)]  # extra city, $5.00
        old_subscription_order, customer = self._create_customer_and_subscription_order(products_to_order)
        old_subscription_order.next_charge_date -= 32 * 86400  # Turn back next_charge_date more than 1 month
        old_subscription_order.put()

        self._create_service(customer, [u'be-loc', u'be-berlare', u'be-beveren', u'es-madrid',
                                        App.APP_ID_ROGERTHAT, App.APP_ID_OSA_LOYALTY])

        products_to_order = [(Product.PRODUCT_FREE_SUBSCRIPTION, 1),
                             (Product.PRODUCT_EXTRA_CITY, 1),  # extra city, $5.00
                             (Product.PRODUCT_EXTRA_CITY, 1),  # extra city, $5.00
                             (Product.PRODUCT_EXTRA_CITY, 1)]  # extra city, $5.00
        order_items = self._create_items(customer, products_to_order)
        new_subscription_order, customer = self._create_order(customer, old_subscription_order.contact_id, order_items,
                                                              replace=True)
        new_subscription_order.next_charge_date -= 32 * 86400  # Turn back next_charge_date more than 1 month
        new_subscription_order.put()

        # Execute recurrent billing code
        products = Product.get_products_dict()
        charge = _create_charge(new_subscription_order.key(), now(), products)
        self.assertIsNotNone(charge)
        expected_charge_amount = 3 * products[Product.PRODUCT_EXTRA_CITY].price  # 3x $5.00
        self.assertEqual(expected_charge_amount, charge.amount)

        def trans_invoice_number():
            return InvoiceNumber.next(get_mobicage_legal_entity())

        invoice_number = run_in_transaction(trans_invoice_number)
        create_invoice(customer.id, new_subscription_order.order_number, charge.id, invoice_number,
                       new_subscription_order.manager, payment_type=Invoice.PAYMENT_ON_SITE)

        dt = datetime.datetime.utcnow()
        invoices = export_invoices(dt.year, dt.month)
        self.assertEqual(1, len(invoices))
        self.assertEqual(len(products_to_order), len(invoices[0]['order_items']))

        order_items_cost = sum(order_item['price'] * order_item['count']
                               for order_item in invoices[0]['order_items'])
        self.assertEqual(expected_charge_amount, order_items_cost)
