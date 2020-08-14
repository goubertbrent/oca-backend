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

from google.appengine.ext import deferred, ndb

from rogerthat.consts import MIGRATION_QUEUE
from rogerthat.models.news import NewsItemMatch, NewsSettingsUser, \
    NewsSettingsUserService, NewsItemActions


def job(app_user):
    NewsSettingsUser.create_key(app_user).delete()
    deferred.defer(_cleanup_matches, app_user, _queue=MIGRATION_QUEUE)
    deferred.defer(_cleanup_actions, app_user, _queue=MIGRATION_QUEUE)
    deferred.defer(_cleanup_user_services, app_user, _queue=MIGRATION_QUEUE)


def _cleanup_actions(app_user):
    batch_count = 200
    qry = NewsItemActions.list_by_app_user(app_user)
    items, _, has_more = qry.fetch_page(batch_count, keys_only=True)

    if items:
        ndb.delete_multi(items)

    if has_more:
        deferred.defer(_cleanup_actions, app_user, _countdown=2, _queue=MIGRATION_QUEUE)


def _cleanup_matches(app_user):
    batch_count = 200
    qry = NewsItemMatch.list_by_app_user(app_user)
    items, _, has_more = qry.fetch_page(batch_count, keys_only=True)

    if items:
        ndb.delete_multi(items)

    if has_more:
        deferred.defer(_cleanup_matches, app_user, _countdown=2, _queue=MIGRATION_QUEUE)


def _cleanup_user_services(app_user):
    batch_count = 200
    qry = NewsSettingsUserService.list_by_app_user(app_user)
    items, _, has_more = qry.fetch_page(batch_count, keys_only=True)

    if items:
        ndb.delete_multi(items)

    if has_more:
        deferred.defer(_cleanup_user_services, app_user, _countdown=2, _queue=MIGRATION_QUEUE)
