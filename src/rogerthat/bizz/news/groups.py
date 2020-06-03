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
from datetime import datetime

from google.appengine.ext import ndb, deferred
from typing import List, Tuple, Optional

from mcfw.properties import azzert
from mcfw.rpc import returns, arguments
from rogerthat.bizz.job import run_job
from rogerthat.bizz.service import InvalidGroupTypeException
from rogerthat.consts import MIGRATION_QUEUE, NEWS_MATCHING_QUEUE, DEBUG
from rogerthat.dal.app import get_app_by_id
from rogerthat.dal.service import get_service_identity
from rogerthat.models import App
from rogerthat.models.news import NewsGroup, NewsSettingsService, NewsStream, \
    NewsGroupTile, NewsStreamLayout, NewsSettingsUser, NewsSettingsUserGroup, \
    NewsSettingsUserGroupDetails, NewsNotificationFilter, NewsStreamCustomLayout, NewsItem
from rogerthat.rpc import users
from rogerthat.to.news import ServiceNewsGroupTO
from rogerthat.utils import guid
from rogerthat.utils.service import get_service_user_from_service_identity_user


def setup_news_stream_app(app_id, news_stream=None):
    ns_key = NewsStream.create_key(app_id)
    if ns_key.get():
        return
    ns = NewsStream(key=ns_key)
    ns.stream_type = news_stream.type if news_stream else None
    ns.should_create_groups = True
    ns.services_need_setup = False

    ns.layout = []
    for types in ([NewsGroup.TYPE_CITY], [NewsGroup.TYPE_PRESS, NewsGroup.TYPE_TRAFFIC], [NewsGroup.TYPE_PROMOTIONS]):
        ns.layout.append(NewsStreamLayout(group_types=types))

    custom_layout_polls = NewsStreamCustomLayout(key=NewsStreamCustomLayout.create_key(NewsGroup.TYPE_POLLS, app_id))
    custom_layout_polls.layout = []
    for types in ([NewsGroup.TYPE_CITY], [NewsGroup.TYPE_POLLS, NewsGroup.TYPE_TRAFFIC], [NewsGroup.TYPE_PROMOTIONS], [NewsGroup.TYPE_PRESS]):
        custom_layout_polls.layout.append(NewsStreamLayout(group_types=types))

    ndb.put_multi([ns, custom_layout_polls])

    if news_stream:
        deferred.defer(setup_default_groups_app, app_id)


def setup_default_groups_app(app_id):
    ns = NewsStream.create_key(app_id).get()
    if not ns:
        return
    if not ns.stream_type:
        return
    if not ns.should_create_groups:
        return
    if ns.stream_type not in (NewsStream.TYPE_CITY, NewsStream.TYPE_COMMUNITY):
        return

    ns.should_create_groups = False
    to_put = [ns]

    app = get_app_by_id(app_id)

    ng1 = NewsGroup(key=NewsGroup.create_key(guid()))
    ng1.name = u'%s CITY' % app.name
    ng1.app_id = app.app_id
    ng1.group_type = NewsGroup.TYPE_CITY
    ng1.filters = []
    ng1.regional = False
    ng1.default_order = 10
    ng1.default_notifications_enabled = True
    ng1.tile = NewsGroupTile(
        background_image_url=u'https://storage.googleapis.com/oca-files/news/groups/_default/city.jpg')

    ng2 = NewsGroup(key=NewsGroup.create_key(guid()))
    ng2.name = u'%s PROMOTIONS' % app.name
    ng2.app_id = app.app_id
    ng2.group_type = NewsGroup.TYPE_PROMOTIONS
    ng2.filters = NewsGroup.PROMOTIONS_FILTERS
    ng2.regional = False
    ng2.default_order = 20
    ng2.default_notifications_enabled = False
    ng2.tile = NewsGroupTile(
        background_image_url=u'https://storage.googleapis.com/oca-files/news/groups/_default/promo.jpg')

    ng3 = NewsGroup(key=NewsGroup.create_key(guid()))
    ng3.name = u'%s PROMOTIONS (regional)' % app.name
    ng3.app_id = app.app_id
    ng3.group_type = NewsGroup.TYPE_PROMOTIONS
    ng3.filters = NewsGroup.PROMOTIONS_FILTERS
    ng3.regional = True
    ng3.default_order = 20
    ng3.default_notifications_enabled = False
    ng3.tile = None

    ng4 = NewsGroup(key=NewsGroup.create_key(guid()))
    ng4.name = u'%s EVENTS' % app.name
    ng4.app_id = app.app_id
    ng4.group_type = NewsGroup.TYPE_EVENTS
    ng4.filters = []
    ng4.regional = False
    ng4.default_order = 30
    ng4.default_notifications_enabled = False
    ng4.tile = NewsGroupTile(
        background_image_url=u'https://storage.googleapis.com/oca-files/news/groups/_default/events.jpg')

    ng5 = NewsGroup(key=NewsGroup.create_key(guid()))
    ng5.name = u'%s TRAFFIC' % app.name
    ng5.app_id = app.app_id
    ng5.group_type = NewsGroup.TYPE_TRAFFIC
    ng5.filters = []
    ng5.regional = False
    ng5.default_order = 40
    ng5.default_notifications_enabled = True
    ng5.tile = NewsGroupTile(
        background_image_url=u'https://storage.googleapis.com/oca-files/news/groups/_default/trafic.jpg')

    ng6 = NewsGroup(key=NewsGroup.create_key(guid()))
    ng6.name = u'%s PRESS' % app.name
    ng6.app_id = app.app_id
    ng6.group_type = NewsGroup.TYPE_PRESS
    ng6.filters = []
    ng6.regional = False
    ng6.default_order = 50
    ng6.default_notifications_enabled = False
    ng6.tile = NewsGroupTile(
        background_image_url=u'https://storage.googleapis.com/oca-files/news/groups/_default/press.jpg')
    ng6.service_filter = True

    ng7 = NewsGroup(key=NewsGroup.create_key(guid()))
    ng7.name = u'%s POLLS' % app.name
    ng7.app_id = app.app_id
    ng7.send_notifications = False
    ng7.group_type = NewsGroup.TYPE_POLLS
    ng7.filters = []
    ng7.regional = False
    ng7.default_order = 60
    ng7.default_notifications_enabled = True
    ng7.tile = NewsGroupTile(background_image_url=u'https://storage.googleapis.com/oca-files/news/groups/_default/polls.jpg',
                             promo_image_url=u'https://storage.googleapis.com/oca-files/news/groups/_default/polls_promo.png')

    to_put.extend([ng1, ng2, ng3, ng4, ng5, ng6, ng7])

    ndb.put_multi(to_put)


def get_group_id_for_type_and_app_id(group_type, app_id, regional=False):
    logging.debug('debugging_news get_group_id_for_type_and_app_id type:%s app_id:%s regional:%s',
                  group_type, app_id, regional)
    for g in get_groups_for_app_id(app_id).get(group_type, []):
        if g.regional == regional:
            return g.group_id
    return None


def get_groups_for_app_id(app_id):
    d = {}
    for g in NewsGroup.list_by_app_id(app_id):
        if g.group_type not in d:
            d[g.group_type] = []
        d[g.group_type].append(g)
    return d


def get_group_types_for_service(news_settings, group_types):
    # type: (NewsSettingsService, List[str]) -> List[str]
    if not group_types:
        group_types = [news_settings.groups[0].group_type] if news_settings.groups else []

    if news_settings.duplicate_in_city_news:
        if NewsGroup.TYPE_CITY not in group_types and NewsGroup.TYPE_CITY in news_settings.get_group_types():
            group_types.append(NewsGroup.TYPE_CITY)

    return group_types


def get_group_ids_for_type(group_type, default_app_id, app_ids):
    group_ids = []
    skipped_app_ids = [App.APP_ID_ROGERTHAT, App.APP_ID_OSA_LOYALTY]
    for app_id in app_ids:
        if app_id in skipped_app_ids:
            # Keep everything on devserver
            if not DEBUG:
                continue
        regional = app_id != default_app_id if group_type == NewsGroup.TYPE_PROMOTIONS else False
        group_id = get_group_id_for_type_and_app_id(group_type, app_id, regional)
        if not group_id:
            raise Exception('Failed to get group_id for group_type:%s app_id:%s regional:%s' %
                            (group_type, app_id, regional))
        group_ids.append(group_id)
    return group_ids


def get_group_info(service_identity_user, group_type=None, app_ids=None, news_item=None):
    # type: (users.User, Optional[str], List[str], Optional[NewsItem]) -> Tuple[List[str], List[str]]
    service_user = get_service_user_from_service_identity_user(service_identity_user)
    news_settings = NewsSettingsService.create_key(service_user).get()  # type: Optional[NewsSettingsService]
    if not news_settings or not news_settings.default_app_id:
        return [], []

    check_group_types = []
    check_app_ids = set()

    if news_item:
        if group_type:
            check_group_types = [group_type]
        else:
            if news_item.group_types_ordered:
                check_group_types = news_item.group_types_ordered
            else:
                check_group_types = news_item.group_types
        check_app_ids = set(news_item.app_ids)
        if app_ids:
            check_app_ids.update(app_ids)

    else:
        if group_type:
            check_group_types = [group_type]
        if app_ids:
            check_app_ids = set(app_ids)

    logging.debug('debugging_news get_group_info check_group_types:%s check_app_ids:%s', check_group_types, check_app_ids)
    if not check_app_ids or not check_group_types:
        return [], []

    group_types = get_group_types_for_service(news_settings, check_group_types)
    logging.debug('debugging_news get_group_info group_types:%s', group_types)
    if not group_types:
        return [], []

    si = get_service_identity(service_identity_user)
    group_ids = []
    for gt in group_types:
        if gt in (NewsGroup.TYPE_CITY, NewsGroup.TYPE_PROMOTIONS, NewsGroup.TYPE_PRESS, NewsGroup.TYPE_PUBLIC_SERVICE_ANNOUNCEMENTS):
            app_ids = []
            for app_id in check_app_ids:
                # TODO refactor: datastore.get in nested for loop
                ns = NewsStream.create_key(app_id).get()
                if ns and not ns.should_create_groups:
                    app_ids.append(app_id)
        else:
            app_ids = [si.app_id]
        # TODO refactor: datastore.query in for loop
        group_ids.extend(get_group_ids_for_type(gt, si.app_id, app_ids))

    logging.debug('debugging_news get_group_info group_ids:%s', group_ids)
    return group_types, group_ids


@ndb.non_transactional()
@returns()
@arguments(service_user=users.User, group_type=unicode)
def validate_group_type(service_user, group_type):
    nss = NewsSettingsService.create_key(service_user).get()
    if not nss:
        raise InvalidGroupTypeException(group_type)

    group_types = nss.get_group_types()
    if group_type not in group_types:
        raise InvalidGroupTypeException(group_type)


def get_groups_for_service_user(service_user, language=None):
    from rogerthat.bizz.news import get_group_title

    nss = NewsSettingsService.create_key(service_user).get()
    if not nss:
        return []

    group_types = nss.get_group_types()
    if not group_types:
        return []

    groups = []
    for ng in NewsGroup.list_by_app_id(nss.default_app_id):
        if ng.group_type not in group_types:
            continue
        if ng.regional:
            continue
        groups.append(ng)

    if not groups:
        return []

    news_stream = NewsStream.create_key(nss.default_app_id).get()
    type_city = False
    if news_stream and news_stream.stream_type == NewsStream.TYPE_CITY:
        type_city = True

    l = []
    for ng in groups:
        l.append(ServiceNewsGroupTO(group_type=ng.group_type,
                                    name=get_group_title(type_city, ng, language)))
    return l


def update_stream_layout(group_ids, layout_id, visible_until):
    news_groups = ndb.get_multi([NewsGroup.create_key(group_id) for group_id in group_ids])
    for ng in news_groups:
        if ng.regional:
            continue
        if ng.group_type == layout_id:
            break
    else:
        return

    if not ng.visible_until or ng.visible_until < visible_until:
        ng.visible_until = visible_until
    ng.send_notifications = True
    ng.put()

    news_stream = NewsStream.create_key(ng.app_id).get()
    if news_stream.custom_layout_id == layout_id:
        return

    custom_layout = NewsStreamCustomLayout.create_key(layout_id, ng.app_id).get()
    if not custom_layout:
        return
    news_stream.custom_layout_id = layout_id
    news_stream.put()


def add_user_group(group_id):
    g = NewsGroup.create_key(group_id).get()
    run_job(_qry_user_settings_app, [g.app_id], _worker_add_group_to_user_settings,
            [group_id], worker_queue=MIGRATION_QUEUE)


def delete_user_group(app_id, group_id):
    run_job(_qry_user_settings_app, [app_id], _worker_delete_group_from_user_settings,
            [group_id], worker_queue=MIGRATION_QUEUE)


def _qry_user_settings_app(app_id):
    return NewsSettingsUser.list_by_app_id(app_id)


@ndb.non_transactional()
def _get_news_group(group_id):
    return NewsGroup.create_key(group_id).get()


@ndb.transactional(xg=True)
def _worker_add_group_to_user_settings(s_key, group_id):
    from rogerthat.bizz.news.matching import create_matches_for_user
    s = s_key.get()
    if group_id in s.group_ids:
        return

    g = _get_news_group(group_id)

    ug = NewsSettingsUserGroup()
    ug.group_type = g.group_type
    ug.order = g.default_order
    ug.details = []
    ugd = NewsSettingsUserGroupDetails()
    ugd.group_id = g.group_id
    ugd.order = 20 if g.regional else 10
    ugd.filters = g.filters
    if g.default_notifications_enabled:
        ugd.notifications = NewsNotificationFilter.ALL
    else:
        ugd.notifications = NewsNotificationFilter.SPECIFIED

    ugd.last_load_request = datetime.utcnow()

    ug.details.append(ugd)

    s.group_ids.append(g.group_id)
    s.groups.append(ug)
    s.put()

    deferred.defer(create_matches_for_user, s.app_user, group_id, _transactional=True, _queue=NEWS_MATCHING_QUEUE)


@ndb.transactional(xg=True)
def _worker_delete_group_from_user_settings(s_key, group_id):
    from rogerthat.bizz.news.matching import delete_matches_for_user
    s = s_key.get()
    if group_id not in s.group_ids:
        return

    s.group_ids.remove(group_id)
    g = s.get_group(group_id)
    azzert(len(g.details) == 1)
    s.groups.remove(g)
    s.put()

    deferred.defer(delete_matches_for_user, s.app_user, group_id, _transactional=True, _queue=NEWS_MATCHING_QUEUE)


def delete_service_group(app_id, group_type):
    run_job(_qry_delete_service_group, [app_id], _worker_delete_service_group,
            [group_type], worker_queue=MIGRATION_QUEUE)


def _qry_delete_service_group(app_id):
    return NewsSettingsService.list_by_app_id(app_id)


@ndb.transactional(xg=True)
def _worker_delete_service_group(nss_key, group_type):
    nss = nss_key.get()
    g = nss.get_group(group_type)
    if not g:
        return
    nss.groups.remove(g)
    nss.put()


def update_notifications_user_group(group_id, notifications):
    run_job(_qry_update_notifications_user_group, [group_id],
            _worker_update_notifications_user_group, [group_id, notifications], worker_queue=MIGRATION_QUEUE)


def _qry_update_notifications_user_group(group_id):
    return NewsSettingsUser.list_by_group_id(group_id)


@ndb.transactional()
@returns()
@arguments(news_settings_user_key=ndb.Key, group_id=unicode, notifications=(int, long))
def _worker_update_notifications_user_group(news_settings_user_key, group_id, notifications):
    news_settings_user = news_settings_user_key.get()
    if not news_settings_user:
        return
    group_details = news_settings_user.get_group_details(group_id)
    if not group_details:
        return
    group_details.notifications = notifications
    news_settings_user.put()
