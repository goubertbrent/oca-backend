# -*- coding: utf-8 -*-
# Copyright 2018 GIG Technology NV
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

from google.appengine.ext import ndb

from mcfw.utils import Enum
from rogerthat.models import NdbModel


class PaymentTransaction(NdbModel):
    STATUS_PENDING = u'pending'
    STATUS_SUCCEEDED = u'succeeded'
    STATUS_FAILED = u'failed'

    timestamp = ndb.IntegerProperty()
    test_mode = ndb.BooleanProperty()
    target = ndb.StringProperty()
    currency = ndb.StringProperty()
    amount = ndb.IntegerProperty()
    precision = ndb.IntegerProperty(default=9)
    app_user = ndb.StringProperty()
    status = ndb.StringProperty(choices=[STATUS_PENDING, STATUS_SUCCEEDED])
    external_id = ndb.StringProperty()
    service_user = ndb.StringProperty()

    @property
    def id(self):
        return self.key.id()

    @property
    def provider_id(self):
        return self.key.namespace()

    @classmethod
    def create_key(cls, provider_id, transaction_id):
        return ndb.Key(cls, transaction_id, namespace=provider_id)


class PayconiqPaymentStatus(Enum):
    INITIAL = 'INITIAL'
    CREATION = 'CREATION'
    PENDING = 'PENDING'
    CONFIRMED = 'CONFIRMED'
    BLOCKED = 'BLOCKED'
    CANCELED_BY_MERCHANT = 'CANCELED_BY_MERCHANT'
    SUCCEEDED = 'SUCCEEDED'
    FAILED = 'FAILED'
    TIMEDOUT = 'TIMEDOUT'
    CANCELED = 'CANCELED'


# Note that 'succeeded' is not final and can still be blocked afterwards
FINAL_STATUSES = [PayconiqPaymentStatus.BLOCKED, PayconiqPaymentStatus.FAILED, PayconiqPaymentStatus.TIMEDOUT,
                  PayconiqPaymentStatus.CANCELED, PayconiqPaymentStatus.CANCELED_BY_MERCHANT]


# For payments via dashboard
class PayconiqPayment(NdbModel):
    creation_date = ndb.DateTimeProperty(auto_now_add=True)
    paid_date = ndb.DateTimeProperty()
    service_user = ndb.StringProperty(required=True)
    currency = ndb.StringProperty(indexed=False)
    amount = ndb.IntegerProperty(indexed=False)
    precision = ndb.IntegerProperty(indexed=False, default=2)
    status = ndb.StringProperty(choices=PayconiqPaymentStatus.all(), default=PayconiqPaymentStatus.INITIAL)
    order_number = ndb.StringProperty()
    transaction_id = ndb.StringProperty()

    @property
    def id(self):
        return self.key.id()

    @classmethod
    def create_key(cls, id_):
        return ndb.Key(cls, id_)
