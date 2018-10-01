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

from rogerthat.bizz.payment.providers.payconiq.models import PayconiqTransaction
from rogerthat.bizz.payment.providers.threefold.api import _get_explorer_url
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

    @property
    def external_url(self):
        if self.provider_id == 'threefold':
            explorer_url = _get_explorer_url(self.test_mode)
            return u'%s/hash.html?hash=%s' % (explorer_url, self.id)

    @classmethod
    def create_key(cls, provider_id, transaction_id):
        return ndb.Key(cls, transaction_id, namespace=provider_id)


def transaction_key(provider_id, transaction_id):
    if provider_id == 'payconiq':
        return PayconiqTransaction.create_key(transaction_id)
    elif provider_id == 'threefold':
        return PaymentTransaction.create_key('threefold', transaction_id)
    return None
