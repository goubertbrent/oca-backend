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

import mc_unittest
from rogerthat.utils import privatize


class Test(mc_unittest.TestCase):

    def testPrivatize(self):
        d = {"a": [], "c": [{"a": {"request": {"email_addresses": ["carl@example.com", "geert@example.com", "tjorven@example.com"]}},
                                                 "ci": "54c8fccf-770f-488b-9887-279790aca2d6", "f": "com.mobicage.api.friends.findRogerthatUsersViaEmail",
                                                 "t": 1354747956, "av": 1}], "r": [], "av": 1}

        d_priv = {"a": [], "c": [{"a": {"request": {"email_addresses": ["***3 items***"]}},
                                                 "ci": "54c8fccf-770f-488b-9887-279790aca2d6", "f": "com.mobicage.api.friends.findRogerthatUsersViaEmail",
                                                 "t": 1354747956, "av": 1}], "r": [], "av": 1}

        assert privatize(d) == d_priv

    def testPrivatizeSubmitForm(self):
        request = {u'c': [{u'ci': u'c7ec5d51-5508-4298-bb2e-53a33690b13a', u'av': 1, u'a': {
            u'request': {u'test': True, u'id': 4609461981282304, u'sections': [{u'id': u'0', u'components': [
                {u'id': u'Normal question', u'value': u'Yes', u'type': u'single_select'},
                {u'id': u'Sensitive question', u'value': u'PRIVATE INFO', u'type': u'text_input'}]}], u'version': 16}},
                           u'f': u'com.mobicage.api.forms.submitForm', u't': 1567588483}], u'r': [], u'a': [], u'av': 1}

        expected_result = {u'c': [{u'ci': u'c7ec5d51-5508-4298-bb2e-53a33690b13a', u'av': 1, u'a': {
            u'request': {u'test': True, u'id': 4609461981282304,
                         u'sections': [{u'id': u'0', u'components': ['***2 items***']}], u'version': 16}},
                                   u'f': u'com.mobicage.api.forms.submitForm', u't': 1567588483}],
                           u'r': [], u'a': [], u'av': 1}
        self.assertEquals(privatize(request), expected_result)
