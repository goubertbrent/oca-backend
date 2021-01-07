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
from rogerthat.utils.transactions import run_in_xg_transaction
from solutions.common.models.discussion_groups import SolutionDiscussionGroup


def job():
    run_job(_query, [], _worker, [], worker_queue=MIGRATION_QUEUE)
    
    
def _query():
    return SolutionDiscussionGroup.all(keys_only=True)


def _worker(dg_key):
    def trans():
        discussion_group = db.get(dg_key)
        if discussion_group.member_list:
            return
        if not discussion_group.members:
            logging.debug("data empty service_user:%s id:%s" % (discussion_group.service_user, discussion_group.id))
            raise Exception("migrate_discussiongroups failed")
        
        kv_store_dict = discussion_group.members.to_json_dict()
        discussion_group.members.clear()
        discussion_group.member_list = kv_store_dict['members']
        discussion_group.put()
    
    run_in_xg_transaction(trans)