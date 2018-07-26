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

from datetime import datetime

from babel import dates
from babel.dates import format_time
from google.appengine.ext import db

from rogerthat.dal import parent_key
from rogerthat.rpc import users
from solutions import translate
from solutions.common import SOLUTION_COMMON
from solutions.common.consts import SECONDS_IN_HOUR


class SolutionAppointmentSettings(db.Model):
    text_1 = db.TextProperty()

    @classmethod
    def create_key(cls, service_user):
        return db.Key.from_path(cls.kind(), service_user.email(),
                                parent=parent_key(service_user, SOLUTION_COMMON))

    @property
    def service_user(self):
        return users.User(self.parent_key().name())


class SolutionAppointmentWeekdayTimeframe(db.Model):
    day = db.IntegerProperty()
    # seconds since midnight
    time_from = db.IntegerProperty()  # type: int
    # seconds since midnight
    time_until = db.IntegerProperty()  # type: int

    @classmethod
    def get_or_create(cls, parent_key, day, time_from, time_until):
        """
        Creates a new timeframe. If it already exists, returns the existing timeframe.
        """
        tf = cls.all().ancestor(parent_key).filter('day = ', day).filter('time_from = ', time_from).filter(
            'time_until = ', time_until).get()
        if tf:
            return tf
        else:
            return cls(
                parent=parent_key,
                day=day,
                time_from=time_from,
                time_until=time_until
            )

    def day_str(self, language):
        return dates.get_day_names('wide', locale=language)[self.day].capitalize()

    def label(self, language):
        time_from_dt = datetime.utcfromtimestamp(self.time_from)
        time_until_dt = datetime.utcfromtimestamp(self.time_until)
        return translate(language, SOLUTION_COMMON , 'appointment-1-label',
                         day=self.day_str(language),
                         time_from=format_time(time_from_dt, format='short', locale=language),
                         time_until=format_time(time_until_dt, format='short', locale=language))

    @property
    def id(self):
        return self.key().id()

    @property
    def service_user(self):
        return users.User(self.parent_key().name())

    @classmethod
    def list(cls, service_user, solution):
        # type: (users.User, unicode) -> list[SolutionAppointmentWeekdayTimeframe]
        return sorted(cls.all().ancestor(parent_key(service_user, solution)),
                      key=lambda x: (x.day, x.time_from, x.time_until))

    @classmethod
    def create_default_timeframes_if_nessecary(cls, service_user, solution):
        has_timeframes = cls.all(keys_only=True).ancestor(parent_key(service_user, solution)).get()
        if not has_timeframes:
            to_put = list()
            for i in xrange(0, 5):
                to_put.append(cls(
                    parent=parent_key(service_user, solution),
                    day=i,
                    time_from=SECONDS_IN_HOUR * 9,
                    time_until=SECONDS_IN_HOUR * 17
                ))
            db.put(to_put)
