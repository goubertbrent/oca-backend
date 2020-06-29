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

from google.appengine.ext import db, deferred

from rogerthat.dal.service import get_service_api_callback_records_query


def run(timestamp, service_user, cursor=None):
    query = get_service_api_callback_records_query(service_user)
    query.with_cursor(cursor)
    records = query.fetch(100)

    put = list()
    for rec in records:
        rec.timestamp = timestamp
        rec.retryCount = 0
        put.append(rec)
    db.put(put)

    if len(records) > 0:
        return deferred.defer(run, timestamp, service_user, query.cursor(), _transactional=db.is_in_transaction())
