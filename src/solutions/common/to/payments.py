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

from mcfw.properties import unicode_property, bool_property, long_property
from rogerthat.to import TO


class PaymentSettingsTO(TO):
    optional = bool_property('optional')

    @classmethod
    def from_model(cls, model):
        return cls(optional=model.payment_optional)


class TransactionDetailsTO(TO):
    id = unicode_property('id')
    timestamp = long_property('timestamp')
    currency = unicode_property('currency')
    amount = long_property('amount')
    amount_str = unicode_property('amount_str')
    precision = long_property('precision')
    status = unicode_property('status')

    def get_display_amount(self):
        return float(self.amount) / pow(10, self.precision)

    @classmethod
    def from_model(cls, model):
        return cls(id=model.id,
                   timestamp=model.timestamp,
                   currency=model.currency,
                   amount=model.amount,
                   amount_str=u'%.2f' % (float(model.amount) / pow(10, model.precision)),
                   precision=model.precision,
                   status=model.status)
