# -*- coding: utf-8 -*-
# Copyright 2018 Mobicage NV
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

import oca_unittest
from shop.handlers import export_products
from shop.models import Product, LegalEntity


class TestCase(oca_unittest.TestCase):

    def test_export_products(self):
        self.set_datastore_hr_probability(1)

        export = export_products()
        product_count = Product.all().count(None)
        self.assertLess(0, product_count)
        self.assertEqual(product_count, len(export))

    def test_legal_entity_serialization(self):
        self.set_datastore_hr_probability(1)
        self.assertIsNotNone(LegalEntity.get_mobicage())
        self.assertIsNotNone(LegalEntity.get_mobicage())  # from cache
        self.assertIsNotNone(LegalEntity.get_mobicage())  # from cache

        mobicage_entity = LegalEntity(is_mobicage=True,
                                      name=u'Mobicage NV',
                                      address=u'Antwerpsesteenweg 19',
                                      postal_code=u'9080',
                                      city=u'Lochristi',
                                      country_code=u'BE',
                                      phone=u'+32 9 324 25 64',
                                      email=u'info@example.com',
                                      iban=u'BE85 3630 8576 4006',
                                      bic=u'BBRUBEBB',
                                      terms_of_use=None,
                                      vat_number=u'BE 0835 560 572',
                                      vat_percent=21)
        mobicage_entity.put()
        self.assertIsNotNone(LegalEntity.get_mobicage())
        self.assertIsNotNone(LegalEntity.get_mobicage())  # from cache
        self.assertIsNotNone(LegalEntity.get_mobicage())  # from cache

    def test_product(self):
        self.set_datastore_hr_probability(1)
        for p in Product.all():
            if not p.is_multilanguage:
                self.assertEqual(p.default_comment_translation_key, p.default_comment('es'))
                self.assertEqual(p.description_translation_key, p.description('es'))
