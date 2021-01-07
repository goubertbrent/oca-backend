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

from rogerthat.bizz.job import run_job
from rogerthat.consts import MIGRATION_QUEUE
from rogerthat.models import FriendMap


def job():
    run_job(_query, [], _worker, [], worker_queue=MIGRATION_QUEUE)


def _query():
    return FriendMap.all(keys_only=True)


def _worker(friend_map_key):
    friend_map = db.get(friend_map_key)  # type: FriendMap
    if friend_map.friend_details_json:
        return
    data = {}
    for friend_detail in friend_map.friendDetails.values():
        data[friend_detail.email] = friend_detail
    friend_map.save_friend_details(data)
    friend_map.friendDetails = None
    friend_map.put()  