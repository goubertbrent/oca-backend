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

from google.appengine.ext import ndb, deferred

from rogerthat.bizz.job import run_job
from rogerthat.bizz.news.groups import get_group_info
from rogerthat.bizz.news.searching import re_index_news_item_by_key
from rogerthat.consts import MIGRATION_QUEUE, NEWS_MATCHING_QUEUE
from rogerthat.dal.service import get_service_identities
from rogerthat.models.news import NewsItem, NewsSettingsService
from rogerthat.rpc import users


def migrate_community_id(community_id, dry_run=True, force=False):
    run_job(_query_nss, [community_id], _worker_nss, [dry_run, force], worker_queue=MIGRATION_QUEUE)


def _query_nss(community_id):
    return NewsSettingsService.list_by_community(community_id)


def _worker_nss(nss_key, dry_run=True, force=False):
    service_user = users.User(nss_key.parent().id().decode('utf8'))
    migrate_service(service_user, dry_run, force)


def migrate_service(service_user, dry_run=True, force=False):
    service_identities = get_service_identities(service_user)
    for si in service_identities:
        run_job(_query_service, [si.service_identity_user], _worker, [dry_run, force], worker_queue=MIGRATION_QUEUE)


def _query_service(service_identity_user):
    return NewsItem.list_by_sender(service_identity_user)


def _worker(ni_key, dry_run=True, force=False):
    # type: (ndb.Key, bool, bool) -> None
    news_item = ni_key.get()  # type: NewsItem
    if news_item.group_types and not force:
        logging.debug('migrate_news_items already migrated news_id:%s', news_item.id)
        return

    group_types, group_ids = get_group_info(news_item.sender, news_item=news_item)
    if dry_run:
        logging.debug('migrate_news_items dry_run news_id:%s', news_item.id)
        return
    logging.debug('migrate_news_items saving news_id:%s', news_item.id)

    def trans():
        ni = ni_key.get()  # type: NewsItem
        if ni.group_types and not force:
            return

        ni.group_types_ordered = group_types
        ni.group_types = group_types
        ni.group_ids = group_ids
        ni.put()

    ndb.transaction(trans)


def add_community_id_to_news_items(service_user, community_id, dry_run=True):
    service_identities = get_service_identities(service_user)
    for si in service_identities:
        run_job(_query_service, [si.service_identity_user], _worker_add_community_id_to_news_items, [community_id, dry_run], worker_queue=MIGRATION_QUEUE)


def _worker_add_community_id_to_news_items(ni_key, community_id, dry_run=True):
    ni = ni_key.get()
    if community_id in ni.community_ids:
        logging.debug('add_community_id_to_news_items already migrated news_id:%s', ni.id)
        return
    group_types, group_ids = get_group_info(ni.sender, news_item=ni, community_ids=[community_id])
    if dry_run:
        logging.debug('add_community_id_to_news_items news_id:%s group_types:%s group_ids:%s', ni.id, group_types, group_ids)
        return

    def trans():
        ni = ni_key.get()
        if community_id in ni.community_ids:
            return

        ni.group_ids = group_ids
        ni.community_ids.append(community_id)
        ni.put()

        deferred.defer(re_index_news_item_by_key, ni_key, _countdown=2,
                       _transactional=True,
                       _queue=NEWS_MATCHING_QUEUE)

    ndb.transaction(trans)