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

import logging

from google.appengine.ext import db
from google.appengine.ext import deferred

from rogerthat.consts import DEBUG
from rogerthat.consts import MIGRATION_QUEUE
from rogerthat.utils.transactions import run_in_xg_transaction
from shop.models import InvoiceNumber, OrderNumber, ChargeNumber, RegioManagerTeam, LegalEntity, Invoice


def job():
    deferred.defer(_job, _queue=MIGRATION_QUEUE)


def _job():
    order_numbers = list(OrderNumber.all())
    charge_numbers = list(ChargeNumber.all())
    invoice_numbers = list(InvoiceNumber.all())
    # Change parent from some OrderNumbers from RegioMangerTeam to LegalEntity.
    # Increase last_number for that legal entity when the parent was a team.
    to_delete = list()
    for ordernumber in order_numbers:
        if ordernumber.parent_key().kind() == RegioManagerTeam.kind():
            # Delete OrderNumber with parent RegioManagerTeam
            logging.warn("Deleting OrderNumber Year %s Original last number: %s" % (
                ordernumber.key().name(), ordernumber.last_number))
            to_delete.append(ordernumber)

    for chargenumber in charge_numbers:
        if chargenumber.parent_key().kind() == RegioManagerTeam.kind():
            logging.warn("Deleting ChargeNumber Year %s Original last number: %s" % (
                chargenumber.key().name(), chargenumber.last_number))
            to_delete.append(chargenumber)

    for invoicenumber in invoice_numbers:
        if invoicenumber.parent_key().kind() == RegioManagerTeam.kind():
            logging.warn("Deleting InvoiceNumber Year %s Original last number: %s" % (
                invoicenumber.key().name(), invoicenumber.last_number))
            # Delete InvoiceNumber with parent RegioManagerTeam
            to_delete.append(invoicenumber)
    db.delete(to_delete)

    for invoice in Invoice.all().filter('date >',
                                        1460635200 if not DEBUG else 1459870047):  # Thu, 14 Apr 2016 12:00:00 GMT
        def trans():
            new_invoice = Invoice(key_name=InvoiceNumber.next(LegalEntity.create_key(invoice.legal_entity_id)),
                                  parent=invoice.parent_key())
            logging.warn("Creating new Invoice %s" % new_invoice.key().name())
            new_invoice.date = invoice.date
            new_invoice.pdf = invoice.pdf
            new_invoice.amount = invoice.amount
            new_invoice.vat_pct = invoice.vat_pct
            new_invoice.total_amount = invoice.total_amount
            new_invoice.paid = invoice.paid
            new_invoice.paid_timestamp = invoice.paid_timestamp
            new_invoice.payment_type = invoice.payment_type
            new_invoice.operator = invoice.operator
            new_invoice.legal_entity_id = invoice.legal_entity_id
            new_invoice.put()
            invoice.deleted = True
            invoice.put()

        run_in_xg_transaction(trans)


def delete_deleted_invoices():
    db.delete(Invoice.all(keys_only=True).filter('deleted', True))
    logging.error("Please remove the Invoice.deleted property")
