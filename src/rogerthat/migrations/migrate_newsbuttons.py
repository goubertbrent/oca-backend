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
from google.appengine.ext import ndb
from typing import List

from rogerthat.bizz.job import run_job, MODE_BATCH
from rogerthat.consts import MIGRATION_QUEUE
from rogerthat.models.news import NewsItem, NewsButton


def job():
    run_job(_query, [], _worker, [], worker_queue=MIGRATION_QUEUE, mode=MODE_BATCH, batch_size=25)


def _query():
    return NewsItem.query()


@ndb.transactional(xg=True)
def _worker(keys):
    models = ndb.get_multi(keys)  # type: List[NewsItem]
    to_put = []
    for news_item in models:
        if news_item.actions:
            continue
        buttons = []
        if news_item.buttons:
            for old_btn in news_item.buttons:
                btn = NewsButton()
                btn.id = old_btn.id
                btn.caption = old_btn.caption
                btn.action = old_btn.action
                btn.flow_params = old_btn.flow_params
                btn.index = old_btn.index
                buttons.append(btn)
        news_item.actions = buttons
        news_item.buttons = None
        to_put.append(news_item)
    ndb.put_multi(to_put)
