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
from solutions.common.models import SolutionScheduledBroadcast
from rogerthat.models import ServiceIdentity


def job():
    run_job(_get_all_scheduled_broadcasts, [], _migrate, [])

def _get_all_scheduled_broadcasts():
    return SolutionScheduledBroadcast.all(keys_only=True)

def _migrate(ssb_key):
    def trans():
        ssb = db.get(ssb_key)
        if ssb.statistics_key:
            ssb.statistics_keys = [ssb.statistics_key]
            ssb.identities = [ServiceIdentity.DEFAULT]
            ssb.put()
    db.run_in_transaction(trans)
