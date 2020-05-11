# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
# NOTICE: THIS FILE HAS BEEN MODIFIED BY GREEN VALLEY BELGIUM NV IN ACCORDANCE WITH THE APACHE LICENSE VERSION 2.0
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
# @@license_version:1.6@@

from google.appengine.ext import ndb

from rogerthat.bizz.payment.providers.payconiq.consts import PAYMENT_PROVIDER_ID
from rogerthat.bizz.payment.utils import get_provider_namespace


class PayconiqTransaction(ndb.Model):
    STATUS_PENDING = u'pending'
    STATUS_SUCCEEDED = u'succeeded'
    STATUS_FAILED = u'failed'
    STATUS_CANCELED = u'canceled'
    STATUS_TIMEDOUT = u'timedout'

    timestamp = ndb.IntegerProperty()
    test_mode = ndb.BooleanProperty()
    target = ndb.StringProperty()
    currency = ndb.StringProperty()
    amount = ndb.IntegerProperty()
    precision = ndb.IntegerProperty(default=2)
    memo = ndb.StringProperty()
    app_user = ndb.UserProperty()
    status = ndb.StringProperty()

    payconic_transaction_id = ndb.StringProperty()
    provider_id = PAYMENT_PROVIDER_ID

    @property
    def id(self):
        return self.key.id

    @property
    def transaction_url(self):
        if not self.payconic_transaction_id:
            return None
        if self.test_mode:
            return 'https://dev.payconiq.com/payconiq/v2/transactions/%s' % self.payconic_transaction_id
        return 'https://api.payconiq.com/payconiq/v2/transactions/%s' % self.payconic_transaction_id

    @property
    def external_url(self):
        if self.test_mode:
            return u'https://portal.ext.payconiq.com/new-transactions'
        else:
            return u'https://portal.payconiq.com/new-transactions'

    @classmethod
    def query(cls, *args, **kwargs):
        kwargs['namespace'] = get_provider_namespace(PAYMENT_PROVIDER_ID)
        return super(PayconiqTransaction, cls).query(*args, **kwargs)

    @classmethod
    def create_key(cls, transaction_id):
        return ndb.Key(cls, u"%s" % transaction_id, namespace=get_provider_namespace(PAYMENT_PROVIDER_ID))

    @classmethod
    def list(cls, start_time, end_time, status=STATUS_SUCCEEDED, test_mode=False):
        qry = cls.query()
        qry = qry.filter(PayconiqTransaction.test_mode == test_mode)
        qry = qry.filter(PayconiqTransaction.status == status)
        qry = qry.filter(PayconiqTransaction.timestamp > start_time)
        qry = qry.filter(PayconiqTransaction.timestamp < end_time)
        return qry
