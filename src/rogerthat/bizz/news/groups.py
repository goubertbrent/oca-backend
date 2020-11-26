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
from collections import defaultdict

from google.appengine.ext import ndb, deferred
from typing import Optional, List, Tuple

from mcfw.rpc import returns, arguments
from rogerthat.bizz.communities.communities import get_community
from rogerthat.bizz.job import run_job, MODE_BATCH
from rogerthat.bizz.service import InvalidGroupTypeException
from rogerthat.consts import MIGRATION_QUEUE
from rogerthat.dal.profile import get_service_profile
from rogerthat.models.news import NewsGroup, NewsSettingsService, NewsStream, \
    NewsGroupTile, NewsStreamLayout, NewsSettingsUser, NewsStreamCustomLayout, NewsItem
from rogerthat.rpc import users
from rogerthat.to.news import ServiceNewsGroupTO
from rogerthat.utils import guid
from rogerthat.utils.service import get_service_user_from_service_identity_user


def setup_news_stream_community(community_id):
    ns_key = NewsStream.create_key(community_id)
    if ns_key.get():
        logging.debug('NewsStream already exists for community %s, doing nothing', community_id)
        return
    ns = NewsStream(key=ns_key)
    ns.stream_type = NewsStream.TYPE_CITY
    ns.should_create_groups = True
    ns.services_need_setup = False

    ns.layout = []
    for types in ([NewsGroup.TYPE_CITY], [NewsGroup.TYPE_PRESS, NewsGroup.TYPE_TRAFFIC], [NewsGroup.TYPE_PROMOTIONS]):
        ns.layout.append(NewsStreamLayout(group_types=types))

    custom_layout_polls = NewsStreamCustomLayout(
        key=NewsStreamCustomLayout.create_key(NewsGroup.TYPE_POLLS, community_id))
    custom_layout_polls.layout = []
    for types in ([NewsGroup.TYPE_CITY], [NewsGroup.TYPE_POLLS, NewsGroup.TYPE_TRAFFIC], [NewsGroup.TYPE_PROMOTIONS],
                  [NewsGroup.TYPE_PRESS]):
        custom_layout_polls.layout.append(NewsStreamLayout(group_types=types))

    ndb.put_multi([ns, custom_layout_polls])
    deferred.defer(setup_default_groups_community, community_id)


def setup_default_groups_community(community_id):
    ns = NewsStream.create_key(community_id).get()
    if not ns or not ns.should_create_groups or ns.stream_type not in (NewsStream.TYPE_CITY, NewsStream.TYPE_COMMUNITY):
        return

    ns.should_create_groups = False
    
    community = get_community(community_id)

    ng1 = NewsGroup(key=NewsGroup.create_key(guid()))
    ng1.name = u'%s CITY' % community.name
    ng1.community_id = community_id
    ng1.group_type = NewsGroup.TYPE_CITY
    ng1.regional = False
    ng1.default_order = 10
    ng1.default_notifications_enabled = True
    ng1.tile = NewsGroupTile(
        background_image_url=u'https://storage.googleapis.com/oca-files/news/groups/_default/city.jpg')

    ng2 = NewsGroup(key=NewsGroup.create_key(guid()))
    ng2.name = u'%s PROMOTIONS' % community.name
    ng2.community_id = community_id
    ng2.group_type = NewsGroup.TYPE_PROMOTIONS
    ng2.regional = False
    ng2.default_order = 20
    ng2.default_notifications_enabled = False
    ng2.tile = NewsGroupTile(
        background_image_url=u'https://storage.googleapis.com/oca-files/news/groups/_default/promo.jpg')

    ng3 = NewsGroup(key=NewsGroup.create_key(guid()))
    ng3.name = u'%s PROMOTIONS (regional)' % community.name
    ng3.community_id = community_id
    ng3.group_type = NewsGroup.TYPE_PROMOTIONS
    ng3.regional = True
    ng3.default_order = 20
    ng3.default_notifications_enabled = False
    ng3.tile = None

    ng4 = NewsGroup(key=NewsGroup.create_key(guid()))
    ng4.name = u'%s EVENTS' % community.name
    ng4.community_id = community_id
    ng4.group_type = NewsGroup.TYPE_EVENTS
    ng4.regional = False
    ng4.default_order = 30
    ng4.default_notifications_enabled = False
    ng4.tile = NewsGroupTile(
        background_image_url=u'https://storage.googleapis.com/oca-files/news/groups/_default/events.jpg')

    ng5 = NewsGroup(key=NewsGroup.create_key(guid()))
    ng5.name = u'%s TRAFFIC' % community.name
    ng5.community_id = community_id
    ng5.group_type = NewsGroup.TYPE_TRAFFIC
    ng5.regional = False
    ng5.default_order = 40
    ng5.default_notifications_enabled = True
    ng5.tile = NewsGroupTile(
        background_image_url=u'https://storage.googleapis.com/oca-files/news/groups/_default/trafic.jpg')

    ng6 = NewsGroup(key=NewsGroup.create_key(guid()))
    ng6.name = u'%s PRESS' % community.name
    ng6.community_id = community_id
    ng6.group_type = NewsGroup.TYPE_PRESS
    ng6.regional = False
    ng6.default_order = 50
    ng6.default_notifications_enabled = False
    ng6.tile = NewsGroupTile(
        background_image_url=u'https://storage.googleapis.com/oca-files/news/groups/_default/press.jpg')
    ng6.service_filter = True

    ng7 = NewsGroup(key=NewsGroup.create_key(guid()))
    ng7.name = u'%s POLLS' % community.name
    ng7.community_id = community_id
    ng7.send_notifications = False
    ng7.group_type = NewsGroup.TYPE_POLLS
    ng7.regional = False
    ng7.default_order = 60
    ng7.default_notifications_enabled = True
    ng7.tile = NewsGroupTile(
        background_image_url=u'https://storage.googleapis.com/oca-files/news/groups/_default/polls.jpg',
        promo_image_url=u'https://storage.googleapis.com/oca-files/news/groups/_default/polls_promo.png')

    ns.group_ids = [ng1.group_id,
                    ng2.group_id,
                    ng3.group_id,
                    ng4.group_id,
                    ng5.group_id,
                    ng6.group_id,
                    ng7.group_id]
    ndb.put_multi([ns, ng1, ng2, ng3, ng4, ng5, ng6, ng7])


def get_group_id_for_type_and_community(group_type, community_id):
    for g in get_groups_for_community(community_id).get(group_type, []):
        if not g.regional:
            return g.group_id
    return None


def get_groups_for_community(community_id):
    result = defaultdict(list)
    for group in NewsGroup.list_by_community_id(community_id):
        result[group.group_type].append(group)
    return result


def get_group_types_for_service(news_settings, group_types):
    # type: (NewsSettingsService, List[str]) -> List[str]
    if not group_types:
        group_types = [news_settings.groups[0].group_type] if news_settings.groups else []

    if news_settings.duplicate_in_city_news:
        if NewsGroup.TYPE_CITY not in group_types and NewsGroup.TYPE_CITY in news_settings.get_group_types():
            group_types.append(NewsGroup.TYPE_CITY)

    return group_types


def get_group_info(service_identity_user, group_type=None, community_ids=None, news_item=None):
    # type: (users.User, Optional[str], List[int], Optional[NewsItem]) -> Tuple[List[str], List[str]]
    service_user = get_service_user_from_service_identity_user(service_identity_user)
    news_settings = NewsSettingsService.create_key(service_user).get()  # type: Optional[NewsSettingsService]
    if not news_settings:
        raise Exception('NewsSettingsService for user %s does not existL %s', service_user)

    check_group_types = []
    check_community_ids = set()

    if news_item:
        if group_type:
            check_group_types = [group_type]
        else:
            if news_item.group_types_ordered:
                check_group_types = news_item.group_types_ordered
            else:
                check_group_types = news_item.group_types
        check_community_ids = set(news_item.community_ids)
        if community_ids:
            check_community_ids.update(community_ids)

    else:
        if group_type:
            check_group_types = [group_type]
        if community_ids:
            check_community_ids = set(community_ids)
    if not check_community_ids or not check_group_types:
        return [], []

    default_community_id = news_settings.community_id
    group_types = get_group_types_for_service(news_settings, check_group_types)
    logging.debug('Fetching group ids for group types: %s', group_types)
    if not group_types:
        return [], []
    news_groups = NewsGroup.list_by_community_ids(check_community_ids)  # type: List[NewsGroup]
    group_ids = []
    for group in news_groups:
        if group.group_type in group_types:
            if group.group_type in (NewsGroup.TYPE_CITY, NewsGroup.TYPE_PRESS, NewsGroup.TYPE_PUBLIC_SERVICE_ANNOUNCEMENTS):
                group_ids.append(group.group_id)

            elif group.group_type in (NewsGroup.TYPE_PROMOTIONS,):
                if group.community_id == default_community_id:
                    if not group.regional:
                        group_ids.append(group.group_id)
                elif group.regional:
                    group_ids.append(group.group_id)
            elif group.community_id == default_community_id:
                group_ids.append(group.group_id)
    logging.debug('Found group ids: %s', group_ids)
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


def get_groups_for_service_user(service_user):
    # type: (users.User) -> List[NewsGroup]
    nss = NewsSettingsService.create_key(service_user).get()  # type: NewsSettingsService
    if not nss:
        return []

    group_types = nss.get_group_types()
    if not group_types:
        return []

    groups = []
    for ng in NewsGroup.list_by_community_id(nss.community_id):
        if ng.group_type not in group_types:
            continue
        if ng.regional:
            continue
        groups.append(ng)
    return groups


def get_group_types_for_service_user(service_user, language):
    # type: (users.User, str) -> List[ServiceNewsGroupTO]
    from rogerthat.bizz.news import get_group_title
    service_profile = get_service_profile(service_user)
    groups = get_groups_for_service_user(service_user)
    if not groups:
        return []

    news_stream = NewsStream.create_key(service_profile.community_id).get()
    type_city = False
    if news_stream and news_stream.stream_type == NewsStream.TYPE_CITY:
        type_city = True

    return [ServiceNewsGroupTO(group_type=ng.group_type, name=get_group_title(type_city, ng, language))
            for ng in groups]


def update_stream_layout(group_ids, layout_id, visible_until):
    news_groups = ndb.get_multi([NewsGroup.create_key(group_id) for group_id in group_ids])  # type: List[NewsGroup]
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

    news_stream = NewsStream.create_key(ng.community_id).get()
    if news_stream.custom_layout_id == layout_id:
        return

    custom_layout = NewsStreamCustomLayout.create_key(layout_id, ng.community_id).get()
    if not custom_layout:
        return
    news_stream.custom_layout_id = layout_id
    news_stream.put()


def delete_user_group(group_id):
    run_job(_qry_user_settings, [group_id], _worker_delete_group_from_user_settings, [group_id], mode=MODE_BATCH,
            worker_queue=MIGRATION_QUEUE)


def _qry_user_settings(group_id):
    return NewsSettingsUser.list_by_group_id(group_id)


def _worker_delete_group_from_user_settings(keys, group_id):
    models = ndb.get_multi(keys)  # type: List[NewsSettingsUser]
    to_put = []
    for settings in models:
        group_settings = settings.get_group_by_id(group_id)
        if group_settings:
            settings.group_settings.remove(group_settings)
            to_put.append(settings)
    ndb.put_multi(to_put)


def delete_service_group(community_id, group_type):
    # type: (int, str) -> None
    assert isinstance(community_id, (int, long))
    run_job(_qry_delete_service_group, [community_id], _worker_delete_service_group, [group_type],
            worker_queue=MIGRATION_QUEUE)


def _qry_delete_service_group(community_id):
    return NewsSettingsService.list_by_community(community_id)


@ndb.transactional(xg=True)
def _worker_delete_service_group(nss_key, group_type):
    nss = nss_key.get()  # type: NewsSettingsService
    g = nss.get_group(group_type)
    if not g:
        return
    nss.groups.remove(g)
    nss.put()
