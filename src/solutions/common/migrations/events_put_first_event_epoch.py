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

from rogerthat.bizz.job import run_job
from google.appengine.ext import db
from solutions.common.models.agenda import Event

def update_all_first_event_epoch_events():
        run_job(_get_all_events_query, [], _put_event, [])

def _get_all_events_query():
    qry = db.GqlQuery("SELECT __key__ FROM Event")
    return qry

def _put_event(event_key):
    def trans():
        event = Event.get(event_key)
        event.first_start_date = event.get_first_event_date()
        event.put()
    db.run_in_transaction(trans)
