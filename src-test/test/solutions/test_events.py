# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
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
# @@license_version:1.5@@

import oca_unittest
from solutions.common.cron.events.uitdatabank import _get_period_dates, \
    get_start_and_end_from_v3_events, get_start_and_end_from_v3_period


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
        self.assertEqual(37800, end_dates[0])
        self.assertEqual(37800, end_dates[-1])

    def test_v3_timeframe_1(self):
        events = [
            {
                "startDate": "2019-07-11T08:00:00+00:00",
                "endDate": "2019-07-11T10:00:00+00:00"
            },
            {
                "startDate": "2019-08-08T08:00:00+01:00",
                "endDate": "2019-08-08T10:00:00+01:00"
            },
            {
                "startDate": "2019-09-12T08:00:00+02:00",
                "endDate": "2019-09-12T10:00:00+02:00"
            }
        ]

        start_dates, end_dates = get_start_and_end_from_v3_events('Europe/Brussels', events)

        self.assertEqual([1562839200, 1565254800, 1568275200], start_dates)
        self.assertEqual([43200, 39600, 36000], end_dates)

    def test_v3_timeframe_2(self):
        events = [
            {
                "startDate": "2019-10-07T13:00:00+02:00",
                "endDate": "2019-10-08T00:00:00+02:00"
            }
        ]

        start_dates, end_dates = get_start_and_end_from_v3_events('Europe/Brussels', events)

        self.assertEqual([1570453200], start_dates)
        self.assertEqual([0], end_dates)

    def test_v3_timeframe_3(self):
        events = [
            {
                "startDate": "2019-12-03T08:30:00+00:00",
                "endDate": "2019-12-17T11:00:00+00:00"
            }
        ]

        start_dates, end_dates = get_start_and_end_from_v3_events('Europe/Brussels', events)

        self.assertEqual([1575365401, 1575417601, 1575504001, 1575590401, 1575676801, 1575763201, 1575849601, 1575936001, 1576022401, 1576108801, 1576195201, 1576281601, 1576368001, 1576454401, 1576540801], start_dates)
        self.assertEqual([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 43200], end_dates)

    def test_v3_period(self):
        event = {
            "startDate": "2019-09-10T22:00:00+00:00",
            "endDate": "2019-11-26T23:00:00+00:00",
            "openingHours": [
                {
                    "opens": "20:00",
                    "closes": "21:15",
                    "dayOfWeek": [
                        "wednesday"
                    ]
                }
            ]
        }

        start_dates, end_dates = get_start_and_end_from_v3_period('Europe/Brussels', event)
        self.assertEqual([1568232000, 1568836800, 1569441600, 1570046400, 1570651200, 1571256000, 1571860800, 1572465600, 1573070400, 1573675200, 1574280000, 1574884800], start_dates)
        self.assertEqual([76500, 76500, 76500, 76500, 76500, 76500, 76500, 76500, 76500, 76500, 76500, 76500], end_dates)

