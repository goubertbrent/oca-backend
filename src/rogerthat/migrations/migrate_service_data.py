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

import json

from google.appengine.ext import db

from rogerthat.bizz.job import run_job
from rogerthat.consts import MIGRATION_QUEUE
from rogerthat.models import ServiceIdentity
from rogerthat.utils.transactions import run_in_xg_transaction


def job():
    run_job(_query, [], _worker, [], worker_queue=MIGRATION_QUEUE)
    
    
def _query():
    return ServiceIdentity.all(keys_only=True)


def _worker(si_key):
    def trans():
        si = db.get(si_key)
        if si.appData:
            return
        if si.serviceData:
            data_dict = si.serviceData.to_json_dict()
            si.serviceData.clear()
        else:
            data_dict = {}

        for prop in ('solutionCalendars', 'solutionEvents', 'broadcast_target_audience', 'broadcast_types', 'timezoneOffset'):
            if prop in data_dict:
                del data_dict[prop]

        si.appData = json.dumps(data_dict)
        si.put()
    
    run_in_xg_transaction(trans)