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

from google.appengine.ext import deferred, db

from rogerthat.consts import MIGRATION_QUEUE
from rogerthat.utils.transactions import run_in_xg_transaction
from shop.dal import get_mobicage_legal_entity
from shop.models import InvoiceNumber, OrderNumber, ChargeNumber, LegalEntity


def job():
    deferred.defer(_job, _queue=MIGRATION_QUEUE)


def create_mobicage_legal_entity():

    mobicage_entity = LegalEntity(is_mobicage=True,
                                  name=u'Mobicage NV',
                                  address=u'Antwerpsesteenweg 19',
                                  postal_code=u'9080',
                                  city=u'Lochristi',
                                  country_code=u'BE',
                                  phone=u'+32 9 324 25 64',
                                  email=u'info@mobicage.com',
                                  iban=u'BE85 3630 8576 4006',
                                  bic=u'BBRUBEBB',
                                  terms_of_use=None,
                                  vat_number=u'BE 0835 560 572',
                                  vat_percent=21)
    mobicage_entity.put()
    return mobicage_entity


def _job():
    legal_entity = get_mobicage_legal_entity()
    if not legal_entity:
        legal_entity = create_mobicage_legal_entity()
    to_put = list()
    to_delete = list()
    for invoice_number in InvoiceNumber.all():
        copied_object = InvoiceNumber(key_name=invoice_number.key().name(),
                                      parent=legal_entity,
                                      last_number=invoice_number.last_number)
        to_put.append(copied_object)
        to_delete.append(invoice_number)
    for order_number in OrderNumber.all():
        copied_object = OrderNumber(key_name=order_number.key().name(),
                                    parent=legal_entity,
                                    last_number=order_number.last_number)
        to_put.append(copied_object)
        to_delete.append(order_number)
    for charge_number in ChargeNumber.all():
        copied_object = OrderNumber(key_name=charge_number.key().name(),
                                    parent=legal_entity,
                                    last_number=charge_number.last_number)
        to_put.append(copied_object)
        to_delete.append(charge_number)

    def trans():
        db.delete(to_delete)
        db.put(to_put)

    run_in_xg_transaction(trans)
