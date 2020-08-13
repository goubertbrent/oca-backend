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

import logging

from rogerthat.bizz.job import run_job
from rogerthat.bizz.news.searching import re_index_news_item
from rogerthat.consts import MIGRATION_QUEUE
from rogerthat.dal.profile import get_service_visible
from rogerthat.models.news import NewsItem, NewsItemMatch, NewsItemActions

    
def migrate_all_news_items(dry_run=True):
    run_job(_query_all_news_items, [], _worker_all_news_items, [dry_run], worker_queue=MIGRATION_QUEUE)
    
    
def _query_all_news_items():
    return NewsItem.query()


def _worker_all_news_items(ni_key, dry_run=True):
    news_item = ni_key.get()  # type: NewsItem
    if news_item.deleted:
        news_item.status = NewsItem.STATUS_DELETED
    elif news_item.published:
        visible = get_service_visible(news_item.sender)
        if visible:
            news_item.status = NewsItem.STATUS_PUBLISHED
        else:
            news_item.status = NewsItem.STATUS_INVISIBLE
    else:
        news_item.status = NewsItem.STATUS_SCHEDULED
    if dry_run:
        logging.debug('migrate_all_news_items dry_run news_id:%s status:%s', news_item.id, news_item.status)
        return
    news_item.put()
    if news_item.status == NewsItem.STATUS_PUBLISHED:
        re_index_news_item(news_item)


def migrate_news_matches(dry_run=True):
    run_job(_query_matches, [], worker_matches, [dry_run], worker_queue=MIGRATION_QUEUE)


def _query_matches():
    return NewsItemMatch.query()


def worker_matches(m_key, dry_run=True):
    news_item_match = m_key.get()
    if not news_item_match.actions:
        if not news_item_match.disabled:
            if dry_run:
                logging.debug('migrate_news_matches dry_run nothing to save news_id:%s', news_item_match.news_id)
            return

    news_item_actions = NewsItemActions.create(news_item_match.app_user, news_item_match.news_id, news_item_match.publish_time)
    for action in news_item_match.actions:
        news_item_actions.add_action(action)
    news_item_actions.disabled = news_item_match.disabled
    if dry_run:
        logging.debug('migrate_news_matches dry_run news_id:%s actions:%s disabled:%s', news_item_match.news_id, news_item_actions.actions, news_item_actions.disabled)
        return
    news_item_actions.put()