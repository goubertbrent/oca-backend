# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
# NOTICE: THIS FILE HAS BEEN MODIFIED BY GREEN VALLEY BELGIUM NV IN ACCORDANCE WITH THE APACHE LICENSE VERSION 2.0
# Copyright 2018 GIG Technology NV
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
# @@license_version:1.6@@

from rogerthat.bizz.friends import update_friend_set_response
from rogerthat.bizz.job import run_job
from rogerthat.capi.friends import updateFriendSet
from rogerthat.dal.friend import get_friends_map
from rogerthat.models import UserProfile
from rogerthat.rpc import users
from rogerthat.rpc.rpc import logError
from rogerthat.to.friends import UpdateFriendSetRequestTO
from rogerthat.utils.app import remove_app_id


def job(app_id):
    run_job(_qry, [app_id], _worker, [])


def _qry(app_id):
    return UserProfile.all(keys_only=True).filter('app_id', app_id)


def _worker(user_profile_key):
    app_user = users.User(user_profile_key.name())
    friend_map = get_friends_map(app_user)
    request = UpdateFriendSetRequestTO()
    request.friends = [remove_app_id(users.User(f.email)).email() for f in friend_map.friendDetails]
    request.version = friend_map.version
    request.added_friend = None
    updateFriendSet(update_friend_set_response, logError, app_user, request=request)
