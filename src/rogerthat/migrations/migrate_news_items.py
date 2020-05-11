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

import logging

from google.appengine.ext import db, ndb, deferred

from rogerthat.bizz.job import run_job
from rogerthat.bizz.news import create_default_news_settings
from rogerthat.bizz.news.groups import setup_news_stream_app, get_group_info
from rogerthat.bizz.news.matching import create_matches_for_news_item_key
from rogerthat.bizz.news.searching import re_index_news_item_by_key
from rogerthat.consts import MIGRATION_QUEUE, NEWS_MATCHING_QUEUE
from rogerthat.dal.service import get_service_identities
from rogerthat.models import ServiceProfile, App
from rogerthat.models.news import NewsItem, NewsSettingsService
from rogerthat.rpc import users


def setup_news_stream():
    run_job(_query_all_apps, [], _setup_news_stream_worker, [], worker_queue=MIGRATION_QUEUE)


def _query_all_apps():
    return App.all(keys_only=True)


def _setup_news_stream_worker(app_key):
    app_id = app_key.name()
    setup_news_stream_app(app_id)


def setup_news_settings_service():
    run_job(_setup_news_settings_service_qry, [], _setup_news_settings_service_worker, [], worker_queue=MIGRATION_QUEUE)


def _setup_news_settings_service_qry():
    return ServiceProfile.all(keys_only=True)


def _setup_news_settings_service_worker(sp_key):
    sp = db.get(sp_key)
    create_default_news_settings(sp.service_user, sp.organizationType)


def migrate_all(dry_run=True, force=False):
    run_job(_query_all, [], _worker, [dry_run, force], worker_queue=MIGRATION_QUEUE)


def _query_all():
    return NewsItem.query()


def migrate_app_id(app_id, dry_run=True, force=False):
    run_job(_query_nss, [app_id], _worker_nss, [dry_run, force], worker_queue=MIGRATION_QUEUE)


def _query_nss(app_id):
    return NewsSettingsService.list_by_app_id(app_id)


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
        ni = ni_key.get()
        if ni.group_types and not force:
            return

        ni.group_types_ordered = group_types
        ni.group_types = group_types
        ni.group_ids = group_ids
        ni.put()

    ndb.transaction(trans)


def job_news_item_publish_time():
    run_job(_query_all, [], _worker_news_item_publish_time, [], worker_queue=MIGRATION_QUEUE)


def _worker_news_item_publish_time(ni_key):

    def trans():
        ni = ni_key.get()
        if ni.scheduled_at:
            ni.published_timestamp = ni.scheduled_at
        else:
            ni.published_timestamp = ni.timestamp
        ni.put()

    ndb.transaction(trans)


def add_app_id_to_news_items(service_user, app_id, create_matches=False, dry_run=True):
    service_identities = get_service_identities(service_user)
    for si in service_identities:
        run_job(_query_service, [si.service_identity_user], _worker_add_app_id_to_news_items, [app_id, create_matches, dry_run], worker_queue=MIGRATION_QUEUE)


def _worker_add_app_id_to_news_items(ni_key, app_id, create_matches=False, dry_run=True):
    ni = ni_key.get()
    if app_id in ni.app_ids:
        logging.debug('add_app_id_to_news_items already migrated news_id:%s', ni.id)
        return
    group_types, group_ids = get_group_info(ni.sender, news_item=ni, app_ids=[app_id])
    if dry_run:
        logging.debug('add_app_id_to_news_items news_id:%s group_types:%s group_ids:%s', ni.id, group_types, group_ids)
        return

    def trans():
        ni = ni_key.get()
        if app_id in ni.app_ids:
            return

        old_group_ids = [group_id for group_id in ni.group_ids]

        ni.group_ids = group_ids
        ni.app_ids.append(app_id)
        ni.put()

        if create_matches:
            deferred.defer(create_matches_for_news_item_key, ni_key, old_group_ids,
                           _transactional=True,
                           _queue=NEWS_MATCHING_QUEUE)
            deferred.defer(re_index_news_item_by_key, ni_key, _countdown=2,
                           _transactional=True,
                           _queue=NEWS_MATCHING_QUEUE)

    ndb.transaction(trans)
