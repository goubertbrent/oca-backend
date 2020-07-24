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

from __future__ import unicode_literals

import datetime

import mc_unittest
from rogerthat.bizz.opening_hours import get_opening_hours_info
from rogerthat.models import OpeningHours, OpeningPeriod, OpeningHour, OpeningHourException, ServiceIdentity
from rogerthat.rpc import users
from rogerthat.to.maps import WeekDayTextTO, MapItemLineTextPartTO


class TestOpeningHours(mc_unittest.TestCase):
    timezone = 'Europe/Brussels'
    lang = 'en'
    exception_color = 'DB4437'
    exception_color_hex = '#DB4437'

    def _create_hours(self, exception_color):
        opening_hours = OpeningHours(
            key=OpeningHours.create_key(users.User('test@example.com'), ServiceIdentity.DEFAULT),
            type=OpeningHours.TYPE_STRUCTURED,
        )
        opening_hours.periods = [
            OpeningPeriod(close=OpeningHour(day=2, time='1832'),  # tuesday
                          open=OpeningHour(day=2, time='0200')),
            OpeningPeriod(close=OpeningHour(day=3, time='1833'),  # wednesday
                          open=OpeningHour(day=3, time='0300')),
            OpeningPeriod(close=OpeningHour(day=4, time='1834'),  # thursday
                          open=OpeningHour(day=4, time='0400')),
            OpeningPeriod(close=OpeningHour(day=5, time='1835'),  # friday
                          open=OpeningHour(day=5, time='0500')),
            OpeningPeriod(close=OpeningHour(day=0, time='0400'),  # saturday
                          open=OpeningHour(day=6, time='1806'))]
        opening_hours.exceptional_opening_hours = [
            OpeningHourException(start_date=datetime.date(2019, 12, 25),
                                 end_date=datetime.date(2019, 12, 25),
                                 description='25 dec gesloten e2',
                                 description_color=self.exception_color,
                                 periods=[]),
            OpeningHourException(start_date=datetime.date(2019, 12, 28),
                                 end_date=datetime.date(2020, 1, 2),
                                 description='28 dec - 2 jan langer open e2',
                                 description_color=self.exception_color,
                                 periods=[
                                     OpeningPeriod(close=OpeningHour(day=2, time='2032'),  # tuesday
                                                   open=OpeningHour(day=2, time='0200'),
                                                   description='e2 tuesday',
                                                   description_color=self.exception_color_hex),
                                     OpeningPeriod(close=OpeningHour(day=3, time='2033'),  # wednesday
                                                   open=OpeningHour(day=3, time='0300'),
                                                   description=None,
                                                   description_color=None),
                                     OpeningPeriod(close=OpeningHour(day=4, time='2034'),  # thursday
                                                   open=OpeningHour(day=4, time='0400'),
                                                   description='e2 thursday',
                                                   description_color=self.exception_color_hex),
                                     OpeningPeriod(close=OpeningHour(day=5, time='2035'),  # friday
                                                   open=OpeningHour(day=5, time='0500'),
                                                   description='e2 friday',
                                                   description_color=self.exception_color_hex),
                                     OpeningPeriod(close=OpeningHour(day=0, time='0300'),  # saturday
                                                   open=OpeningHour(day=6, time='2000'),
                                                   description='e2 saturday',
                                                   description_color=self.exception_color_hex)]),
            OpeningHourException(start_date=datetime.date(2020, 1, 3),
                                 end_date=datetime.date(2020, 1, 3),
                                 description='3 jan gesloten e3',
                                 description_color=self.exception_color),
            OpeningHourException(start_date=datetime.date(2020, 1, 4),
                                 end_date=datetime.date(2020, 1, 4),
                                 description='4 jan gesloten e4',
                                 description_color=self.exception_color)
        ]
        opening_hours.put()
        return opening_hours
    
    def test_hours_lang(self):
        opening_hours = self._create_hours(self.exception_color)
        now = datetime.datetime(2019, 11, 27, 12, 41, 2)  # Wednesday
        get_opening_hours_info(opening_hours, self.timezone, 'nl_AX', now)
        get_opening_hours_info(opening_hours, self.timezone, 'fr_IT', now)
        get_opening_hours_info(opening_hours, self.timezone, 'it_BE', now)

    def test_hours_1(self):
        opening_hours = self._create_hours(self.exception_color)
        now = datetime.datetime(2019, 11, 27, 12, 41, 2)  # Wednesday
        now_open, open_until, extra_description, weekday_text = get_opening_hours_info(opening_hours, self.timezone,
                                                                                       self.lang, now)
        self.assertEqual(True, now_open)
        self.assertEqual('Open until 6:33 PM', open_until)
        self.assertEqual(None, extra_description)
        self.assertEqual([WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                        day='Monday'),
                          WeekDayTextTO(lines=[MapItemLineTextPartTO(text='2:00 AM - 6:32 PM')],
                                        day='Tuesday'),
                          WeekDayTextTO(lines=[MapItemLineTextPartTO(text='3:00 AM - 6:33 PM')],
                                        day='Wednesday'),
                          WeekDayTextTO(lines=[MapItemLineTextPartTO(text='4:00 AM - 6:34 PM')],
                                        day='Thursday'),
                          WeekDayTextTO(lines=[MapItemLineTextPartTO(text='5:00 AM - 6:35 PM')],
                                        day='Friday'),
                          WeekDayTextTO(lines=[MapItemLineTextPartTO(text='6:06 PM - 4:00 AM')],
                                        day='Saturday'),
                          WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                        day='Sunday')], weekday_text)

    def test_hours_2(self):
        opening_hours = self._create_hours(self.exception_color)
        now = datetime.datetime(2019, 11, 28, 00, 41, 2)  # Thursday
        now_open, open_until, extra_description, weekday_text = get_opening_hours_info(opening_hours, self.timezone,
                                                                                       self.lang, now)
        self.assertEqual(now_open, False)
        self.assertEqual(open_until, 'Opens at 4:00 AM')
        self.assertEqual(extra_description, None)
        self.assertEqual([WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                        day='Monday'),
                          WeekDayTextTO(lines=[MapItemLineTextPartTO(text='2:00 AM - 6:32 PM')],
                                        day='Tuesday'),
                          WeekDayTextTO(lines=[MapItemLineTextPartTO(text='3:00 AM - 6:33 PM')],
                                        day='Wednesday'),
                          WeekDayTextTO(lines=[MapItemLineTextPartTO(text='4:00 AM - 6:34 PM')],
                                        day='Thursday'),
                          WeekDayTextTO(lines=[MapItemLineTextPartTO(text='5:00 AM - 6:35 PM')],
                                        day='Friday'),
                          WeekDayTextTO(lines=[MapItemLineTextPartTO(text='6:06 PM - 4:00 AM')],
                                        day='Saturday'),
                          WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                        day='Sunday')], weekday_text)

    def test_hours_3(self):
        opening_hours = self._create_hours(self.exception_color)
        now = datetime.datetime(2019, 11, 30, 06, 41, 02)  # Saturday
        now_open, open_until, extra_description, weekday_text = get_opening_hours_info(opening_hours, self.timezone,
                                                                                       self.lang, now)
        self.assertEqual(False, now_open)
        self.assertEqual(open_until, 'Opens at 6:06 PM')
        self.assertEqual(None, extra_description)
        self.assertEqual([WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                        day='Monday'),
                          WeekDayTextTO(lines=[MapItemLineTextPartTO(text='2:00 AM - 6:32 PM')],
                                        day='Tuesday'),
                          WeekDayTextTO(lines=[MapItemLineTextPartTO(text='3:00 AM - 6:33 PM')],
                                        day='Wednesday'),
                          WeekDayTextTO(lines=[MapItemLineTextPartTO(text='4:00 AM - 6:34 PM')],
                                        day='Thursday'),
                          WeekDayTextTO(lines=[MapItemLineTextPartTO(text='5:00 AM - 6:35 PM')],
                                        day='Friday'),
                          WeekDayTextTO(lines=[MapItemLineTextPartTO(text='6:06 PM - 4:00 AM')],
                                        day='Saturday'),
                          WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                        day='Sunday')], weekday_text)
        
    
    def test_hours_3_2(self):
        opening_hours = self._create_hours(self.exception_color)
        now = datetime.datetime(2019, 11, 30, 18, 41, 02)  # Saturday
        now_open, open_until, extra_description, weekday_text = get_opening_hours_info(opening_hours, self.timezone,
                                                                                       self.lang, now)
        self.assertEqual(True, now_open)
        self.assertEqual(open_until, 'Open until Sunday 4:00 AM')
        self.assertEqual(None, extra_description)
        self.assertEqual([WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                        day='Monday'),
                          WeekDayTextTO(lines=[MapItemLineTextPartTO(text='2:00 AM - 6:32 PM')],
                                        day='Tuesday'),
                          WeekDayTextTO(lines=[MapItemLineTextPartTO(text='3:00 AM - 6:33 PM')],
                                        day='Wednesday'),
                          WeekDayTextTO(lines=[MapItemLineTextPartTO(text='4:00 AM - 6:34 PM')],
                                        day='Thursday'),
                          WeekDayTextTO(lines=[MapItemLineTextPartTO(text='5:00 AM - 6:35 PM')],
                                        day='Friday'),
                          WeekDayTextTO(lines=[MapItemLineTextPartTO(text='6:06 PM - 4:00 AM')],
                                        day='Saturday'),
                          WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                        day='Sunday')], weekday_text)

    def test_hours_4(self):
        opening_hours = self._create_hours(self.exception_color)
        now = datetime.datetime(2019, 12, 1, 17, 41, 2) # Sunday
        now_open, open_until, extra_description, weekday_text = get_opening_hours_info(opening_hours, self.timezone,
                                                                                       self.lang, now)
        self.assertEqual(now_open, False)
        self.assertEqual(open_until, 'Opens on Tuesday at 2:00 AM')
        self.assertEqual(extra_description, None)
        self.assertEqual(weekday_text, [WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                                      day='Monday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='2:00 AM - 6:32 PM')],
                                                      day='Tuesday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='3:00 AM - 6:33 PM')],
                                                      day='Wednesday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='4:00 AM - 6:34 PM')],
                                                      day='Thursday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='5:00 AM - 6:35 PM')],
                                                      day='Friday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='6:06 PM - 4:00 AM')],
                                                      day='Saturday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                                      day='Sunday')])

    def test_hours_5(self):
        opening_hours = self._create_hours(self.exception_color)
        now = datetime.datetime(2019, 12, 2, 7, 41, 2) # Monday
        now_open, open_until, extra_description, weekday_text = get_opening_hours_info(opening_hours, self.timezone,
                                                                                       self.lang, now)
        self.assertEqual(now_open, False)
        self.assertEqual(open_until, 'Opens on Tuesday at 2:00 AM')
        self.assertEqual(extra_description, None)
        self.assertEqual(weekday_text, [WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                                      day='Monday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='2:00 AM - 6:32 PM')],
                                                      day='Tuesday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='3:00 AM - 6:33 PM')],
                                                      day='Wednesday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='4:00 AM - 6:34 PM')],
                                                      day='Thursday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='5:00 AM - 6:35 PM')],
                                                      day='Friday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='6:06 PM - 4:00 AM')],
                                                      day='Saturday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                                      day='Sunday')])

    def test_hours_6(self):
        opening_hours = self._create_hours(self.exception_color)
        now = datetime.datetime(2019, 12, 2, 17, 41, 2) # Monday
        now_open, open_until, extra_description, weekday_text = get_opening_hours_info(opening_hours, self.timezone,
                                                                                       self.lang, now)
        self.assertEqual(now_open, False)
        self.assertEqual(open_until, 'Opens on Tuesday at 2:00 AM')
        self.assertEqual(extra_description, None)
        self.assertEqual(weekday_text, [WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                                      day='Monday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='2:00 AM - 6:32 PM')],
                                                      day='Tuesday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='3:00 AM - 6:33 PM')],
                                                      day='Wednesday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='4:00 AM - 6:34 PM')],
                                                      day='Thursday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='5:00 AM - 6:35 PM')],
                                                      day='Friday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='6:06 PM - 4:00 AM')],
                                                      day='Saturday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                                      day='Sunday')])

    def test_hours_7(self):
        opening_hours = self._create_hours(self.exception_color)
        now = datetime.datetime(2019, 12, 3, 0, 41, 2) # Tuesday
        now_open, open_until, extra_description, weekday_text = get_opening_hours_info(opening_hours, self.timezone,
                                                                                       self.lang, now)
        self.assertEqual(now_open, False)
        self.assertEqual(open_until, 'Opens at 2:00 AM')
        self.assertEqual(extra_description, None)
        self.assertEqual(weekday_text, [WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                                      day='Monday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='2:00 AM - 6:32 PM')],
                                                      day='Tuesday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='3:00 AM - 6:33 PM')],
                                                      day='Wednesday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='4:00 AM - 6:34 PM')],
                                                      day='Thursday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='5:00 AM - 6:35 PM')],
                                                      day='Friday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='6:06 PM - 4:00 AM')],
                                                      day='Saturday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                                      day='Sunday')])

    def test_hours_8(self):
        opening_hours = self._create_hours(self.exception_color)
        now = datetime.datetime(2019, 12, 25, 12, 0, 0)  # Wednesday
        now_open, open_until, extra_description, weekday_text = get_opening_hours_info(opening_hours, self.timezone,
                                                                                       self.lang, now)
        self.assertEqual(False, now_open)
        self.assertEqual('Opens on Thursday at 4:00 AM', open_until)
        self.assertEqual('25 dec gesloten e2', extra_description)
        self.assertEqual([
            WeekDayTextTO(lines=[MapItemLineTextPartTO(color=None, text=u'Closed'),
                                 MapItemLineTextPartTO(color=u'#DB4437', text=u'28 dec - 2 jan langer open e2')],
                          day=u'Monday'),
            WeekDayTextTO(lines=[MapItemLineTextPartTO(color=None, text=u'2:00 AM - 8:32 PM'),
                                 MapItemLineTextPartTO(color=u'#DB4437', text=u'e2 tuesday')], day=u'Tuesday'),
            WeekDayTextTO(lines=[MapItemLineTextPartTO(color=None, text=u'Closed'),
                                 MapItemLineTextPartTO(color=u'#DB4437', text=u'25 dec gesloten e2')],
                          day=u'Wednesday'),
            WeekDayTextTO(lines=[MapItemLineTextPartTO(color=None, text=u'4:00 AM - 6:34 PM')], day=u'Thursday'),
            WeekDayTextTO(lines=[MapItemLineTextPartTO(color=None, text=u'5:00 AM - 6:35 PM')], day=u'Friday'),
            WeekDayTextTO(lines=[MapItemLineTextPartTO(color=None, text=u'8:00 PM - 3:00 AM'),
                                 MapItemLineTextPartTO(color=u'#DB4437', text=u'e2 saturday')], day=u'Saturday'),
            WeekDayTextTO(lines=[MapItemLineTextPartTO(color=None, text=u'Closed'),
                                 MapItemLineTextPartTO(color=u'#DB4437', text=u'28 dec - 2 jan langer open e2')],
                          day=u'Sunday')],
            weekday_text)

    def test_hours_9(self):
        opening_hours = self._create_hours(self.exception_color)
        now = datetime.datetime(2019, 12, 27, 12, 0, 0)  # Friday
        now_open, open_until, extra_description, weekday_text = get_opening_hours_info(opening_hours, self.timezone,
                                                                                       self.lang, now)
        self.assertEqual(True, now_open)
        self.assertEqual('Open until 6:35 PM', open_until)
        self.assertEqual(None, extra_description)
        self.assertEqual([
            WeekDayTextTO(lines=[MapItemLineTextPartTO(color=None, text=u'Closed'),
                                 MapItemLineTextPartTO(color=u'#DB4437', text=u'28 dec - 2 jan langer open e2')],
                          day=u'Monday'),
            WeekDayTextTO(lines=[MapItemLineTextPartTO(color=None, text=u'2:00 AM - 8:32 PM'),
                                 MapItemLineTextPartTO(color=u'#DB4437', text=u'e2 tuesday')], day=u'Tuesday'),
            WeekDayTextTO(lines=[MapItemLineTextPartTO(color=None, text=u'3:00 AM - 8:33 PM'),
                                 MapItemLineTextPartTO(color=u'#DB4437', text=u'28 dec - 2 jan langer open e2')],
                          day=u'Wednesday'),
            WeekDayTextTO(lines=[MapItemLineTextPartTO(color=None, text=u'4:00 AM - 8:34 PM'),
                                 MapItemLineTextPartTO(color=u'#DB4437', text=u'e2 thursday')], day=u'Thursday'),
            WeekDayTextTO(lines=[MapItemLineTextPartTO(color=None, text=u'5:00 AM - 6:35 PM')], day=u'Friday'),
            WeekDayTextTO(lines=[MapItemLineTextPartTO(color=None, text=u'8:00 PM - 3:00 AM'),
                                 MapItemLineTextPartTO(color=u'#DB4437', text=u'e2 saturday')], day=u'Saturday'),
            WeekDayTextTO(lines=[MapItemLineTextPartTO(color=None, text=u'Closed'),
                                 MapItemLineTextPartTO(color=u'#DB4437', text=u'28 dec - 2 jan langer open e2')],
                          day=u'Sunday')], weekday_text)


    def test_hours_10(self):
        opening_hours = self._create_hours(self.exception_color)
        now = datetime.datetime(2019, 12, 31, 12, 0, 0)  # Tuesday
        now_open, open_until, extra_description, weekday_text = get_opening_hours_info(opening_hours, self.timezone,
                                                                                       self.lang, now)
        self.assertEqual(True, now_open)
        self.assertEqual('Open until 8:32 PM', open_until)
        self.assertEqual('28 dec - 2 jan langer open e2', extra_description)
        self.assertEqual([
            WeekDayTextTO(lines=[MapItemLineTextPartTO(color=None, text=u'Closed')], day=u'Monday'),
            WeekDayTextTO(lines=[MapItemLineTextPartTO(color=None, text=u'2:00 AM - 8:32 PM'),
                                 MapItemLineTextPartTO(color=u'#DB4437', text=u'e2 tuesday')], day=u'Tuesday'),
            WeekDayTextTO(lines=[MapItemLineTextPartTO(color=None, text=u'3:00 AM - 8:33 PM'),
                                 MapItemLineTextPartTO(color=u'#DB4437', text=u'28 dec - 2 jan langer open e2')],
                          day=u'Wednesday'),
            WeekDayTextTO(lines=[MapItemLineTextPartTO(color=None, text=u'4:00 AM - 8:34 PM'),
                                 MapItemLineTextPartTO(color=u'#DB4437', text=u'e2 thursday')], day=u'Thursday'),
            WeekDayTextTO(lines=[MapItemLineTextPartTO(color=None, text=u'Closed'),
                                 MapItemLineTextPartTO(color=u'#DB4437', text=u'3 jan gesloten e3')], day=u'Friday'),
            WeekDayTextTO(lines=[MapItemLineTextPartTO(color=None, text=u'Closed'),
                                 MapItemLineTextPartTO(color=u'#DB4437', text=u'4 jan gesloten e4')], day=u'Saturday'),
            WeekDayTextTO(lines=[MapItemLineTextPartTO(color=None, text=u'Closed')], day=u'Sunday')], weekday_text)
        

    def _create_hours_2(self, exception_color):
        opening_hours = OpeningHours(
            key=OpeningHours.create_key(users.User('test@example.com'), ServiceIdentity.DEFAULT),
            type=OpeningHours.TYPE_STRUCTURED,
        )
        opening_hours.periods = [
            OpeningPeriod(close=OpeningHour(day=2, time='1832'),  # tuesday
                          open=OpeningHour(day=2, time='0200')),
            OpeningPeriod(close=OpeningHour(day=5, time='1835'),  # friday
                          open=OpeningHour(day=5, time='0500'))]
        opening_hours.put()
        return opening_hours

    def test_hours_11(self):
        opening_hours = self._create_hours_2(self.exception_color)
        now = datetime.datetime(2019, 11, 27, 12, 41, 2) # Wednesday
        now_open, open_until, extra_description, weekday_text = get_opening_hours_info(opening_hours, self.timezone,
                                                                                       self.lang, now)
        self.assertEqual(now_open, False)
        self.assertEqual(open_until, 'Opens on Friday at 5:00 AM')
        self.assertEqual(extra_description, None)
        self.assertEqual(weekday_text, [WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                                      day='Monday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='2:00 AM - 6:32 PM')],
                                                      day='Tuesday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                                      day='Wednesday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                                      day='Thursday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='5:00 AM - 6:35 PM')],
                                                      day='Friday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                                      day='Saturday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                                      day='Sunday')])

    def test_hours_12(self):
        opening_hours = self._create_hours_2(self.exception_color)
        now = datetime.datetime(2019, 11, 30, 12, 41, 2) # Saturday
        now_open, open_until, extra_description, weekday_text = get_opening_hours_info(opening_hours, self.timezone,
                                                                                       self.lang, now)
        self.assertEqual(now_open, False)
        self.assertEqual(open_until, 'Opens on Tuesday at 2:00 AM')
        self.assertEqual(extra_description, None)
        self.assertEqual(weekday_text, [WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                                      day='Monday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='2:00 AM - 6:32 PM')],
                                                      day='Tuesday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                                      day='Wednesday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                                      day='Thursday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='5:00 AM - 6:35 PM')],
                                                      day='Friday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                                      day='Saturday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                                      day='Sunday')])

    def _create_hours_3(self, exception_color):
        opening_hours = OpeningHours(
            key=OpeningHours.create_key(users.User('test@example.com'), ServiceIdentity.DEFAULT),
            type=OpeningHours.TYPE_STRUCTURED,
        )
        opening_hours.periods = [
            OpeningPeriod(close=None,
                          open=OpeningHour(day=1, time='0000')), # monday
            OpeningPeriod(close=None,
                          open=OpeningHour(day=2, time='0000')), # tuesday
            OpeningPeriod(close=None,
                          open=OpeningHour(day=3, time='0000')), # wednesday
            OpeningPeriod(close=None,
                          open=OpeningHour(day=4, time='0000')), # thursday
            ]
        opening_hours.exceptional_opening_hours = [
            OpeningHourException(start_date=datetime.date(2020, 3, 15),
                                 end_date=datetime.date(2020, 3, 17),
                                 description='exception 1 root',
                                 description_color=self.exception_color,
                                 periods=[
                                     OpeningPeriod(close=OpeningHour(day=1, time='0801'),  # monday
                                                   open=OpeningHour(day=1, time='0800'),
                                                   description='exception 1 child 1',
                                                   description_color=self.exception_color),
                                     OpeningPeriod(close=OpeningHour(day=1, time='0901'),  # monday
                                                   open=OpeningHour(day=1, time='0900'),
                                                   description='exception 1 child 2',
                                                   description_color=self.exception_color)]),
        ]
        opening_hours.put()
        return opening_hours

        def test_hours_13(self):
            opening_hours = self._create_hours_3(self.exception_color)

        now = datetime.datetime(2020, 3, 16, 6, 41, 2)  # Monday
        now_open, open_until, extra_description, weekday_text = get_opening_hours_info(opening_hours, self.timezone,
                                                                                       self.lang, now)
        self.assertEqual(now_open, False)
        self.assertEqual(open_until, 'Opens at 8:00 AM')
        self.assertEqual(extra_description, 'exception 1 root')
        self.assertEqual(weekday_text, [WeekDayTextTO(lines=[MapItemLineTextPartTO(text='8:00 AM - 8:01 AM'),
                                                             MapItemLineTextPartTO(text='exception 1 child 1',
                                                                                   color=self.exception_color_hex),
                                                             MapItemLineTextPartTO(text='9:00 AM - 9:01 AM'),
                                                             MapItemLineTextPartTO(text='exception 1 child 2',
                                                                                   color=self.exception_color_hex)],
                                                      day='Monday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed'),
                                                             MapItemLineTextPartTO(text='exception 1 root', color=self.exception_color_hex)],
                                                      day='Tuesday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Open 24 hours')],
                                                      day='Wednesday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Open 24 hours')],
                                                      day='Thursday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                                      day='Friday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                                      day='Saturday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                                      day='Sunday')])

        def test_hours_14(self):
            opening_hours = self._create_hours_3(self.exception_color)

        now = datetime.datetime(2020, 3, 16, 7, 41, 2)  # Monday
        now_open, open_until, extra_description, weekday_text = get_opening_hours_info(opening_hours, self.timezone,
                                                                                       self.lang, now)
        self.assertEqual(now_open, False)
        self.assertEqual(open_until, 'Opens at 9:00 AM')
        self.assertEqual(extra_description, 'exception 1 root')
        self.assertEqual(weekday_text, [WeekDayTextTO(lines=[MapItemLineTextPartTO(text='8:00 AM - 8:01 AM'),
                                                             MapItemLineTextPartTO(text='exception 1 child 1',
                                                                                   color=self.exception_color_hex),
                                                             MapItemLineTextPartTO(text='9:00 AM - 9:01 AM'),
                                                             MapItemLineTextPartTO(text='exception 1 child 2',
                                                                                   color=self.exception_color_hex)],
                                                      day='Monday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed'),
                                                             MapItemLineTextPartTO(text='exception 1 root', color=self.exception_color_hex)],
                                                      day='Tuesday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Open 24 hours')],
                                                      day='Wednesday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Open 24 hours')],
                                                      day='Thursday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                                      day='Friday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                                      day='Saturday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                                      day='Sunday')])

        def test_hours_15(self):
            opening_hours = self._create_hours_3(self.exception_color)

        now = datetime.datetime(2020, 3, 16, 12, 41, 2)  # Monday
        now_open, open_until, extra_description, weekday_text = get_opening_hours_info(opening_hours, self.timezone,
                                                                                       self.lang, now)
        self.assertEqual(now_open, False)
        self.assertEqual(open_until, 'Opens on Wednesday at 12:00 AM')
        self.assertEqual(extra_description, 'exception 1 root')
        self.assertEqual(weekday_text, [WeekDayTextTO(lines=[MapItemLineTextPartTO(text='8:00 AM - 8:01 AM'),
                                                             MapItemLineTextPartTO(text='exception 1 child 1',
                                                                                   color=self.exception_color_hex),
                                                             MapItemLineTextPartTO(text='9:00 AM - 9:01 AM'),
                                                             MapItemLineTextPartTO(text='exception 1 child 2',
                                                                                   color=self.exception_color_hex)],
                                                      day='Monday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed'),
                                                             MapItemLineTextPartTO(text='exception 1 root', color=self.exception_color_hex)],
                                                      day='Tuesday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Open 24 hours')],
                                                      day='Wednesday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Open 24 hours')],
                                                      day='Thursday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                                      day='Friday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                                      day='Saturday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                                      day='Sunday')])

        def test_hours_16(self):
            opening_hours = self._create_hours_3(self.exception_color)

        now = datetime.datetime(2020, 3, 17, 12, 41, 2)  # Tuesday
        now_open, open_until, extra_description, weekday_text = get_opening_hours_info(opening_hours, self.timezone,
                                                                                       self.lang, now)
        self.assertEqual(now_open, False)
        self.assertEqual(open_until, 'Opens on Wednesday at 12:00 AM')
        self.assertEqual(extra_description, 'exception 1 root')
        self.assertEqual(weekday_text, [WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Open 24 hours')],
                                                      day='Monday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed'),
                                                             MapItemLineTextPartTO(text='exception 1 root',
                                                                                   color=self.exception_color_hex)],
                                                      day='Tuesday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Open 24 hours')],
                                                      day='Wednesday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Open 24 hours')],
                                                      day='Thursday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                                      day='Friday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                                      day='Saturday'),
                                        WeekDayTextTO(lines=[MapItemLineTextPartTO(text='Closed')],
                                                      day='Sunday')])

    def test_close_day_gt_open_day(self):
        opening_hours = OpeningHours(
            key=OpeningHours.create_key(users.User('test@example.com'), ServiceIdentity.DEFAULT),
            type=OpeningHours.TYPE_STRUCTURED,
        )

        opening_hours.periods = [
            OpeningPeriod(close=OpeningHour(day=2, time='0100'),
                          open=OpeningHour(day=1, time='1700')),  # open monday from 17:00 until tuesday night 01:00
        ]
        now = datetime.datetime(2020, 3, 16, 12, 0, 0)  # Monday
        now_open, open_until, _, weekday_text = get_opening_hours_info(opening_hours, self.timezone,
                                                                       self.lang, now)
        self.assertEqual(False, now_open)
        self.assertEqual('Opens at 5:00 PM', open_until)
        self.assertEqual(WeekDayTextTO(lines=[MapItemLineTextPartTO(color=None, text=u'5:00 PM - 1:00 AM')],
                                       day=u'Monday'), weekday_text[0])

        now = datetime.datetime(2020, 3, 16, 18, 0, 0)  # Tuesday
        now_open, open_until, extra_description, weekday_text = get_opening_hours_info(opening_hours, self.timezone,
                                                                                       self.lang, now)
        self.assertEqual(True, now_open)
        self.assertEqual('Open until Tuesday 1:00 AM', open_until)


    def test_close_day_gt_open_day_multiple_periods(self):
        opening_hours = OpeningHours(
            key=OpeningHours.create_key(users.User('test@example.com'), ServiceIdentity.DEFAULT),
            type=OpeningHours.TYPE_STRUCTURED,
        )
        opening_hours.periods = [
            OpeningPeriod(close=OpeningHour(day=2, time='0100'),
                          open=OpeningHour(day=1, time='1700')),  # open monday from 17:00 until tuesday night 01:00
            OpeningPeriod(close=OpeningHour(day=2, time='1130'),
                          open=OpeningHour(day=2, time='0900')),  # open tuesday from 9 until 11:30
        ]

        now = datetime.datetime(2020, 3, 16, 18, 0, 0)  # Tuesday
        now_open, open_until, _, weekday_text = get_opening_hours_info(opening_hours, self.timezone, self.lang, now)
        print weekday_text[1]
        self.assertEqual(WeekDayTextTO(lines=[MapItemLineTextPartTO(color=None, text=u'5:00 PM - 1:00 AM')],
                                       day=u'Monday'), weekday_text[0])
        self.assertEqual(WeekDayTextTO(lines=[MapItemLineTextPartTO(color=None, text=u'9:00 AM - 11:30 AM')],
                                       day=u'Tuesday'), weekday_text[1])
        self.assertEqual(True, now_open)
        self.assertEqual('Open until Tuesday 1:00 AM', open_until)
