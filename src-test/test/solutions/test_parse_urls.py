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
from solutions.common.bizz.settings import parse_facebook_url


class TestParseFbUrls(oca_unittest.TestCase):
    def test_parse_url_1(self):
        result = parse_facebook_url('www.fb.com/onzestadapp')
        self.assertEqual('https://www.facebook.com/onzestadapp', result)

    def test_parse_url_2(self):
        result = parse_facebook_url('www.facebook.com/onzestadapp')
        self.assertEqual('https://www.facebook.com/onzestadapp', result)

    def test_parse_url_3(self):
        result = parse_facebook_url('  https://www.facebook.com/onzestadapp')
        self.assertEqual('https://www.facebook.com/onzestadapp', result)

    def test_parse_url_4(self):
        result = parse_facebook_url('https://facebook.com/onzestadapp')
        self.assertEqual('https://www.facebook.com/onzestadapp', result)

    def test_parse_url_5(self):
        self.assertEqual(None, parse_facebook_url('https://google.com?q=onzestadapp'))
        self.assertEqual(None, parse_facebook_url('geen'))
        self.assertEqual(None, parse_facebook_url('onzestadapp (www.facebook.com/onzestadapp)'))

    def test_parse_url_6(self):
        result = parse_facebook_url('https://business.facebook.com/greenvalleybelgium/?business_id=135650101025700')
        self.assertEqual('https://business.facebook.com/greenvalleybelgium/?business_id=135650101025700', result)

    def test_parse_url_7(self):
        result = parse_facebook_url('HTtps://wWw.FaCeBoOk.com/onzestadapp')
        self.assertEqual('https://www.facebook.com/onzestadapp', result)

    def test_parse_url_8(self):
        result = parse_facebook_url('@onzestadapp')
        self.assertEqual('https://www.facebook.com/onzestadapp', result)
