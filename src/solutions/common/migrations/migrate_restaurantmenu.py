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
from solutions.common.models import RestaurantMenu


def job():
    run_job(_query, [], _worker, [], worker_queue=MIGRATION_QUEUE)


def _query():
    return RestaurantMenu.all(keys_only=True)


def _worker(menu_key):
    menu = db.get(menu_key)  # type: RestaurantMenu
    if menu.categories_json:
        return
    data = {}
    for c in menu.categories:
        if c.id:
            data[c.id] = c
        else:
            data[c.name] = c
    menu.save_categories(data)
    menu.categories = None
    menu.put()