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

from google.appengine.ext import db

from mcfw.utils import Enum
from rogerthat.bizz.payment.providers.payconiq.models import PayconiqTransaction
from rogerthat.dal import parent_key, parent_key_unsafe
from rogerthat.rpc import users
from rogerthat.utils.service import get_identity_from_service_identity_user, \
    get_service_user_from_service_identity_user
from solutions.common import SOLUTION_COMMON
from solutions.common.consts import ORDER_TYPE_SIMPLE, ORDER_TYPE_ADVANCED, SECONDS_IN_MINUTE
from solutions.common.models.appointment import SolutionAppointmentWeekdayTimeframe
from solutions.common.models.payment import PaymentTransaction
from solutions.common.models.properties import SolutionUserProperty


class OrderSettingsFlags(Enum):
    DEFAULT = 0  # No special flow
    ENABLED = 1  # instead of a flow, a poke will be used to check if it is currently paused or not.
    PAUSED = 2  # Currently not possible to order


class SolutionOrderSettings(db.Model):
    TYPE_SIMPLE = ORDER_TYPE_SIMPLE
    TYPE_ADVANCED = ORDER_TYPE_ADVANCED
    DEFAULT_ORDER_TYPE = ORDER_TYPE_SIMPLE
    text_1 = db.TextProperty()
    order_type = db.IntegerProperty(indexed=False, default=DEFAULT_ORDER_TYPE)
    leap_time = db.IntegerProperty(indexed=False, default=15)
    leap_time_type = db.IntegerProperty(indexed=False, default=SECONDS_IN_MINUTE)

    order_ready_message = db.StringProperty(indexed=False, multiline=True)
    manual_confirmation = db.BooleanProperty(indexed=False, default=False)
    flags = db.IntegerProperty(indexed=False, choices=OrderSettingsFlags.all())
    disable_order_outside_hours = db.BooleanProperty(default=False, indexed=False)
    outside_hours_message = db.StringProperty(indexed=False)
    # properties names are for easy conversion to ndb model later
    pause_settings_enabled = db.BooleanProperty(name='pause_settings.enabled', indexed=False, default=False)
    pause_settings_paused_until = db.DateTimeProperty(name='pause_settings.paused_until', indexed=False)
    pause_settings_message = db.StringProperty(name='pause_settings.message', indexed=False)

    @classmethod
    def create_key(cls, service_user):
        return db.Key.from_path(cls.kind(), service_user.email(), parent=parent_key(service_user, SOLUTION_COMMON))

    @property
    def service_user(self):
        return users.User(self.parent_key().name())


class SolutionOrder(db.Model):
    STATUS_RECEIVED = 1
    STATUS_COMPLETED = 2

    ORDER_STATUSES = (STATUS_RECEIVED, STATUS_COMPLETED)

    status = db.IntegerProperty(indexed=True)
    user = db.UserProperty(indexed=True)
    timestamp = db.IntegerProperty(indexed=True)
    description = db.TextProperty(indexed=False)
    sender = SolutionUserProperty()
    picture_url = db.TextProperty(indexed=False)
    phone_number = db.StringProperty(indexed=False)
    deleted = db.BooleanProperty(indexed=True, default=False)

    solution_inbox_message_key = db.StringProperty(indexed=False)

    # advanced orders only
    takeaway_time = db.IntegerProperty(indexed=False, default=0)
    transaction_id = db.StringProperty()
    payment_provider = db.StringProperty()

    @property
    def id(self):
        return self.key().id()

    @property
    def transaction_key(self):
        if self.transaction_id and self.payment_provider:
            if self.payment_provider == 'payconiq':
                return PayconiqTransaction.create_key(self.transaction_id)
            elif 'threefold' in self.payment_provider:
                return PaymentTransaction.create_key(self.payment_provider, self.transaction_id)

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
    def solution_order_key(self):
        # TODO get rid of this and use id instead
        return str(self.key())

    @classmethod
    def list(cls, service_identity_user):
        return cls.all() \
            .filter('deleted', False) \
            .ancestor(parent_key_unsafe(service_identity_user, SOLUTION_COMMON)) \
            .order('-timestamp').run()


class SolutionOrderWeekdayTimeframe(SolutionAppointmentWeekdayTimeframe):
    pass
