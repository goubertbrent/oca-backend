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

import oca_unittest
from rogerthat.bizz.embedded_applications import delete_embedded_application
from rogerthat.bizz.payment import get_payment_methods, create_payment_provider, service_put_provider
from rogerthat.models.properties.forms import BasePaymentMethod
from rogerthat.rpc import users
from rogerthat.to.messaging.forms import PaymentMethodTO
from rogerthat.to.payment import GetPaymentMethodsRequestTO, PaymentProviderTO, ConversionRatioTO, \
    ConversionRatioValueTO, ServicePaymentProviderFeeTO
from util import setup_payment_providers, TEST_PROVIDER_ID, TEST_CURRENCY


class Test(oca_unittest.TestCase):
    def setUp(self, datastore_hr_probability=0):
        super(Test, self).setUp(datastore_hr_probability)
        self.test_payment_provider = setup_payment_providers()
        self.service_email = 'testservice@rogerth.at/+default+'
        self.tft_address = '01312bca26747afc3744e04e6c2cbe5aa7818e962d2cbd354cdad935cd6c49122b9f35eebf5f99'
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

    def create_tf_provider(self, usd_eur_conversion, tft_usd_conversion):
        obj = PaymentProviderTO(
            id='threefold',
            name='Threefold',
            logo=None,
            version=1,
            description=u'Threefold description',
            oauth_settings=None,
            background_color=None,
            text_color=None,
            button_color=None,
            black_white_logo=None,
            asset_types=[],
            currencies=[],
            settings={},
            embedded_application=self.test_payment_provider.embedded_application,
            app_ids=[],
            conversion_ratio=ConversionRatioTO(
                base='USD',
                values=[ConversionRatioValueTO(currency='EUR', rate=usd_eur_conversion),
                        ConversionRatioValueTO(currency='TFT', rate=tft_usd_conversion)]
            )
        )
        create_payment_provider(obj)
        self.put_service_provider(obj.id)

    def test_get_payment_methods(self):
        precision = 2
        usd_method = PaymentMethodTO(provider_id=TEST_PROVIDER_ID,
                                     currency=TEST_CURRENCY,
                                     amount=100,
                                     precision=precision,
                                     calculate_amount=True,
                                     target=self.service_email)
        tft_method = PaymentMethodTO(provider_id=TEST_PROVIDER_ID,
                                     currency='TFT',
                                     amount=9999,  # intentionally wrong, should be updated
                                     precision=precision,
                                     calculate_amount=True,
                                     target=self.tft_address)
        eur_method = PaymentMethodTO(provider_id=TEST_PROVIDER_ID,
                                     currency='EUR',
                                     amount=300,  # intentionally wrong, should stay like this
                                     precision=precision,
                                     calculate_amount=False,
                                     target=self.service_email)
        tft_more_precision = PaymentMethodTO(provider_id=TEST_PROVIDER_ID,
                                             currency='TFT',
                                             amount=0,
                                             precision=5,
                                             calculate_amount=True,
                                             target=self.tft_address)
        request = GetPaymentMethodsRequestTO(service=self.service_email,
                                             test_mode=True,
                                             base_method=BasePaymentMethod(currency='USD',
                                                                           amount=100,
                                                                           precision=precision, ),
                                             methods=[usd_method, tft_method, eur_method, tft_more_precision])
        result = get_payment_methods(request, users.User('someone@example.com'))
        self.assertEqual(1, len(result.methods))
        self.assertEqual(4, len(result.methods[0].methods))
        self.assertEqual(TEST_PROVIDER_ID, result.methods[0].provider.id)
        self.assertEqual(100, result.methods[0].methods[0].amount)
        self.assertEqual(10, result.methods[0].methods[1].amount)
        self.assertEqual(300, result.methods[0].methods[2].amount)
        self.assertEqual(self.service_email, result.methods[0].methods[2].target)
        self.assertEqual(5, result.methods[0].methods[3].precision)
        self.assertEqual(10000, result.methods[0].methods[3].amount)

    def test_payment_method_2(self):
        usd_eur_conversion = 0.9
        tft_usd_conversion = 10
        self.create_tf_provider(usd_eur_conversion, tft_usd_conversion)
        precision = 2
        eur_price = 1523  # 15.23 euro
        eur_method = PaymentMethodTO(provider_id=TEST_PROVIDER_ID,
                                     currency='EUR',
                                     amount=0,
                                     precision=precision,
                                     calculate_amount=True,
                                     target=self.service_email)
        tft_method = PaymentMethodTO(provider_id='threefold',
                                     currency='TFT',
                                     amount=0,
                                     precision=precision,
                                     calculate_amount=True,
                                     target=self.tft_address)
        tft_precision = 5
        tft_more_method = PaymentMethodTO(provider_id='threefold',
                                          currency='TFT',
                                          amount=0,
                                          precision=tft_precision,
                                          calculate_amount=True,
                                          target=self.tft_address)
        request = GetPaymentMethodsRequestTO(service=self.service_email,
                                             test_mode=True,
                                             base_method=BasePaymentMethod(currency='EUR',
                                                                           amount=eur_price,
                                                                           precision=precision),
                                             methods=[eur_method, tft_method, tft_more_method])
        result = get_payment_methods(request, users.User('someone@example.com'))
        self.assertEqual(2, len(result.methods))
        self.assertEqual(1, len(result.methods[0].methods))
        self.assertEqual(2, len(result.methods[1].methods))
        self.assertEqual(eur_price, result.methods[0].methods[0].amount)
        self.assertEqual(16922, result.methods[1].methods[0].amount)
        expected = round(eur_price / usd_eur_conversion * tft_usd_conversion * pow(10, tft_precision - precision))
        self.assertEqual(expected, result.methods[1].methods[1].amount)

    def test_payment_method_3(self):
        usd_eur_conversion = 0.9
        tft_usd_conversion = 10
        self.create_tf_provider(usd_eur_conversion, tft_usd_conversion)
        precision = 2
        eur_price = 1234
        tft_precision = 5
        eur_method = PaymentMethodTO(provider_id=TEST_PROVIDER_ID,
                                     currency='EUR',
                                     amount=0,
                                     precision=precision,
                                     calculate_amount=True,
                                     target=self.service_email)
        tft_method = PaymentMethodTO(provider_id='threefold',
                                     currency='TFT',
                                     amount=0,
                                     precision=tft_precision,
                                     calculate_amount=True,
                                     target=self.tft_address)
        request = GetPaymentMethodsRequestTO(service=self.service_email,
                                             test_mode=True,
                                             base_method=BasePaymentMethod(currency='EUR',
                                                                           amount=eur_price,
                                                                           precision=precision),
                                             methods=[eur_method, tft_method])
        result = get_payment_methods(request, users.User('someone@example.com'))
        self.assertEqual(2, len(result.methods))
        self.assertEqual(1, len(result.methods[0].methods))
        self.assertEqual(1, len(result.methods[1].methods))
        expected = round(eur_price / usd_eur_conversion * tft_usd_conversion * pow(10, tft_precision - precision))
        self.assertEqual(expected, result.methods[1].methods[0].amount)

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
