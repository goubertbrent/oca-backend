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

from rogerthat.bizz.job import run_job
from shop.models import Charge, Invoice


def job():
    run_job(_all_charges, [], set_invoice_number, [])


def _all_charges():
    return Charge.all()


def _get_invoice_number(charge):
    invoices = list(Invoice.all(keys_only=True).ancestor(charge))
    if len(invoices) == 1:
        return invoices[0].name()
    elif len(invoices) == 0:
        return ""
    else:
        from shop.bizz import PaymentFailedException
        raise PaymentFailedException("Found multiple invoices for charge %r!" % charge.key())


def set_invoice_number(charge):
    charge.invoice_number = _get_invoice_number(charge)
    charge.put()
