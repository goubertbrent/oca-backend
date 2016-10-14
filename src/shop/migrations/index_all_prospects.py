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

from google.appengine.api import search
from google.appengine.ext import deferred

from shop.constants import PROSPECT_INDEX
from shop.models import Prospect


def job(cursor=None):
    qry = Prospect.all()
    if cursor:
        qry.with_cursor(cursor)

    prospects = qry.fetch(200)
    if not prospects:
        return
    to_put = list()
    index = search.Index(name=PROSPECT_INDEX)
    for prospect in prospects:
        try:
            index.delete(prospect.id)
        except ValueError:
            pass

        fields = [
            search.AtomField(name='key', value=prospect.id),
            search.TextField(name='name', value=prospect.name),
            search.TextField(name='address', value=prospect.address),
            search.TextField(name='phone', value=prospect.phone),
            search.TextField(name='email', value=prospect.email)
        ]
        doc = search.Document(doc_id=prospect.id, fields=fields)
        to_put.append(doc)

    index.put(to_put)
    deferred.defer(job, qry.cursor())
