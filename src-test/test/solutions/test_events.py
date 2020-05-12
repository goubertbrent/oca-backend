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

from datetime import datetime, date

import oca_unittest
from solutions.common.models.agenda import Event, EventCalendarType, EventPeriod, EventDate, EventOpeningPeriod


class TestEvents(oca_unittest.TestCase):
    comparison_date = datetime(2019, 12, 17, 12, 0, 0)

    def test_get_closest_occurrence_single(self):
        event = Event(calendar_type=EventCalendarType.SINGLE, start_date=datetime(2019, 12, 17, 18),
                      end_date=datetime(2019, 12, 17, 22, 30))
        start, end = event.get_closest_occurrence(self.comparison_date)
        self.assertEqual(event.start_date, start.datetime)
        self.assertEqual(event.end_date, end.datetime)

    def test_get_closest_occurrence_multiple(self):
        first_start_date = datetime(2020, 1, 28, 20, 30)
        event = Event(calendar_type=EventCalendarType.MULTIPLE,
                      periods=[EventPeriod(end=EventDate(datetime=datetime(2020, 1, 28, 20, 30)),
                                           start=EventDate(datetime=first_start_date)),
                               EventPeriod(end=EventDate(datetime=datetime(2020, 2, 28, 20, 30)),
                                           start=EventDate(datetime=datetime(2020, 2, 28, 18, 15))),
                               EventPeriod(end=EventDate(datetime=datetime(2020, 3, 31, 19, 30)),
                                           start=EventDate(datetime=datetime(2020, 3, 31, 17, 15)))])
        start, end = event.get_closest_occurrence(self.comparison_date)
        self.assertEqual(first_start_date, start.datetime)
        self.assertEqual(event.periods[0].end.datetime, end.datetime)
        start, end = event.get_closest_occurrence(event.periods[1].start.datetime)
        self.assertEqual(event.periods[2].start.datetime, start.datetime)
        self.assertEqual(event.periods[2].end.datetime, end.datetime)

        event.periods = [event.periods[2], event.periods[0], event.periods[1]]
        start, end = event.get_closest_occurrence(self.comparison_date)
        self.assertEqual(first_start_date, start.datetime)

    def test_get_closest_occurrence_periodic_1(self):
        event = Event(calendar_type=EventCalendarType.PERIODIC,
                      end_date=datetime(2020, 5, 24, 22, 0),
                      start_date=datetime(2020, 3, 15, 23, 0),
                      opening_hours=[EventOpeningPeriod(close=u'2000', day=1, open=u'1900'),
                                     EventOpeningPeriod(close=u'2115', day=1, open=u'2015')])
        start, end = event.get_closest_occurrence(self.comparison_date)
        self.assertEqual(datetime(2020, 3, 16, 19, 0), start.datetime)
        self.assertEqual(datetime(2020, 3, 16, 20, 00), end.datetime)
        start, end = event.get_closest_occurrence(datetime(2020, 4, 1, 19))
        self.assertEqual(datetime(2020, 4, 6, 19, 00), start.datetime)
        self.assertEqual(datetime(2020, 4, 6, 20, 00), end.datetime)
        start, end = event.get_closest_occurrence(datetime(2020, 4, 6, 19, 1))
        self.assertEqual(datetime(2020, 4, 6, 20, 15), start.datetime)
        self.assertEqual(datetime(2020, 4, 6, 21, 15), end.datetime)

    def test_get_closest_occurrence_periodic_2(self):
        # See https://www.uitinvlaanderen.be/agenda/e/video-s-bewerken/430f9948-3050-4690-808b-51af77c85282
        event = Event(calendar_type=EventCalendarType.PERIODIC,
                      end_date=datetime(2020, 1, 26, 23, 0),
                      opening_hours=[EventOpeningPeriod(close=u'1630', day=1, open=u'1330')],
                      start_date=datetime(2020, 1, 20, 13, 30))
        comparison_date = datetime(2020, 1, 15, 12, 37)
        start, end = event.get_closest_occurrence(comparison_date)
        self.assertEqual(datetime(2020, 1, 20, 13, 30), start.datetime)
        self.assertEqual(datetime(2020, 1, 20, 16, 30), end.datetime)

    def test_get_closest_occurrence_no_opening_hours(self):
        event = Event(calendar_type=EventCalendarType.PERIODIC,
                      end_date=datetime(2020, 1, 8, 23, 0),
                      start_date=datetime(2020, 1, 1, 13, 30))
        comparison_date = datetime(2020, 1, 1, 0, 0)
        start, end = event.get_closest_occurrence(comparison_date)
        self.assertEqual(datetime(2020, 1, 1, 13, 30), start.datetime)
        self.assertEqual(datetime(2020, 1, 1, 23, 59, 59, 999999), end.datetime)

    def test_get_occurrence_dates_no_opening(self):
        # See https://www.uitinvlaanderen.be/agenda/e/video-s-bewerken/430f9948-3050-4690-808b-51af77c85282
        event = Event(calendar_type=EventCalendarType.PERIODIC,
                      end_date=datetime(2020, 1, 27, 0, 0),
                      opening_hours=[EventOpeningPeriod(close=u'1630', day=1, open=u'1330')],
                      start_date=datetime(2020, 1, 13, 13, 30))
        comparison_date = datetime(2020, 1, 1)
        dates = event.get_occurrence_dates(comparison_date)
        self.assertEqual(3, len(dates))
        first_start, first_end = dates[0]
        self.assertEqual(datetime(2020, 1, 13, 13, 30), first_start)
        self.assertEqual(datetime(2020, 1, 13, 16, 30), first_end)
        last_start, last_end = dates[-1]
        self.assertEqual(datetime(2020, 1, 27, 13, 30), last_start)
        self.assertEqual(datetime(2020, 1, 27, 16, 30), last_end)

    def test_get_occurrence_dates_no_opening_hours(self):
        event = Event(calendar_type=EventCalendarType.PERIODIC,
                      end_date=datetime(2020, 1, 8),
                      start_date=datetime(2020, 1, 1))
        comparison_date = datetime(2020, 1, 1)
        dates = event.get_occurrence_dates(comparison_date)
        first_start, first_end = dates[0]
        self.assertEqual(datetime(2020, 1, 1), first_start)
        self.assertEqual(datetime(2020, 1, 1, 23, 59, 59, 999999), first_end)
        last_start, last_end = dates[-1]
        self.assertEqual(datetime(2020, 1, 8), last_start)
        self.assertEqual(datetime(2020, 1, 8, 23, 59, 59, 999999), last_end)
        self.assertEqual(8, len(dates))

    def test_get_occurrence_dates_without_time(self):
        event = Event(calendar_type=EventCalendarType.SINGLE,
                      end_date=datetime(2020, 1, 28),
                      start_date=datetime(2020, 1, 28),
                      periods=[EventPeriod(end=EventDate(date=date(2020, 1, 28)),
                                           start=EventDate(date=date(2020, 1, 28)))])
        dates = event.get_occurrence_dates(datetime(2020, 1, 1))
        first_start, first_end = dates[0]
        self.assertEqual(1, len(dates))
        self.assertEqual(datetime(2020, 1, 28), first_start)
        self.assertEqual(datetime(2020, 1, 28, 23, 59, 59, 999999), first_end)

    def test_get_occurrence_dates_without_time_multiple(self):
        event = Event(calendar_type=EventCalendarType.MULTIPLE,
                      end_date=datetime(2020, 1, 1),
                      start_date=datetime(2020, 1, 1),
                      periods=[EventPeriod(end=EventDate(date=date(2020, 2, 29)),
                                           start=EventDate(date=date(2020, 2, 29))),
                               EventPeriod(end=EventDate(date=date(2020, 1, 6)),
                                           start=EventDate(date=date(2020, 1, 5)))])
        dates = event.get_occurrence_dates(datetime(2020, 1, 1))
        first_start, first_end = dates[0]
        self.assertEqual(datetime(2020, 2, 29), first_start)
        self.assertEqual(datetime(2020, 2, 29, 23, 59, 59, 999999), first_end)
        last_start, last_end = dates[-1]
        self.assertEqual(datetime(2020, 1, 5), last_start)
        self.assertEqual(datetime(2020, 1, 6, 23, 59, 59, 999999), last_end)
        self.assertEqual(2, len(dates))

    def test_crappy_end_date(self):
        # No opening hours, and end date is a few thousand years in the future
        # Should only return 100 occurrences, as to not overload the search index with a million occurrence dates...
        event = Event(calendar_type=EventCalendarType.PERIODIC,
                      end_date=datetime(5201, 6, 28),
                      start_date=datetime(2019, 9, 1))
        dates = event.get_occurrence_dates(datetime(2020, 2, 18))
        first_start, first_end = dates[0]
        self.assertEqual(datetime(2020, 2, 18), first_start)
        self.assertEqual(100, len(dates))

    def test_crappy_end_date_with_hours(self):
        event = Event(calendar_type=EventCalendarType.PERIODIC,
                      end_date=datetime(5201, 6, 28),
                      start_date=datetime(2019, 9, 1), )
        event.opening_hours = [EventOpeningPeriod(close=u'1630', day=1, open=u'1330')]
        dates = event.get_occurrence_dates(datetime(2020, 2, 17))
        first_start, first_end = dates[0]
        self.assertEqual(datetime(2020, 2, 17, 13, 30), first_start)
        self.assertEqual(100, len(dates))
