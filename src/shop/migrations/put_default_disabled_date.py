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
from google.appengine.ext.deferred import deferred

from rogerthat.consts import MIGRATION_QUEUE
from shop.models import Customer


def job():
    deferred.defer(_put_customers, _queue=MIGRATION_QUEUE)


def _put_customers(cursor=None):
    qry = Customer.all()
    if cursor:
        qry.with_cursor(cursor)

    customers = qry.fetch(200)
    if not customers:
        return
    cursor = qry.cursor()
    to_put = list()
    for c in customers:
        if c.service_disabled_at == 0:
            c.service_disabled_at = 0
            to_put.append(c)
    db.put(to_put)
    _put_customers(cursor)
