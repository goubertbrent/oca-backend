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
from rogerthat.models import FriendMap
from rogerthat.rpc import users


def job():
    run_job(_qry, [], _worker, [])


def _qry():
    return FriendMap.all(keys_only=True)


def _worker(friend_map_key):
    def trans():
        updated = False
        friend_map = db.get(friend_map_key)
        for email in friend_map.friendDetails._table:
            user = users.User(email)
            if user not in friend_map.friends:
                friend_map.friends.append(user)
                updated = True
        if updated:
            friend_map.put()

    db.run_in_transaction(trans)
