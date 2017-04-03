# -*- coding: utf-8 -*-
# Copyright 2017 GIG Technology NV
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

import base64

from google.appengine.ext import db

import mc_unittest
from rogerthat.bizz.profile import create_user_profile, UNKNOWN_AVATAR
from rogerthat.models import App
from rogerthat.rpc import users
from rogerthat.translations import DEFAULT_LANGUAGE
from mcfw.consts import MISSING
from shop.bizz import put_service, _after_service_saved, create_or_update_customer, create_contact, create_order, \
    sign_order
from shop.business.order import get_subscription_order_remaining_length
from shop.models import RegioManagerTeam, Product, Customer, Order
from shop.to import ShopProductTO, CustomerServiceTO, OrderItemTO
from solutions.common.bizz import OrganizationType
from solutions.common.bizz import SolutionModule
from solutions.common.restapi.store import add_item_to_order, remove_from_order, pay_order
from test import set_current_user


class CustomerStoreTestCase(mc_unittest.TestCase):
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

        order = create_order(customer.id, contact.id, items)
        sign_order(customer.id, order.order_number, 'image/png,%s' % base64.b64encode(UNKNOWN_AVATAR))
        return db.get((order.key(), customer.key()))

    def _create_service(self, customer):
        service = CustomerServiceTO()
        service.address = u'antwerpsesteenweg 19 lochristi'
        service.apps = [App.APP_ID_ROGERTHAT, u'be-loc']
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

    def test_customer_store(self):
        xcty_product = ShopProductTO.create(u'be-berlare', u'XCTY', 1)
        posm_product = ShopProductTO.create(MISSING, u'POSM', 250)
        _, customer = self._create_customer_and_subscription_order(
            [u'MSUP', u'BEAC', u'KSUP', u'ILOS'])
        self._create_service(customer)
        customer = Customer.get_by_id(customer.id)
        self.current_user = users.User(customer.service_email)
        set_current_user(self.current_user)
        product_xcty, product_posm = db.get([Product.create_key(u'XCTY'), Product.create_key(u'POSM')])

        xcty_order_item = add_item_to_order(xcty_product).order_item
        remaining_subscription_length = get_subscription_order_remaining_length(customer.id,
                                                                                customer.subscription_order_number)[0]
        price_xcty = remaining_subscription_length * product_xcty.price
        temp_order = Order.get_by_order_number(customer.id, '-1')
        self.assertEqual(temp_order.is_subscription_order, False)
        self.assertEqual(temp_order.amount, price_xcty)
        self.assertEqual(temp_order.is_subscription_extension_order, False)  # Is set when paying the order

        add_item_to_order(posm_product).order_item
        temp_order = Order.get_by_order_number(customer.id, '-1')
        self.assertEqual(temp_order.amount, price_xcty + product_posm.price * 250)

        # test removing an order item
        remove_from_order(xcty_order_item.id)
        temp_order = Order.get_by_order_number(customer.id, '-1')
        self.assertEqual(temp_order.amount, product_posm.price * 250)

        xcty_order_item = add_item_to_order(xcty_product).order_item
        temp_order = Order.get_by_order_number(customer.id, '-1')
        self.assertEqual(temp_order.amount, price_xcty + product_posm.price * 250)
        self.assertEqual(pay_order().success, False)  # should be false since we have no credit card linked

        # todo: test with credit card linked
