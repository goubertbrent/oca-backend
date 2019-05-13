# -*- coding: utf-8 -*-
# Copyright 2019 Mobicage NV
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
from solutions.common.cron.events.uitdatabank import _get_period_dates


class TestEvents(oca_unittest.TestCase):
    def test_get_period_dates(self):
        period = {
            "dateto": "2019-04-01",
            "weekscheme": {
                "monday": {
                    "openingtime": {
                        "to": "10:30:00",
                        "from": "09:30:00"
                    },
                    "opentype": "open"
                },
                "tuesday": {
                    "opentype": "closed"
                },
                "friday": {
                    "opentype": "closed"
                },
                "wednesday": {
                    "opentype": "closed"
                },
                "thursday": {
                    "opentype": "closed"
                },
                "sunday": {
                    "opentype": "closed"
                },
                "saturday": {
                    "opentype": "closed"
                }
            },
            "datefrom": "2019-01-14"
        }
        start_dates, end_dates = _get_period_dates(period)
        self.assertEqual(1547454600, start_dates[0])
        self.assertEqual(1554103800, start_dates[-1])
        self.assertEqual(1547458200, end_dates[0])
        self.assertEqual(1554107400, end_dates[-1])
