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

import random

from rogerthat.utils import base38
import mc_unittest


class Test(mc_unittest.TestCase):


    def testBase42(self):
        self.assertEqual(0, base38.decode_int(base38.encode_int(0)))
        randomint = random.randint(0, 1000000000)
        self.assertEqual(randomint, base38.decode_int(base38.encode_int(randomint)))

    def testDecode(self):
        self.assertFalse(base38.is_base38("04$J1"))
        base38.decode_int("04J1")
