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
import logging

from google.appengine.ext import db

from rogerthat.bizz.job import run_job
from rogerthat.consts import MIGRATION_QUEUE
from rogerthat.models import UserData
from rogerthat.utils.transactions import run_in_xg_transaction


def job():
    run_job(_query, [], _worker, [], worker_queue=MIGRATION_QUEUE)
    
    
def _query():
    return UserData.all(keys_only=True)


def _worker(user_data_key):
    def trans():
        user_data = db.get(user_data_key)
        if user_data.data:
            return
        if not user_data.userData:
            logging.debug("data empty app_user:%s service_identity_user:%s" % (user_data.app_user, user_data.service_identity_user))
            raise Exception("migrate_user_data failed")
        
        data_dict = user_data.userData.to_json_dict()
        user_data.userData.clear()
        user_data.data = json.dumps(data_dict)
        user_data.put()
    
    run_in_xg_transaction(trans)