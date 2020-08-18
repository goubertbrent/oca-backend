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

from google.appengine.ext import deferred, ndb

from rogerthat.consts import MIGRATION_QUEUE
from rogerthat.models.news import NewsItemActions, NewsSettingsUser, NewsSettingsUserService


def job(app_user):
    NewsSettingsUser.create_key(app_user).delete()
    deferred.defer(_cleanup_actions, app_user, _queue=MIGRATION_QUEUE)
    deferred.defer(_cleanup_user_services, app_user, _queue=MIGRATION_QUEUE)


def _delete_all(qry):
    # type: (ndb.Query) -> None
    start_cursor = None
    has_more = True
    deleted_count = 0
    while has_more:
        keys, start_cursor, has_more = qry.fetch_page(500, keys_only=True, start_cursor=start_cursor)
        deleted_count += len(keys)
        ndb.delete_multi(keys)
    logging.debug('Deleted %d %s items', deleted_count, qry.kind)


def _cleanup_actions(app_user):
    _delete_all(NewsItemActions.list_by_app_user(app_user))


def _cleanup_user_services(app_user):
    _delete_all(NewsSettingsUserService.list_by_app_user(app_user))
