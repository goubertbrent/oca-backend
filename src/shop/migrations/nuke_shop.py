# -*- coding: utf-8 -*-
# Copyright 2021 Green Valley NV
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
from google.appengine.ext import ndb

from rogerthat.migrations import delete_all_models_by_kind
from rogerthat.models import NdbModel


class AuditLog(NdbModel):
    pass


class RegioManagerTeam(NdbModel):
    pass


class RegioManagerStatistic(NdbModel):
    pass


class LegalEntity(NdbModel):
    pass


class Product(NdbModel):
    pass


class OrderNumber(NdbModel):
    pass


class ChargeNumber(NdbModel):
    pass


class InvoiceNumber(NdbModel):
    pass


class CreditCard(NdbModel):
    pass


class StructuredInfoSequence(NdbModel):
    pass


class Order(NdbModel):
    pass


class Charge(NdbModel):
    pass


def remove_models():
    del_all(OrderNumber)
    del_all(ChargeNumber)
    del_all(InvoiceNumber)
    del_all(CreditCard)
    del_all(StructuredInfoSequence)
    del_all(RegioManagerTeam)
    del_all(RegioManagerStatistic)
    del_all(LegalEntity)
    delete_all_models_by_kind.job(AuditLog, batch_size=200)
    delete_all_models_by_kind.job(Product, batch_size=200)
    delete_all_models_by_kind.job(Order, batch_size=100)
    delete_all_models_by_kind.job(Charge, batch_size=100)


def del_all(model):
    ndb.delete_multi(model.query().fetch(keys_only=True))
