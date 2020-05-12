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

from google.appengine.api import search
from google.appengine.ext import deferred

from rogerthat.bizz.job import run_job
from rogerthat.bizz.profile import _re_index, USER_INDEX
from rogerthat.consts import MIGRATION_QUEUE
from rogerthat.models import UserProfile
from rogerthat.rpc import users
from rogerthat.utils import drop_index


def job(queue=MIGRATION_QUEUE):
    usr_index = search.Index(name=USER_INDEX)

    drop_index(usr_index)

    run_job(query, [], worker, [queue], worker_queue=queue)


def worker(up_key, queue):
    deferred.defer(_re_index, users.User(up_key.parent().name()), _queue=queue)


def query():
    return UserProfile.all(keys_only=True)
