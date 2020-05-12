#!/usr/bin/python
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
from shop.translations import shop_translations
from solutions import translations


class I18nTest(oca_unittest.TestCase):

    def test_sln_placeholders(self):
        from rogerthat_tests.i18n.test_i18n import Test as RogerthatI18nTest
        for d in translations.itervalues():
            RogerthatI18nTest._test_placeholder(self, d)

    def test_shop_placeholders(self):
        from rogerthat_tests.i18n.test_i18n import Test as RogerthatI18nTest
        RogerthatI18nTest._test_placeholder(self, shop_translations)
