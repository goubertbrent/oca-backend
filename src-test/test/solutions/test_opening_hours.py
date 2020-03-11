# -*- coding: utf-8 -*-
# Copyright 2020 Green Valley NV
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
from __future__ import unicode_literals

from datetime import date, datetime

import oca_unittest
from rogerthat.models import OpeningPeriod, OpeningHour, OpeningHourException, OpeningHours
from rogerthat.rpc import users
from solutions.common.bizz.opening_hours import opening_hours_to_text


class TestOpeningHours(oca_unittest.TestCase):

    def _create_hours(self):
        hours = OpeningHours(
            key=OpeningHours.create_key(users.User('test@example.com'), '1'),
            type=OpeningHours.TYPE_STRUCTURED,
            periods=[
                OpeningPeriod(open=OpeningHour(day=1, time=u'1245'),
                              close=OpeningHour(day=1, time=u'1730')),
                OpeningPeriod(open=OpeningHour(day=2, time=u'0900'),
                              close=OpeningHour(day=2, time=u'1700')),
                OpeningPeriod(open=OpeningHour(day=0, time=u'1400'),
                              close=OpeningHour(day=0, time=u'1700')),
                OpeningPeriod(open=OpeningHour(day=1, time=u'0800'),
                              close=OpeningHour(day=1, time=u'1200')),
                OpeningPeriod(open=OpeningHour(day=5, time=u'0800'),
                              close=OpeningHour(day=5, time=u'1200')),
            ],
            exceptional_opening_hours=[
                OpeningHourException(start_date=date(2020, 1, 12), end_date=date(2020, 1, 13)),
                OpeningHourException(start_date=date(2020, 1, 1), end_date=date(2020, 1, 1)),
                OpeningHourException(start_date=date(2020, 8, 15), end_date=date(2020, 8, 16),
                                     description='Assumption of Mary'),
                OpeningHourException(start_date=date(2020, 1, 2), end_date=date(2020, 1, 2),
                                     description='Slacking off after new year\'s day'),

                OpeningHourException(start_date=date(2020, 7, 1), end_date=date(2020, 8, 30),
                                     description='Summer vacation - deviating hours on monday and friday',
                                     periods=[
                                         OpeningPeriod(open=OpeningHour(day=1, time='0900'),
                                                       close=OpeningHour(day=1, time='1200')),
                                         OpeningPeriod(open=OpeningHour(day=5, time='1000'),
                                                       close=OpeningHour(day=5, time='1200'))
                                     ])
            ]
        )
        hours.put()
        return hours

    def test_sort_hours(self):
        hours = self._create_hours()
        self.assertEqual(1, hours.periods[0].open.day)
        self.assertEqual('0800', hours.periods[0].open.time)
        self.assertEqual(0, hours.periods[-1].open.day)
        self.assertEqual('1400', hours.periods[-1].open.time)
        self.assertEqual(date(2020, 1, 1), hours.exceptional_opening_hours[0].start_date)

    def test_structured_to_str(self):
        hours = self._create_hours()
        current_date = datetime(2020, 1, 2)
        text = opening_hours_to_text(hours, 'en_GB', current_date)
        expected = """Monday
08:00 — 12:00
12:45 — 17:30

Tuesday
09:00 — 17:00

Friday
08:00 — 12:00

Sunday
14:00 — 17:00

Deviating opening hours

02/01/2020 Slacking off after new year's day — Closed
12/01/2020 — 13/01/2020 Closed
01/07/2020 — 30/08/2020 Summer vacation - deviating hours on monday and friday
Monday
09:00 — 12:00

Friday
10:00 — 12:00
15/08/2020 — 16/08/2020 Assumption of Mary — Closed"""
        self.assertEqual(expected, text)

    def test_always_open(self):
        hours = OpeningHours(
            key=OpeningHours.create_key(users.User('test@example.com'), '1'),
            type=OpeningHours.TYPE_STRUCTURED,
            periods=[
                OpeningPeriod(open=OpeningHour(day=0, time=u'0000')),
                OpeningPeriod(open=OpeningHour(day=1, time=u'0000')),
                OpeningPeriod(open=OpeningHour(day=2, time=u'0000')),
                OpeningPeriod(open=OpeningHour(day=3, time=u'0000')),
                OpeningPeriod(open=OpeningHour(day=4, time=u'0000')),
                OpeningPeriod(open=OpeningHour(day=5, time=u'0000')),
                OpeningPeriod(open=OpeningHour(day=6, time=u'0000')),
            ]
        )
        current_date = datetime(2020, 1, 2)
        text = opening_hours_to_text(hours, 'en_GB', current_date)
        expected = """Open 24/7"""
        self.assertEqual(expected, text)

    def test_open_24h(self):
        hours = OpeningHours(
            key=OpeningHours.create_key(users.User('test@example.com'), '1'),
            type=OpeningHours.TYPE_STRUCTURED,
            periods=[
                OpeningPeriod(open=OpeningHour(day=1, time='0000')),
                OpeningPeriod(open=OpeningHour(day=2, time='0800'), close=OpeningHour(day=1, time=u'1700')),
            ]
        )
        current_date = datetime(2020, 1, 2)
        text = opening_hours_to_text(hours, 'en_GB', current_date)
        expected = """Monday
Open 24 hours

Tuesday
08:00 — 17:00"""
        self.assertEqual(expected, text)

    def test_always_closed(self):
        hours = OpeningHours(
            key=OpeningHours.create_key(users.User('test@example.com'), '1'),
            type=OpeningHours.TYPE_STRUCTURED,
        )
        current_date = datetime(2020, 1, 2)
        text = opening_hours_to_text(hours, 'en_GB', current_date)
        expected = """Always closed"""
        self.assertEqual(expected, text)
