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

import datetime
import time

from rogerthat.dal import parent_key, parent_key_unsafe
from rogerthat.rpc import users
from rogerthat.utils import now
from rogerthat.utils.service import get_identity_from_service_identity_user, \
    get_service_user_from_service_identity_user
from google.appengine.ext import db

from solutions.common.consts import SECONDS_IN_MINUTE, SECONDS_IN_HOUR
from solutions.common.models.properties import SolutionUserProperty
from solutions.common.utils import create_service_identity_user_wo_default


class SandwichSettings(db.Model):
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 4
    THURSDAY = 8
    FRIDAY = 16
    SATURDAY = 32
    SUNDAY = 64
    DAYS = [MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY]
    DAYS_JS = [SUNDAY, MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY]
    LEAP_TIME_TYPES = [SECONDS_IN_MINUTE, SECONDS_IN_HOUR]

    status_days = db.IntegerProperty(default=31)
    time_from = db.IntegerProperty(default=28800)
    time_until = db.IntegerProperty(default=46800)
    broadcast_days = db.IntegerProperty(default=0)
    reminder_broadcast_message = db.TextProperty()
    remind_at = db.IntegerProperty(default=39600)
    show_prices = db.BooleanProperty(default=True)
    order_flow = db.StringProperty(indexed=False)
    leap_time_enabled = db.BooleanProperty(indexed=False, default=False)
    leap_time = db.IntegerProperty(indexed=False, default=15)
    leap_time_type = db.IntegerProperty(indexed=False, default=SECONDS_IN_MINUTE)

    @property
    def service_user(self):
        return users.User(self.parent_key().name())

    @classmethod
    def create_key(cls, service_user, solution):
        return db.Key.from_path(cls.kind(), service_user.email(), parent=parent_key(service_user, solution))

    @classmethod
    def get_settings(cls, service_user, solution):
        """
        Returns:
            SandwichSettings:
        """
        sandwich_settings = cls.get(cls.create_key(service_user, solution))
        if not sandwich_settings:
            from solutions import translate as common_translate
            from solutions.common import SOLUTION_COMMON
            from solutions.common.dal import get_solution_settings

            sln_settings = get_solution_settings(service_user)
            sandwich_settings = SandwichSettings(key_name=service_user.email(),
                                                 parent=parent_key(service_user, solution))
            sandwich_settings.reminder_broadcast_message = common_translate(sln_settings.main_language, SOLUTION_COMMON,
                                                                            u'order-sandwich-reminder-message')
            sandwich_settings.put()

        return sandwich_settings

    def can_order_sandwiches_on(self, date):
        return self.status_days & SandwichSettings.DAYS[date.weekday()] == SandwichSettings.DAYS[date.weekday()]

    def can_broadcast_for_sandwiches_on(self, date):
        return self.broadcast_days & SandwichSettings.DAYS[date.weekday()] == SandwichSettings.DAYS[date.weekday()]

    def get_reminder_broadcast_timeout(self, date):
        now_ = now()
        timeout = 0
        timeout_max = now_ + 10 * 60 * 60
        time_now = date.hour * 3600 + date.minute * 60

        if self.time_until >= time_now:
            timeout = now_ + self.time_until - time_now

        if timeout > timeout_max:
            timeout = timeout_max
        return timeout


class SandwichLastBroadcastDay(db.Model):
    year = db.IntegerProperty(indexed=False)
    month = db.IntegerProperty(indexed=False)
    day = db.IntegerProperty(indexed=False)

    @property
    def service_user(self):
        return users.User(self.parent_key().name())

    @classmethod
    def create_key(cls, service_user, solution):
        return db.Key.from_path(cls.kind(), service_user.email(), parent=parent_key(service_user, solution))

    @classmethod
    def get_last_broadcast_day(cls, service_user, solution):
        return cls.get(cls.create_key(service_user, solution))


class SandwichType(db.Model):
    description = db.StringProperty()
    price = db.IntegerProperty()  # In euro cents
    order = db.IntegerProperty()
    deleted = db.BooleanProperty(default=False)

    @property
    def price_in_euro(self):
        return u'{:20,.2f}'.format(self.price / 100.0).strip()

    @property
    def service_user(self):
        return users.User(self.parent_key().name())

    @property
    def type_id(self):
        return self.key().id()

    id = type_id

    @staticmethod
    def get_by_type_id(service_user, solution, type_id):
        return SandwichType.get_by_id(type_id, parent_key(service_user, solution))

    @staticmethod
    def list(service_user, solution):
        return SandwichType.all().ancestor(parent_key(service_user, solution)).filter('deleted', False).order('order')

class SandwichTopping(db.Model):
    description = db.StringProperty()
    price = db.IntegerProperty()  # In euro cents
    order = db.IntegerProperty()
    deleted = db.BooleanProperty(default=False)

    @property
    def price_in_euro(self):
        return u'{:20,.2f}'.format(self.price / 100.0).strip()

    @property
    def service_user(self):
        return users.User(self.parent_key().name())

    @property
    def topping_id(self):
        return self.key().id()

    id = topping_id

    @staticmethod
    def get_by_topping_id(service_user, solution, topping_id):
        return SandwichTopping.get_by_id(topping_id, parent_key(service_user, solution))

    @staticmethod
    def list(service_user, solution):
        return SandwichTopping.all().ancestor(parent_key(service_user, solution)).filter('deleted', False).order('order')

class SandwichOption(db.Model):
    description = db.StringProperty()
    price = db.IntegerProperty()  # In euro cents
    order = db.IntegerProperty()
    deleted = db.BooleanProperty(default=False)

    @property
    def price_in_euro(self):
        return u'{:20,.2f}'.format(self.price / 100.0).strip()

    @property
    def service_user(self):
        return users.User(self.parent_key().name())

    @staticmethod
    def get_by_option_ids(service_user, solution, option_ids):
        return SandwichOption.get_by_id(option_ids, parent_key(service_user, solution))

    @staticmethod
    def list(service_user, solution, include_deleted=False):
        qry = SandwichOption.all().ancestor(parent_key(service_user, solution))
        if include_deleted:
            return qry.order('order')
        else:
            return qry.filter('deleted', False).order('order')

    @property
    def option_id(self):
        return self.key().id()

    id = option_id

class SandwichOrder(db.Model):
    STATUS_RECEIVED = 1
    STATUS_READY = 2
    STATUS_REPLIED = 3

    sender = SolutionUserProperty()
    order_time = db.IntegerProperty()
    type_id = db.IntegerProperty()
    topping_id = db.IntegerProperty()
    option_ids = db.ListProperty(int)
    price = db.IntegerProperty()  # In euro cents
    remark = db.TextProperty()
    deleted = db.BooleanProperty(default=False)
    status = db.IntegerProperty(default=STATUS_RECEIVED)
    solution_inbox_message_key = db.StringProperty(indexed=False)
    takeaway_time = db.IntegerProperty(indexed=False)

    @property
    def price_in_euro(self):
        return u'{:20,.2f}'.format(self.price / 100.0).strip()

    @property
    def service_identity_user(self):
        return users.User(self.parent_key().name())

    @property
    def service_user(self):
        return get_service_user_from_service_identity_user(self.service_identity_user)

    @property
    def service_identity(self):
        return get_identity_from_service_identity_user(self.service_identity_user)

    @property
    def solution(self):
        return self.parent_key().kind()

    @property
    def solution_sandwich_order_key(self):
        return str(self.key())

    @property
    def parent_message_key(self):
        return self.key().name()

    id = parent_message_key

    @property
    def sandwich_type(self):
        return SandwichType.get_by_type_id(self.service_user, self.solution, self.type_id)

    @property
    def sandwich_topping(self):
        if not self.topping_id:
            return None
        return SandwichTopping.get_by_topping_id(self.service_user, self.solution, self.topping_id)

    @property
    def sandwich_options(self):
        l = list()
        for option_id in self.option_ids:
            l.append(SandwichOption.get_by_option_ids(self.service_user, self.solution, option_id))
        return l

    @staticmethod
    def get_by_order_id(service_user, service_identity, solution, order_id):
        service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
        return SandwichOrder.get_by_key_name(order_id, parent_key_unsafe(service_identity_user, solution))

    @staticmethod
    def list(service_user, service_identity, solution):
        service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
        midnight = int(time.mktime(time.strptime(str(datetime.date.today()), '%Y-%m-%d')))
        return SandwichOrder.all().ancestor(parent_key_unsafe(service_identity_user, solution)).filter('deleted', False).filter("order_time >", midnight).order('-order_time')
