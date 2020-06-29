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

import oca_unittest
from rogerthat.bizz.embedded_applications import delete_embedded_application
from rogerthat.bizz.payment import get_payment_methods, service_put_provider
from rogerthat.models.properties.forms import BasePaymentMethod
from rogerthat.rpc import users
from rogerthat.to.messaging.forms import PaymentMethodTO
from rogerthat.to.payment import GetPaymentMethodsRequestTO, ServicePaymentProviderFeeTO
from util import setup_payment_providers, TEST_PROVIDER_ID, TEST_CURRENCY


class Test(oca_unittest.TestCase):
    def setUp(self, datastore_hr_probability=0):
        super(Test, self).setUp(datastore_hr_probability)
        self.test_payment_provider = setup_payment_providers()
        self.service_email = 'testservice@rogerth.at/+default+'
        self.payment_service_provider = self.put_service_provider(self.test_payment_provider.id)

    def tearDown(self):
        delete_embedded_application(self.test_payment_provider.embedded_application)
        super(Test, self).tearDown()

    def put_service_provider(self, provider_id):
        return service_put_provider(users.User(self.service_email), provider_id, {}, test_mode=True,
                                    enabled=True, fee=ServicePaymentProviderFeeTO(amount=3,
                                                                                  precision=2,
                                                                                  min_amount=50,
                                                                                  currency='EUR'))

    def test_get_payment_methods(self):
        precision = 2
        usd_method = PaymentMethodTO(provider_id=TEST_PROVIDER_ID,
                                     currency=TEST_CURRENCY,
                                     amount=100,
                                     precision=precision,
                                     calculate_amount=True,
                                     target=self.service_email)
        eur_method = PaymentMethodTO(provider_id=TEST_PROVIDER_ID,
                                     currency='EUR',
                                     amount=300,  # intentionally wrong, should stay like this
                                     precision=precision,
                                     calculate_amount=False,
                                     target=self.service_email)
        request = GetPaymentMethodsRequestTO(service=self.service_email,
                                             test_mode=True,
                                             base_method=BasePaymentMethod(currency='USD',
                                                                           amount=100,
                                                                           precision=precision, ),
                                             methods=[usd_method, eur_method])
        result = get_payment_methods(request, users.User('someone@example.com'))
        self.assertEqual(1, len(result.methods))
        self.assertEqual(2, len(result.methods[0].methods))
        self.assertEqual(TEST_PROVIDER_ID, result.methods[0].provider.id)
        self.assertEqual(100, result.methods[0].methods[0].amount)
        self.assertEqual(300, result.methods[0].methods[1].amount)
        self.assertEqual(self.service_email, result.methods[0].methods[1].target)

    def test_payment_method_base(self):
        usd_amount = 1240
        usd_method = PaymentMethodTO(provider_id=TEST_PROVIDER_ID,
                                     currency='USD',
                                     amount=0,
                                     precision=2,
                                     calculate_amount=True,
                                     target=self.service_email)
        eur_method = PaymentMethodTO(provider_id=TEST_PROVIDER_ID,
                                     currency='EUR',
                                     amount=0,
                                     precision=2,
                                     calculate_amount=True,
                                     target=self.service_email)
        request = GetPaymentMethodsRequestTO(service=self.service_email,
                                             test_mode=True,
                                             base_method=BasePaymentMethod(currency='USD',
                                                                           amount=usd_amount,
                                                                           precision=2),
                                             methods=[usd_method, eur_method])
        result = get_payment_methods(request, users.User('someone@example.com'))
        self.assertEqual(usd_amount, result.methods[0].methods[0].amount)
        self.assertEqual(usd_amount / 2, result.methods[0].methods[1].amount)

    def test_different_base(self):
        eur_amount = 500
        eur_method = PaymentMethodTO(provider_id=TEST_PROVIDER_ID,
                                     currency='EUR',
                                     amount=0,
                                     precision=2,
                                     calculate_amount=True,
                                     target=self.service_email)
        usd_method = PaymentMethodTO(provider_id=TEST_PROVIDER_ID,
                                     currency='USD',
                                     amount=0,
                                     precision=2,
                                     calculate_amount=True,
                                     target=self.service_email)
        request = GetPaymentMethodsRequestTO(service=self.service_email,
                                             test_mode=True,
                                             base_method=BasePaymentMethod(currency='EUR',
                                                                           amount=eur_amount,
                                                                           precision=2),
                                             methods=[eur_method, usd_method])
        result = get_payment_methods(request, users.User('someone@example.com'))
        self.assertEqual(eur_amount, result.methods[0].methods[0].amount)
        self.assertEqual(eur_amount * 2, result.methods[0].methods[1].amount)

    def test_fee(self):
        fee = self.payment_service_provider.fee.amount
        eur_amount = 49
        eur_method = PaymentMethodTO(provider_id=TEST_PROVIDER_ID,
                                     currency='EUR',
                                     amount=0,
                                     precision=2,
                                     calculate_amount=True,
                                     target=self.service_email)
        usd_method = PaymentMethodTO(provider_id=TEST_PROVIDER_ID,
                                     currency='USD',
                                     amount=0,
                                     precision=2,
                                     calculate_amount=True,
                                     target=self.service_email)
        request = GetPaymentMethodsRequestTO(service=self.service_email,
                                             test_mode=True,
                                             base_method=BasePaymentMethod(currency='EUR',
                                                                           amount=eur_amount,
                                                                           precision=2),
                                             methods=[eur_method, usd_method])
        result = get_payment_methods(request, users.User('someone@example.com'))
        self.assertEqual(eur_amount + fee, result.methods[0].methods[0].amount)
        # conversion ratio between usd and eur is 0.5
        self.assertEqual((eur_amount + fee) * 2, result.methods[0].methods[1].amount)

    def test_fee_2(self):
        fee = self.payment_service_provider.fee.amount
        usd_amount = 49
        eur_method = PaymentMethodTO(provider_id=TEST_PROVIDER_ID,
                                     currency='EUR',
                                     amount=0,
                                     precision=2,
                                     calculate_amount=True,
                                     target=self.service_email)
        usd_method = PaymentMethodTO(provider_id=TEST_PROVIDER_ID,
                                     currency='USD',
                                     amount=0,
                                     precision=2,
                                     calculate_amount=True,
                                     target=self.service_email)
        request = GetPaymentMethodsRequestTO(service=self.service_email,
                                             test_mode=True,
                                             base_method=BasePaymentMethod(currency='USD',
                                                                           amount=usd_amount,
                                                                           precision=2),
                                             methods=[eur_method, usd_method])
        result = get_payment_methods(request, users.User('someone@example.com'))
        usd_f = float(usd_amount)
        self.assertEqual(long(round(usd_f * 0.5 + fee)), result.methods[0].methods[0].amount)
        # conversion ratio between usd and eur is 0.5
        # Fee is in EUR, so we gotta double it here
        self.assertEqual(usd_f + (fee / 0.5), result.methods[0].methods[1].amount)
