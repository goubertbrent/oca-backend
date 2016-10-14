# -*- coding: utf-8 -*-
# Copyright 2016 Mobicage NV
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
# @@license_version:1.1@@

from google.appengine.ext.deferred import deferred, db

from rogerthat.consts import MIGRATION_QUEUE
from rogerthat.utils import now
from mcfw.utils import chunks
from shop.dal import get_mobicage_legal_entity
from shop.models import Invoice, RegioManager, RegioManagerTeam
from shop.products import add_all_products


def job():
    add_all_products()
    set_default_legal_entity_to_teams()
    deferred.defer(put_invoices, _queue=MIGRATION_QUEUE)


def set_default_legal_entity_to_teams():
    mobicage_legal_entity_id = get_mobicage_legal_entity().id
    to_put = list()
    for team in RegioManagerTeam.all():
        if not team.legal_entity_id:
            team.legal_entity_id = mobicage_legal_entity_id
        team.is_mobicage = team.name == 'Mobicage'
        to_put.append(team)
    db.put(to_put)


def put_invoices():
    all_invoices = list(Invoice.all())
    mobicage_legal_entity_id = get_mobicage_legal_entity()
    for invoices in chunks(all_invoices, 200):
        to_put = list()
        for i in invoices:
            manager = i.operator and RegioManager.get(RegioManager.create_key(i.operator.email()))
            i.legal_entity_id = manager and manager.team.legal_entity_id or mobicage_legal_entity_id.id
            if i.paid and i.paid_timestamp is None:
                i.paid_timestamp = 0 if i.legal_entity_id == mobicage_legal_entity_id.id else now()
            to_put.append(i)
        db.put(invoices)
