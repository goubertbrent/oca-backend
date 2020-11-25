# -*- coding: utf-8 -*-
# Copyright 2020 Green Valley NV
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

from rogerthat.bizz.job import run_job
from shop.constants import MAPS_QUEUE
from solutions.common.bizz.events.events_search import re_index_all_events
from solutions.common.cron.events.uitdatabank import _get_uitdatabank_enabled_query, _process_cityapp_uitdatabank_events
from solutions.common.models.agenda import Event
from solutions.common.models.cityapp import UitdatabankSettings


def reset_uit_events(dry_run=True):
    to_delete = Event.query().filter(Event.source == Event.SOURCE_UITDATABANK_BE).fetch(keys_only=True)
    if not dry_run:
        ndb.delete_multi(to_delete)
    to_put = []
    for uit_settings in UitdatabankSettings.query():  # type: UitdatabankSettings
        uit_settings.cron_sync_time = 0
        uit_settings.cron_run_time = 0
        to_put.append(uit_settings)
    if not dry_run:
        ndb.put_multi(to_put)
        re_index_all_events()
    return len(to_delete), len(to_put)


def run_resync():
    run_job(_get_uitdatabank_enabled_query, [],
            _process_cityapp_uitdatabank_events, [1], worker_queue=MAPS_QUEUE)
