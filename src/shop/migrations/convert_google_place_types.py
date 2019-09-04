# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
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

from google.appengine.ext import db
from google.appengine.ext.deferred import deferred

from shop.models import Prospect


def job(cursor=None):
    qry = Prospect.all()
    if cursor:
        qry.with_cursor(cursor)

    prospects = qry.fetch(200)
    if not prospects:
        return

    for p in prospects:
        if p.status == Prospect.STATUS_ADDED_BY_DISCOVERY:
            p.categories = ['unclassified']
        else:
            p.categories = Prospect.convert_place_types(p.type)

    db.put(prospects)

    deferred.defer(job, qry.cursor())
