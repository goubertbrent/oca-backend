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

from google.appengine.ext import db

from rogerthat.bizz.job import run_job, MODE_BATCH
from rogerthat.consts import MIGRATION_QUEUE
from rogerthat.models import UserProfile, FacebookUserProfile


def job():
    run_job(_query_up, [], _worker, [], worker_queue=MIGRATION_QUEUE, mode=MODE_BATCH, batch_size=25)
    run_job(_query_fup, [], _worker, [], worker_queue=MIGRATION_QUEUE, mode=MODE_BATCH, batch_size=25)


def _query_up():
    return UserProfile.all(keys_only=True)

def _query_fup():
    return FacebookUserProfile.all(keys_only=True)


def _worker(up_keys):
    ups = db.get(up_keys)
    to_put = []
    for up in ups:
        if up.mobiles_json:
            continue
        data = {}
        if up.mobiles:
            for md in up.mobiles.values():
                data[md.account] = md
        up.save_mobiles(data)
        up.mobiles = None
        to_put.append(up)
    if to_put:
        db.put(to_put)