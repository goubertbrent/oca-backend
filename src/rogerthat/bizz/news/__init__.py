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

import base64
import imghdr
import json
import logging
import urllib2
import urlparse
from collections import defaultdict
from datetime import datetime
from types import NoneType

from google.appengine.api import urlfetch, images, taskqueue
from google.appengine.ext import db, ndb
from google.appengine.ext.deferred import deferred
from google.appengine.ext.ndb import utils
from google.appengine.ext.ndb.query import Cursor
from typing import List, Dict, Tuple, Iterable, Any, Optional

from mcfw.consts import MISSING
from mcfw.properties import azzert
from mcfw.rpc import returns, arguments
from mcfw.utils import chunks
from rogerthat.bizz.communities.communities import get_community
from rogerthat.bizz.job import run_job
from rogerthat.bizz.messaging import ALLOWED_BUTTON_ACTIONS, UnsupportedActionTypeException, _ellipsize_for_json, \
    _len_for_json
from rogerthat.bizz.news.groups import get_group_types_for_service, get_group_info, validate_group_type, \
    get_group_id_for_type_and_community
from rogerthat.bizz.news.matching import (
    create_matches_for_news_item,
    setup_default_settings,
    update_badge_count_user,
    create_matches_for_news_item_key,
    get_news_item_match_type,
)
from rogerthat.bizz.news.searching import find_news, re_index_news_item, re_index_news_item_by_key, find_news_by_service
from rogerthat.capi.news import disableNews, createNotification
from rogerthat.consts import SCHEDULED_QUEUE, DEBUG, NEWS_STATS_QUEUE, NEWS_MATCHING_QUEUE
from rogerthat.dal import put_in_chunks
from rogerthat.dal.app import get_app_by_id
from rogerthat.dal.mobile import get_mobile_key_by_account
from rogerthat.dal.profile import get_user_profile, get_service_profile, get_service_profiles, \
    get_service_visible_non_transactional
from rogerthat.dal.service import get_service_identity, \
    get_service_identities_not_cached
from rogerthat.exceptions.news import NewsNotFoundException, CannotUnstickNewsException, TooManyNewsButtonsException, \
    CannotChangePropertyException, MissingNewsArgumentException, InvalidNewsTypeException, NoPermissionToNewsException, \
    ValueTooLongException, InvalidScheduledTimestamp, \
    EmptyActionButtonCaption, InvalidActionButtonFlowParamsException
from rogerthat.models import ServiceProfile, PokeTagMap, ServiceMenuDef, UserProfileInfoAddress, NdbProfile, \
    UserProfileInfo, ServiceIdentity, NdbServiceProfile, NdbUserProfile
from rogerthat.models.maps import MapService
from rogerthat.models.news import NewsItem, NewsItemImage, NewsItemActionStatistics, NewsGroup, NewsSettingsUser, \
    NewsSettingsService, NewsSettingsUserService, \
    NewsMedia, NewsStream, NewsItemLocation, NewsItemGeoAddress, NewsItemAddress, \
    NewsNotificationStatus, NewsNotificationFilter, NewsStreamCustomLayout, NewsItemAction, MediaType, \
    NewsSettingsServiceGroup, NewsItemWebActions, NewsItemActions, \
    NewsMatchType, UserNewsGroupSettings
from rogerthat.models.properties.news import NewsItemStatistics, NewsButtons, NewsButton
from rogerthat.models.utils import ndb_allocate_id
from rogerthat.rpc import users
from rogerthat.rpc.models import RpcCAPICall
from rogerthat.rpc.rpc import logError, mapping, CAPI_KEYWORD_ARG_PRIORITY, PRIORITY_HIGH, \
    CAPI_KEYWORD_ARG_APPLE_PUSH_MESSAGE, CAPI_KEYWORD_PUSH_DATA, DO_NOT_SAVE_RPCCALL_OBJECTS
from rogerthat.rpc.service import BusinessException, logServiceError
from rogerthat.settings import get_server_settings
from rogerthat.to.messaging import BaseMemberTO
from rogerthat.to.news import NewsActionButtonTO, NewsItemTO, NewsItemListResultTO, DisableNewsRequestTO, \
    DisableNewsResponseTO, NewsTargetAudienceTO, BaseMediaTO, MediaTO, \
    GetNewsGroupsResponseTO, IfEmtpyScreenTO, NewsGroupRowTO, NewsGroupTabInfoTO, NewsGroupLayoutTO, \
    GetNewsStreamItemsResponseTO, NewsStreamItemTO, GetNewsGroupServicesResponseTO, NewsSenderTO, \
    SaveNewsGroupServicesResponseTO, CreateNotificationRequestTO, \
    CreateNotificationResponseTO, NewsLocationsTO, UpdateBadgeCountResponseTO, GetNewsGroupResponseTO, \
    GetNewsItemDetailsResponseTO, NewsStatisticAction, NewsGroupTO, GetNewsStreamFilterTO
from rogerthat.to.push import NewsStreamNotification
from rogerthat.translations import localize
from rogerthat.utils import now, is_flag_set, try_or_defer, guid, bizz_check, get_epoch_from_datetime
from rogerthat.utils.app import get_app_id_from_app_user, create_app_user
from rogerthat.utils.iOS import construct_push_notification
from rogerthat.utils.service import add_slash_default, get_service_user_from_service_identity_user, \
    remove_slash_default, get_service_identity_tuple
from rogerthat.web_client.models import WebClientSession

_DEFAULT_LIMIT = 100
ALLOWED_NEWS_BUTTON_ACTIONS = list(ALLOWED_BUTTON_ACTIONS) + ['poke']
IMAGE_MAX_SIZE = 409600  # 400kb


def create_default_news_settings(service_user, organization_type, community_id):
    # type: (users.User, int, int) -> None
    nss_key = NewsSettingsService.create_key(service_user)
    nss = nss_key.get()  # type: NewsSettingsService
    if nss and nss.community_id == community_id:
        return

    nss = NewsSettingsService(key=nss_key)
    nss.community_id = community_id
    nss.groups = []
    news_stream = NewsStream.create_key(nss.community_id).get()  # type: NewsStream
    if organization_type and organization_type == ServiceProfile.ORGANIZATION_TYPE_CITY:
        nss.setup_needed_id = 1
    else:
        group_types = []
        for ng in NewsGroup.list_by_community_id(community_id):
            group_types.append(ng.group_type)

        if NewsGroup.TYPE_PROMOTIONS in group_types:
            nss.groups.append(NewsSettingsServiceGroup(group_type=NewsGroup.TYPE_PROMOTIONS))
        if NewsGroup.TYPE_EVENTS in group_types:
            nss.groups.append(NewsSettingsServiceGroup(group_type=NewsGroup.TYPE_EVENTS))
        if nss.groups:
            nss.setup_needed_id = 0
        else:
            nss.setup_needed_id = 2
    nss.put()

    if news_stream and not news_stream.services_need_setup and nss.setup_needed_id != 0:
        news_stream.services_need_setup = True
        news_stream.put()


def delete_news_settings(service_user, service_identity_users):
    NewsSettingsService.create_key(service_user).delete()

    for si_user in service_identity_users:
        delete_news_items_service_identity_user(si_user)


def delete_news_items_service_identity_user(service_identity_user):
    run_job(_query_news_items_service, [service_identity_user],
            _worker_delete_news_items, [],
            worker_queue=NEWS_MATCHING_QUEUE)


def _query_news_items_service(service_identity_user):
    return NewsItem.list_by_sender(service_identity_user)


def _worker_delete_news_items(ni_key):
    news_item = ni_key.get()
    news_item.deleted = True
    news_item.status = NewsItem.STATUS_DELETED
    news_item.put()
    re_index_news_item(news_item)


def update_visibility_news_items(service_identity_user, visible):
    run_job(_query_news_items_service, [service_identity_user],
            _worker_update_visibility_news_items, [visible],
            worker_queue=NEWS_MATCHING_QUEUE)


def _worker_update_visibility_news_items(ni_key, visible):
    news_item = ni_key.get()
    if visible:
        if news_item.status == NewsItem.STATUS_PUBLISHED:
            news_item.status = NewsItem.STATUS_INVISIBLE
            news_item.put()
    elif news_item.status == NewsItem.STATUS_INVISIBLE:
        news_item.status = NewsItem.STATUS_PUBLISHED
        news_item.put()

    re_index_news_item(news_item)


def _get_service_identity_users_for_groups(news_groups):
    # type: (List[NewsGroup]) -> List[users.User]
    si_users = set()
    for news_group in news_groups:
        if news_group.service_filter and news_group.services:
            si_users.update({service_identity_user for service_identity_user in news_group.services})
    return list(si_users)


def get_service_profiles_and_identities(service_identity_users):
    # type: (Iterable[users.User]) -> Tuple[Dict[users.User, NdbServiceProfile], Dict[users.User, ServiceIdentity]]
    service_users = [get_service_user_from_service_identity_user(u) for u in service_identity_users]
    profiles_futures = ndb.get_multi_async([NdbProfile.createKey(user) for user in service_users])
    if service_identity_users:
        service_identities = {si.service_identity_user: si
                              for si in get_service_identities_not_cached(service_identity_users)}
    else:
        service_identities = {}
    service_profiles = {p.get_result().user: p.get_result() for p in profiles_futures}
    return service_profiles, service_identities


def _get_news_group_services_from_mapping(base_url, news_group, service_profiles, services_identities):
    # type: (str, NewsGroup, Dict[users.User, NdbServiceProfile], Dict[users.User, ServiceIdentity]) -> List[NewsSenderTO]
    services = []
    if news_group.service_filter:
        for service_identity_user in news_group.services:
            service_identity = services_identities.get(service_identity_user)
            if not service_identity:
                logging.warning('Could not find service identity %s, skipping', service_identity_user)
                continue
            service_profile = service_profiles[service_identity.service_user]
            services.append(NewsSenderTO.from_service_models(base_url, service_profile, service_identity))
    return services


@returns(GetNewsGroupsResponseTO)
@arguments(app_user=users.User)
def get_groups_for_user(app_user):
    from rogerthat.bizz.system import has_profile_addresses
    user_profile = get_user_profile(app_user)
    community_id = user_profile.community_id

    response = GetNewsGroupsResponseTO(rows=[], if_empty=None, has_locations=False)
    up, profile_info, news_user_settings, news_stream = ndb.get_multi([
        NdbProfile.createKey(app_user),
        UserProfileInfo.create_key(app_user),
        NewsSettingsUser.create_key(app_user),
        NewsStream.create_key(community_id)
    ])  # type: NdbUserProfile, UserProfileInfo, NewsSettingsUser, NewsStream
    lang = up.language
    fresh_setup = False if news_user_settings else True
    if fresh_setup:
        news_user_settings = setup_default_settings(app_user)
    else:
        news_user_settings.last_get_groups_request = datetime.utcnow()
        news_user_settings.put()

    if not news_stream.group_ids:
        logging.debug('debugging_news get_groups_for_user no groups community_id:%s', community_id)
        response.if_empty = IfEmtpyScreenTO(title=localize(lang, u'No news yet'),
                                            message=localize(lang, u"News hasn't been setup yet for this app"))

        return response

    response.has_locations = has_profile_addresses(profile_info)

    keys = [NewsGroup.create_key(group_id) for group_id in news_stream.group_ids]
    if news_stream:
        news_stream_layout = news_stream.layout
        if news_stream.custom_layout_id:
            keys.append(NewsStreamCustomLayout.create_key(news_stream.custom_layout_id, community_id))
    else:
        news_stream_layout = None
    models = ndb.get_multi(keys)
    if news_stream and news_stream.custom_layout_id:
        custom_layout = models.pop()
        if custom_layout and custom_layout.layout:
            news_stream_layout = custom_layout.layout

    badge_count_rpcs = {}
    if not fresh_setup:
        for group_id in news_stream.group_ids:
            user_group = news_user_settings.get_group_by_id(group_id)
            if not user_group:
                continue
            last_request_date = get_epoch_from_datetime(user_group.last_load_request)
            badge_count_rpcs[group_id] = NewsItem.count_unread(group_id, last_request_date)

    news_groups_mapping = {}  # type: Dict[str, NewsGroup]
    news_groups_type_mapping = defaultdict(list)  # type: Dict[str, List[NewsGroup]]
    for group in models:
        news_groups_mapping[group.group_id] = group
        news_groups_type_mapping[group.group_type].append(group)

    type_city = news_stream and news_stream.stream_type == NewsStream.TYPE_CITY
    base_url = get_server_settings().baseUrl
    si_users = _get_service_identity_users_for_groups(news_groups_mapping.values())
    service_profiles, services_identities = get_service_profiles_and_identities(si_users)

    if news_stream_layout:
        types_layout = []
        for nsl in news_stream_layout:
            types_layout.append(nsl.group_types)
    else:
        types_layout = ([NewsGroup.TYPE_CITY],
                        [NewsGroup.TYPE_PRESS, NewsGroup.TYPE_TRAFFIC],
                        [NewsGroup.TYPE_PROMOTIONS])

    for types in types_layout:
        row = NewsGroupRowTO(items=[])
        for group_type in types:
            tabs, news_groups = get_tabs_for_group(lang, news_groups_type_mapping, news_user_settings, group_type)
            if not tabs:
                logging.error("get_groups_for_user no tabs for type: %s", group_type)
                continue
            news_group = news_groups[0]
            badge_count_rpc = badge_count_rpcs.get(news_group.group_id)
            badge_count = badge_count_rpc and badge_count_rpc.get_result() or 0
            layout = get_layout_params_for_group(base_url, type_city, lang, news_group, badge_count)
            row.items.append(NewsGroupTO(
                key=news_group.group_id,
                name=get_group_title(type_city, news_group, lang),
                if_empty=get_if_empty_for_group_type(group_type, lang),
                tabs=tabs,
                layout=layout,
                services=_get_news_group_services_from_mapping(base_url, news_group, service_profiles,
                                                               services_identities)
            ))

        if row.items:
            response.rows.append(row)
    return response


def get_tabs_for_group(lang, news_groups_type_mapping, user_settings, group_type):
    # type: (str, Dict[str, List[NewsGroup]], NewsSettingsUser, unicode) -> Tuple[List[NewsGroupTabInfoTO], List[NewsGroup]]
    news_groups = sorted(news_groups_type_mapping.get(group_type, []),
                         key=lambda k: k.regional)  # type: List[NewsGroup]
    if not news_groups:
        return [], []
    tabs = []
    for news_group in news_groups:
        user_group = user_settings.get_group_by_id(news_group.group_id)
        if user_group and user_group.notifications != NewsNotificationFilter.NOT_SET:
            notifications = user_group.notifications
        else:
            notifications = news_group.default_notification_filter
        tab = NewsGroupTabInfoTO(key=news_group.group_id,
                                 name=localize(lang, u'Regional') if news_group.regional else localize(lang, u'Local'),
                                 notifications=notifications)
        tabs.append(tab)
    return tabs, news_groups


def get_news_group_response(app_user, group_id):
    user_profile = get_user_profile(app_user)
    keys = [
        NewsStream.create_key(user_profile.community_id),
        NewsGroup.create_key(group_id),
        NewsSettingsUser.create_key(app_user)
    ]
    news_stream, news_group, news_user_settings = ndb.get_multi(keys)  # type: NewsStream, NewsGroup,NewsSettingsUser
    if not news_user_settings:
        news_user_settings = setup_default_settings(app_user)
    all_groups = ndb.get_multi([NewsGroup.create_key(i) for i in news_stream.group_ids])  # type: List[NewsGroup]
    news_groups_type_mapping = defaultdict(list)  # type: Dict[str, List[NewsGroup]]
    for group in all_groups:
        news_groups_type_mapping[group.group_type].append(group)
    base_url = get_server_settings().baseUrl
    lang = user_profile.language
    type_city = news_stream and news_stream.stream_type == NewsStream.TYPE_CITY

    si_users = _get_service_identity_users_for_groups([news_group])
    service_profiles, services_identities = get_service_profiles_and_identities(si_users)
    tabs, _ = get_tabs_for_group(lang, news_groups_type_mapping, news_user_settings, news_group.group_type)
    group = NewsGroupTO(
        key=group_id,
        name=get_group_title(type_city, news_group, lang),
        if_empty=get_if_empty_for_group_type(news_group.group_type, lang),
        tabs=tabs,
        # We don't bother calculating the badge count here since there's no usecase for it yet.
        # this saves us a NewsItem.count_unread query
        layout=get_layout_params_for_group(base_url, type_city, lang, news_group, badge_count=0),
        services=_get_news_group_services_from_mapping(base_url, news_group, service_profiles, services_identities),
    )
    return GetNewsGroupResponseTO(group=group)


def get_layout_params_for_group(base_url, type_city, lang, group, badge_count):
    # type: (str, str, str, NewsGroup, int) -> NewsGroupLayoutTO
    layout = NewsGroupLayoutTO()
    layout.badge_count = badge_count
    if group.tile:
        layout.background_image_url = group.tile.background_image_url
        layout.promo_image_url = group.tile.promo_image_url
    layout.title = get_group_title(type_city, group, lang)
    layout.subtitle = get_group_subtitle(type_city, group, lang)

    if group.group_type != NewsGroup.TYPE_PROMOTIONS:
        return layout

    ni = get_latest_item_for_user_by_group(group.group_id)
    if not ni:
        return layout
    si = get_service_identity(ni.sender)
    if not si:
        return layout

    layout.promo_image_url = u"%s/unauthenticated/mobi/cached/avatar/%s" % (base_url, si.avatarId)
    if ni.type == NewsItem.TYPE_NORMAL and ni.title:
        layout.subtitle = ni.title
    elif ni.type == NewsItem.TYPE_QR_CODE and ni.qr_code_caption:
        layout.subtitle = ni.qr_code_caption
    return layout


def get_group_title(type_city, group, lang):
    if group.tile and group.tile.title:
        return localize(lang, group.tile.title)
    return get_group_title_for_type(type_city, group.group_type, lang)


def get_group_subtitle(type_city, group, lang):
    if group.tile and group.tile.subtitle:
        return localize(lang, group.tile.subtitle)
    return get_group_subtitle_for_type(type_city, group.group_type, lang)


def get_group_title_for_type(type_city, group_type, lang):
    if group_type == NewsGroup.TYPE_CITY:
        if type_city:
            return localize(lang, u'City news')
        return localize(lang, u'Community news')
    elif group_type == NewsGroup.TYPE_PROMOTIONS:
        return localize(lang, u'Promotions')
    elif group_type == NewsGroup.TYPE_EVENTS:
        return localize(lang, u'Events')
    elif group_type == NewsGroup.TYPE_TRAFFIC:
        return localize(lang, u'Traffic')
    elif group_type == NewsGroup.TYPE_PRESS:
        return localize(lang, u'Press')
    elif group_type == NewsGroup.TYPE_POLLS:
        return localize(lang, u'Polls')
    elif group_type == NewsGroup.TYPE_PUBLIC_SERVICE_ANNOUNCEMENTS:
        return localize(lang, u'Coronavirus info')
    return group_type


def get_group_subtitle_for_type(type_city, group_type, lang):
    if group_type == NewsGroup.TYPE_CITY:
        if type_city:
            return localize(lang, u'The latest news of your city')
        return localize(lang, u'The latest news of your community')
    elif group_type == NewsGroup.TYPE_PROMOTIONS:
        if type_city:
            return localize(lang, u'Promotions in and around your city')
        return localize(lang, u'Promotions in and around your community')
    elif group_type == NewsGroup.TYPE_EVENTS:
        return localize(lang, u'News about events')
    elif group_type == NewsGroup.TYPE_TRAFFIC:
        return localize(lang, u'Expected traffic')
    elif group_type == NewsGroup.TYPE_PRESS:
        if type_city:
            return localize(lang, u'Your city in the press')
        return localize(lang, u'Your community in the press')
    elif group_type == NewsGroup.TYPE_POLLS:
        return localize(lang, u'Current polls')
    elif group_type == NewsGroup.TYPE_PUBLIC_SERVICE_ANNOUNCEMENTS:
        return localize(lang, u'The latest information about COVID-19')
    return group_type


def get_if_empty_for_group_type(group_type, lang):
    if group_type == NewsGroup.TYPE_PROMOTIONS:
        return IfEmtpyScreenTO(title=localize(lang, u'No promotions'),
                               message=localize(lang, u'There are no promotions at this time'))
    elif group_type == NewsGroup.TYPE_EVENTS:
        return IfEmtpyScreenTO(title=localize(lang, u'No events'),
                               message=localize(lang, u'There are no events at this time'))
    elif group_type == NewsGroup.TYPE_TRAFFIC:
        return IfEmtpyScreenTO(title=localize(lang, u'No traffic'),
                               message=localize(lang, u'There is no traffic at this time'))
    elif group_type == NewsGroup.TYPE_PRESS:
        return IfEmtpyScreenTO(title=localize(lang, u'No press'),
                               message=localize(lang, u'There are no local press articles at this time'))
    elif group_type == NewsGroup.TYPE_POLLS:
        return IfEmtpyScreenTO(title=localize(lang, u'No polls'),
                               message=localize(lang, u'There are no polls at this time'))
    return IfEmtpyScreenTO(title=localize(lang, u'No news'),
                           message=localize(lang, u'There is no news at this time'))


@returns(NewsItem)
@arguments(group_id=unicode)
def get_latest_item_for_user_by_group(group_id):
    return NewsItem.list_published_by_group_id_sorted(group_id).get()


def _save_last_load_request_news_group(app_user, group_id, d):
    nsu = NewsSettingsUser.create_key(app_user).get()  # type: NewsSettingsUser
    if not nsu:
        return
    user_group = nsu.get_group_by_id(group_id)
    if not user_group:
        user_group = UserNewsGroupSettings()
        user_group.group_id = group_id
        user_group.notifications = NewsNotificationFilter.NOT_SET
        nsu.group_settings.append(user_group)

    user_group.last_load_request = d
    nsu.put()


def __get_community(community_id, app_user):
    if community_id:
        return community_id
    else:
        if app_user is None:
            raise Exception('Expected app_user to be set when community_id is None')
        return get_user_profile(app_user).community_id


def get_items_for_filter(stream_filter, news_ids=None, cursor=None, app_user=None, community_id=None, amount=None):
    # type: (GetNewsStreamFilterTO, List[int], unicode, users.User, Optional[int], int) -> GetNewsStreamItemsResponseTO
    if news_ids is None:
        news_ids = []
    if not amount:
        amount = 50 if cursor else 10
    if stream_filter.group_type and not stream_filter.group_id:
        stream_filter.group_id = get_group_id_for_type_and_community(stream_filter.group_type,
                                                                     __get_community(community_id, app_user))
    if stream_filter.search_string is not None:
        return get_items_for_user_by_search_string(app_user, stream_filter.search_string, cursor, amount,
                                                   __get_community(community_id, app_user))
    if stream_filter.service_identity_email is not None:
        return get_items_for_user_by_service(app_user,
                                             stream_filter.service_identity_email,
                                             stream_filter.group_id,
                                             __get_community(community_id, app_user),
                                             cursor,
                                             amount)
    if stream_filter.group_id is not None:
        return get_items_for_user_by_group(app_user, stream_filter.group_id, cursor, news_ids, amount)
    return GetNewsStreamItemsResponseTO(cursor=None, items=[])


@returns(GetNewsStreamItemsResponseTO)
@arguments(app_user=(users.User, NoneType), group_id=unicode, cursor=unicode, additional_news_ids=[(int, long)],
           amount=(int, long))
def get_items_for_user_by_group(app_user, group_id, cursor, additional_news_ids, amount):
    if app_user and cursor is None and group_id != u'pinned':
        deferred.defer(_save_last_load_request_news_group, app_user, group_id, datetime.utcnow())
        deferred.defer(update_badge_count_user, app_user, group_id, 0)

    r = GetNewsStreamItemsResponseTO(cursor=None, items=[], group_id=group_id)

    if group_id == u'pinned':
        group_id = None
        qry = NewsItemActions.list_pinned(app_user)
    else:
        qry = NewsItem.list_published_by_group_id_sorted(group_id)

    news_ids = list(additional_news_ids)  # making a copy to not alter the news_ids list of the request
    items, new_cursor, has_more = qry.fetch_page(
        amount, start_cursor=Cursor.from_websafe_string(cursor) if cursor else None, keys_only=True)
    for item in items:
        if item.id() not in news_ids:
            news_ids.append(item.id())
    if has_more:
        r.cursor = new_cursor.to_websafe_string().decode('utf-8') if new_cursor else None
    else:
        r.cursor = None

    r.items = _get_news_stream_items_for_user(app_user, news_ids, group_id, additional_news_ids)
    return r


@returns(GetNewsStreamItemsResponseTO)
@arguments(app_user=(users.User, NoneType), service_identity_email=unicode, group_id=unicode,
           community_id=(int, long, NoneType), cursor=unicode, amount=(int, long))
def get_items_for_user_by_service(app_user, service_identity_email, group_id, community_id, cursor, amount):
    # type: (Optional[users.User], unicode, Optional[unicode], Optional[int], Optional[unicode], int) -> GetNewsStreamItemsResponseTO
    if app_user and group_id and cursor is None:
        deferred.defer(_save_last_load_request_news_group, app_user, group_id, datetime.utcnow())
        deferred.defer(update_badge_count_user, app_user, group_id, 0)

    service_identity_user = add_slash_default(users.User(service_identity_email))
    if group_id:
        qry = NewsItem.list_published_by_sender_and_group_id_sorted(service_identity_user, group_id, keys_only=True)
    else:
        qry = NewsItem.list_published_by_sender(service_identity_user, community_id, keys_only=True)

    items, new_cursor, has_more = qry.fetch_page(
        amount, start_cursor=Cursor.from_websafe_string(cursor) if cursor else None, keys_only=True)

    r = GetNewsStreamItemsResponseTO()
    r.group_id = group_id
    if has_more:
        r.cursor = new_cursor.to_websafe_string().decode('utf-8') if new_cursor else None
    else:
        r.cursor = None
    r.items = _get_news_stream_items_for_user(app_user, [ni_key.id() for ni_key in items], group_id, [])
    return r


@returns(GetNewsStreamItemsResponseTO)
@arguments(app_user=users.User, search_string=unicode, cursor=unicode, amount=(int, long),
           community_id=(int, long, NoneType))
def get_items_for_user_by_search_string(app_user, search_string, cursor, amount, community_id):
    result = GetNewsStreamItemsResponseTO(cursor=None, items=[])
    if not search_string:
        return result
    new_cursor, news_ids = find_news(community_id, search_string, cursor, amount)
    if not news_ids:
        return result
    result.cursor = new_cursor
    result.items = _get_news_stream_items_for_user(app_user, news_ids, None, [])
    return result


@ndb.non_transactional
@utils.positional(1)
def get_news_share_base_url(base_url, app_id=None, community_id=0):
    # type: (unicode, Optional[unicode], Optional[long]) -> unicode
    if community_id:
        community = get_community(community_id)
        app_id = community.default_app
    elif not app_id:
        azzert(app_id, 'Expected app_id to be set when community_id is not set')
    app = get_app_by_id(app_id)
    if not app:
        logging.debug('get_news_share_base_url app:%s was not found', app_id)
        return None
    if not app.default_app_name_mapping:
        logging.debug('get_news_share_base_url app:%s has no default mapping', app_id)
        return None
    return '%s/web/%s/news/id' % (base_url, app.default_app_name_mapping)


def get_news_share_url(share_base_url, news_id):
    if not share_base_url:
        return None
    return '%s/%s' % (share_base_url, news_id)


@returns([NewsStreamItemTO])
@arguments(app_user=(users.User, NoneType), ids=[(int, long)], group_id=unicode, required_news_ids=[(int, long)])
def _get_news_stream_items_for_user(app_user, ids, group_id, required_news_ids):
    # type: (Optional[users.User], List[int], Optional[unicode], List[int]) -> List[NewsStreamItemTO]
    # app_user should only be None when used by news widget on home screen / bottom sheet
    news_items = get_news_by_ids(ids)
    server_settings = get_server_settings()
    base_url = server_settings.baseUrl
    service_profiles, service_identities = get_service_profiles_and_identities(list({item.sender
                                                                                     for item in news_items}))
    if app_user:
        app_id = get_app_id_from_app_user(app_user)
        share_base_url = get_news_share_base_url(server_settings.webClientUrl, app_id=app_id)
    else:
        share_base_url = None
    news_items_dict = {}
    for news_item in news_items:
        news_item_to = NewsItemTO.from_model(
            news_item,
            base_url,
            service_profiles[get_service_user_from_service_identity_user(news_item.sender)],
            service_identities[news_item.sender],
            share_url=get_news_share_url(share_base_url, news_item.id)
        )
        news_items_dict[news_item.id] = {'model': news_item,
                                         'to': news_item_to}

    items = []
    if group_id:
        if app_user:
            news_user_settings = NewsSettingsUser.create_key(app_user).get()
            model_keys = []
            for news_id in ids:
                service_identity_user = add_slash_default(users.User(news_items_dict[news_id]['to'].sender.email))
                model_keys.append(NewsItemActions.create_key(app_user, news_id))
                model_keys.append(NewsSettingsUserService.create_key(app_user, group_id, service_identity_user))

            models = ndb.get_multi(model_keys)
        else:
            models = [None for _ in ids] * 2
        for news_id, chunk_ in zip(ids, chunks(models, 2)):
            if app_user:
                match_type = get_news_item_match_type(news_user_settings, news_items_dict[news_id]['model'])
            else:
                match_type = NewsMatchType.NORMAL
            if match_type == NewsMatchType.NO_MATCH:
                if news_id in required_news_ids:
                    match_type = NewsMatchType.NORMAL
                else:
                    continue

            news_item_actions, news_settings = chunk_  # type: (NewsItemActions, NewsSettingsUserService)
            notifications = news_settings.notifications if news_settings else NewsNotificationStatus.NOT_SET
            news_item_to = news_items_dict[news_id]['to']
            items.append(
                NewsStreamItemTO.from_model(app_user, news_item_actions, news_item_to, notifications, match_type))
    else:
        if app_user:
            models = ndb.get_multi([NewsItemActions.create_key(app_user, news_id) for news_id in ids])
        else:
            models = [None for _ in ids]
        for news_id, news_item_actions in zip(ids, models):
            news_item_to = news_items_dict[news_id]['to']
            items.append(NewsStreamItemTO.from_model(app_user, news_item_actions, news_item_to))
    return items


@returns(GetNewsGroupServicesResponseTO)
@arguments(app_user=users.User, group_id=unicode, key=unicode, cursor=unicode)
def get_group_services(app_user, group_id, key, cursor):
    batch_count = 50 if cursor else 10
    if key == u'notifications_disabled':
        qry = NewsSettingsUserService.list_by_notification_status(
            app_user, group_id, NewsNotificationStatus.DISABLED)
    elif key == u'notifications_enabled':
        qry = NewsSettingsUserService.list_by_notification_status(
            app_user, group_id, NewsNotificationStatus.ENABLED)
    else:
        return GetNewsGroupServicesResponseTO(cursor=None, services=[])

    r = GetNewsGroupServicesResponseTO()
    r.services = []
    items, new_cursor, has_more = qry.fetch_page(
        batch_count, start_cursor=Cursor.from_websafe_string(cursor) if cursor else None, keys_only=True)

    service_identity_users = [users.User(item.id()) for item in items]
    service_users = [get_service_user_from_service_identity_user(u) for u in service_identity_users]
    service_profiles = {prof.service_user: prof for prof in get_service_profiles(service_users)}
    sis = get_service_identities_not_cached(service_identity_users)
    base_url = get_server_settings().baseUrl
    for si in sis:
        service_profile = service_profiles.get(si.service_user)
        r.services.append(NewsSenderTO.from_service_models(base_url, service_profile, si))

    if has_more:
        r.cursor = new_cursor.to_websafe_string().decode('utf-8') if new_cursor else None
    else:
        r.cursor = None
    return r


@returns(SaveNewsGroupServicesResponseTO)
@arguments(app_user=users.User, group_id=unicode, key=unicode, action=unicode, service=unicode)
def save_group_services(app_user, group_id, key, action, service):
    settings = NewsSettingsUser.create_key(app_user).get()  # type: NewsSettingsUser
    if not settings:
        return SaveNewsGroupServicesResponseTO()
    if key != u'notifications':
        return SaveNewsGroupServicesResponseTO()

    if service:
        should_put = False
        service_identity_user = add_slash_default(users.User(service))
        nsus_key = NewsSettingsUserService.create_key(app_user, group_id, service_identity_user)
        service_settings = nsus_key.get()  # type: NewsSettingsUserService
        if not service_settings:
            service_settings = NewsSettingsUserService(key=nsus_key, group_id=group_id,
                                                       notifications=NewsNotificationStatus.NOT_SET)
        group = NewsGroup.create_key(group_id).get()  # type: NewsGroup
        group_details = settings.get_group_by_id(group_id)
        if group_details:
            if group_details.notifications == NewsNotificationFilter.NOT_SET:
                group_details.notifications = group.default_notification_filter
                settings.put()
        else:
            group_details = UserNewsGroupSettings()
            group_details.group_id = group_id
            group_details.last_load_request = datetime.now()
            group_details.notifications = group.default_notification_filter
            settings.group_settings.append(group_details)
            settings.put()

        if action == u'enable':
            if group_details.notifications == NewsNotificationFilter.ALL:
                service_settings.notifications = NewsNotificationStatus.NOT_SET
            else:
                service_settings.notifications = NewsNotificationStatus.ENABLED
            should_put = True
        elif action == u'disable':
            if group_details.notifications == NewsNotificationFilter.SPECIFIED:
                service_settings.notifications = NewsNotificationStatus.NOT_SET
            else:
                service_settings.notifications = NewsNotificationStatus.DISABLED
            should_put = True
        if should_put:
            service_settings.put()
    else:
        if action in (NewsSettingsUser.NOTIFICATION_ENABLED_FOR_NONE,
                      NewsSettingsUser.NOTIFICATION_ENABLED_FOR_ALL,
                      NewsSettingsUser.NOTIFICATION_ENABLED_FOR_SPECIFIED):
            group_details = settings.get_group_by_id(group_id)
            if not group_details:
                group_details = UserNewsGroupSettings()
                group_details.group_id = group_id
                group_details.last_load_request = datetime.now()
                settings.group_settings.append(group_details)
            group_details.notifications = NewsSettingsUser.FILTER_MAPPING[action]
            settings.put()
        else:
            logging.error('Unexpected action "%s" for key "%s"', action, key)

    return SaveNewsGroupServicesResponseTO()


def get_news_item_details(app_user, news_id):
    news_item, news_item_actions = ndb.get_multi(
        [NewsItem.create_key(news_id), NewsItemActions.create_key(app_user, news_id)])  # type: NewsItem, NewsItemActions
    if not news_item:
        return GetNewsItemDetailsResponseTO(item=None)
    server_settings = get_server_settings()
    service_profile = get_service_profile(get_service_user_from_service_identity_user(news_item.sender))
    service_identity = get_service_identity(news_item.sender)
    share_base_url = get_news_share_base_url(server_settings.webClientUrl, community_id=service_profile.community_id)
    share_url = get_news_share_url(share_base_url, news_item.id)
    item_to = NewsItemTO.from_model(news_item, server_settings.baseUrl, service_profile, service_identity, share_url)
    return GetNewsItemDetailsResponseTO(item=NewsStreamItemTO.from_model(app_user, news_item_actions, item_to))


@returns(NewsItemListResultTO)
@arguments(cursor=unicode, batch_count=(int, long), service_identity_user=users.User, query=unicode)
def get_news_by_service(cursor, batch_count, service_identity_user, query=None):
    service_user = get_service_user_from_service_identity_user(service_identity_user)
    if query:
        # Use search index to find item ids, then use datastore to fetch the items.
        r_cursor, news_ids = find_news_by_service(service_identity_user, query, batch_count, cursor)
        results = ndb.get_multi([NewsItem.create_key(news_id) for news_id in news_ids])
        has_more = len(results) == batch_count  # Might not be exactly true but it's a good enough guess
    else:
        # Use datastore to get items
        qry = NewsItem.list_by_sender(service_identity_user)
        c = ndb.Cursor.from_websafe_string(cursor) if cursor else None
        results, new_cursor, has_more = qry.fetch_page(batch_count,
                                                       start_cursor=c)  # type: List[NewsItem], ndb.Cursor, bool
        r_cursor = new_cursor and new_cursor.to_websafe_string().decode('utf-8')
    news_items = replace_hashed_news_button_tags_with_real_tag(results, service_user)
    service_profile = get_service_profile(service_user)
    service_identity = get_service_identity(service_identity_user)
    server_settings = get_server_settings()
    share_base_url = get_news_share_base_url(server_settings.webClientUrl, community_id=service_profile.community_id)
    return NewsItemListResultTO(news_items, has_more, r_cursor, server_settings.baseUrl, service_profile,
                                service_identity, share_base_url)


@returns([NewsItem])
@arguments(news_items=[NewsItem], service_user=users.User)
def replace_hashed_news_button_tags_with_real_tag(news_items, service_user):
    """
    Args:
        news_items (list of NewsItem)
        service_user (users.User)
    Returns:
        news_items (list of NewsItem)
    """
    poke_tag_maps_to_get = []
    for news_item in news_items:
        if news_item.buttons:
            for button in news_item.buttons:
                if button.action.startswith('poke://'):
                    poke_tag_maps_to_get.append(PokeTagMap.create_key(button.action.split('poke://')[1], service_user))

    if poke_tag_maps_to_get:
        poke_tag_maps = {poke_tag_map.hash: poke_tag_map for poke_tag_map in PokeTagMap.get(poke_tag_maps_to_get)}
        for news_item in news_items:
            if news_item.buttons:
                for button in news_item.buttons:
                    if button.action.startswith('poke://'):
                        hashed_tag = button.action.split('poke://')[1]
                        button.action = u'poke://%s' % poke_tag_maps[hashed_tag].tag
    return news_items


@returns([(NewsItem, NoneType)])
@arguments(news_ids=[(int, long)])
def get_news_by_ids(news_ids):
    # type: (List[int]) -> List[NewsItem]
    return ndb.get_multi([NewsItem.create_key(i) for i in news_ids])


@ndb.non_transactional()
def _get_group_info(service_identity_user, group_type=None, community_ids=None, news_item=None):
    return get_group_info(service_identity_user, group_type, community_ids, news_item)


@returns(NewsItem)
@arguments(sender=users.User, sticky=bool, sticky_until=(int, long), title=unicode, message=unicode,
           image=unicode, news_type=int, news_buttons=[NewsActionButtonTO],
           qr_code_content=unicode, qr_code_caption=unicode, community_ids=[(int, long)], scheduled_at=(int, long),
           flags=int, news_id=(int, long, NoneType), target_audience=NewsTargetAudienceTO,
           tags=[unicode], media=BaseMediaTO, locations=NewsLocationsTO, group_type=unicode,
           group_visible_until=(int, long, NoneType), timestamp=(int, long, NoneType))
def put_news(sender, sticky, sticky_until, title, message, image, news_type, news_buttons,
             qr_code_content, qr_code_caption, community_ids, scheduled_at, flags, news_id=None, target_audience=None,
             tags=None, media=MISSING, locations=None, group_type=MISSING,
             group_visible_until=None, timestamp=None):
    """
    Args:
        sender (users.User): Sender of the news item
        sticky (bool): Whether or not this is  a sticky news item
        sticky_until (long): Timestamp until this news item is sticky
        title (unicode): Title of the news item. Maximum 70 characters.
        message (unicode): Message of the news item. Maximum 500 characters.
        image (unicode): base64 encoded image
        news_type (int): Type of the news item. Should be one of NewsItem.TYPES
        news_buttons (list of NewsActionButtonTO): Additional buttons of the news item where users can interact with.
         Other buttons will be added by default depending on the type of the news
        qr_code_content (unicode): Content of the QR code. Should only be used when news_type is NewsItem.TYPE_QR_CODE
        qr_code_caption (unicode): Caption of the QR code. Should only be used when news_type is NewsItem.TYPE_QR_CODE
        community_ids (list[int]): List of communities where the news should be shown.
        scheduled_at (long): Timestamp when this news item should be published
        flags (int): Flags to enable follow/rogerthat buttons
        news_id (long): id of the news to update. When not specified a new item is created
        target_audience (NewsTargetAudienceTO)
        locations(NewsLocationsTO)

    Returns:
        NewsItem
    """
    # Validation
    service_user = get_service_user_from_service_identity_user(sender)

    def is_set(val):
        return val is not MISSING

    def is_empty(val):
        return not (is_set(val) and val)

    existing_news_item = None
    scheduled_at_changed = False
    if news_id:
        existing_news_item = get_and_validate_news_item(news_id, sender)
        if existing_news_item.sticky and sticky is not MISSING and not sticky:
            raise CannotUnstickNewsException()
        if news_type is not MISSING and existing_news_item.type != news_type:
            raise CannotChangePropertyException(u'news_type')
        if existing_news_item.scheduled_at > 0 and existing_news_item.scheduled_at != scheduled_at and not existing_news_item.published:
            scheduled_at_changed = True
        else:
            scheduled_at = existing_news_item.scheduled_at
        old_group_ids = [group_id for group_id in existing_news_item.group_ids]
    else:
        old_group_ids = []
        if is_empty(group_type):
            raise MissingNewsArgumentException(u'group_type')
        if is_empty(news_type):
            raise MissingNewsArgumentException(u'news_type')
        if news_type not in NewsItem.TYPES:
            raise InvalidNewsTypeException(news_type)
        if news_type == NewsItem.TYPE_QR_CODE:
            if is_empty(qr_code_content):
                raise MissingNewsArgumentException(u'qr_code_content')
            if is_empty(qr_code_caption):
                raise MissingNewsArgumentException(u'qr_code_caption')
        elif news_type == NewsItem.TYPE_NORMAL:
            if is_empty(title):
                raise MissingNewsArgumentException(u'title')
        if is_empty(community_ids):
            raise MissingNewsArgumentException(u'community_ids')

    if sticky and is_empty(sticky_until):
        raise MissingNewsArgumentException(u'sticky_until')

    if not is_empty(title) and len(title) > NewsItem.MAX_TITLE_LENGTH:
        raise ValueTooLongException('title', NewsItem.MAX_TITLE_LENGTH)
    if not is_empty(qr_code_caption) and len(qr_code_caption) > NewsItem.MAX_TITLE_LENGTH:
        raise ValueTooLongException('qr_code_caption', NewsItem.MAX_TITLE_LENGTH)

    if not is_empty(group_type):
        validate_group_type(service_user, group_type)

    if not is_empty(scheduled_at) and (not existing_news_item or scheduled_at_changed):
        if scheduled_at < now() and scheduled_at is not 0:
            raise InvalidScheduledTimestamp()
    scheduled_at = scheduled_at if not is_empty(scheduled_at) else 0

    buttons = NewsButtons()

    poke_tags_to_create = []
    if is_set(news_buttons):
        for i, news_button in enumerate(news_buttons):
            btn = NewsButton()
            btn.id = news_button.id
            if not news_button.caption or not news_button.caption.strip():
                raise EmptyActionButtonCaption()
            btn.caption = news_button.caption
            btn.action = news_button.action
            btn.flow_params = None
            if not is_empty(news_button.flow_params):
                try:
                    json.loads(news_button.flow_params)
                    btn.flow_params = news_button.flow_params
                except ValueError:
                    raise InvalidActionButtonFlowParamsException(btn.id)
            btn.index = i

            if news_button.action:
                scheme = urllib2.urlparse.urlparse(btn.action)[0]
                if scheme not in ALLOWED_NEWS_BUTTON_ACTIONS:
                    raise UnsupportedActionTypeException(scheme)
                if btn.action.startswith("mailto:") and not btn.action.startswith("mailto://"):
                    btn.action = "mailto://" + btn.action[7:]
                elif btn.action.startswith("smi://"):
                    btn.action = 'smi://' + ServiceMenuDef.hash_tag(btn.action[6:])
                elif btn.action.startswith("poke://"):
                    tag = btn.action[7:]
                    hashed_tag = ServiceMenuDef.hash_tag(tag)
                    btn.action = 'poke://' + hashed_tag
                    poke_tags_to_create.append(PokeTagMap(key=PokeTagMap.create_key(hashed_tag, service_user),
                                                          tag=tag))

            buttons.add(btn)
    if poke_tags_to_create:
        deferred.defer(_save_models, poke_tags_to_create, _transactional=ndb.in_transaction())

    service_profile = get_service_profile(service_user)
    community = get_community(service_profile.community_id)
    if community.demo:
        # services in demo apps can only send to their own community
        community_ids = [service_profile.community_id]
    service_visible = get_service_visible_non_transactional(sender)
    if media is not MISSING and media:
        pass
    elif image is not MISSING:
        if image:
            media = MediaTO(type=MediaType.IMAGE, content=image)
        else:
            media = None
    media_changed = media is not MISSING
    if media_changed and media and existing_news_item and existing_news_item.media:
        media_changed = media.content != existing_news_item.media.url
    decoded_image = None
    if media_changed and media:
        bizz_check(media.type in MediaType.all(), 'Invalid MediaType: %s' % media.type)
        media, decoded_image = get_and_validate_media_info(media.type, media.content)

    existing_news_item_published = existing_news_item and existing_news_item.published

    locations_set = not is_empty(locations)

    group_types, group_ids = _get_group_info(sender,
                                             group_type=None if is_empty(group_type) else group_type,
                                             community_ids=list(set(community_ids)) if community_ids and community_ids is not MISSING else [],
                                             news_item=existing_news_item)

    # noinspection PyShadowingNames
    @ndb.transactional(xg=True)
    def trans(news_item_id, news_type):
        news_item = None  # type: Optional[NewsItem]
        news_item_image_id = None
        to_put = []
        if news_item_id:
            news_item = NewsItem.get_by_id(news_item_id)
            news_type = news_item.type
        if media_changed:
            if news_item and news_item.media and news_item.media.content:
                NewsItemImage.create_key(news_item.media.content).delete_async()
            if decoded_image:
                news_item_image_id = ndb_allocate_id(NewsItemImage)
                news_item_image = NewsItemImage(key=NewsItemImage.create_key(news_item_image_id),
                                                image=decoded_image)
                to_put.append(news_item_image)
        send_to_community_ids = set(community_ids) if community_ids and community_ids is not MISSING else set()

        order_timestamp = max(scheduled_at, now())
        if news_item:
            if not news_item.sticky and sticky:
                news_item.sticky = sticky
                news_item.sticky_until = sticky_until
            for community_id in news_item.community_ids:
                send_to_community_ids.add(community_id)
            news_item.community_ids = list(send_to_community_ids)
            news_item.version += 1

            if not is_set(flags):
                item_flags = news_item.flags
            else:
                item_flags = flags

            # set the new scheduling timestamp if it has changed only
            if not news_item.published and scheduled_at_changed:
                news_item.scheduled_at = scheduled_at
        else:
            if not is_set(flags):
                item_flags = NewsItem.DEFAULT_FLAGS
            else:
                item_flags = flags

            news_item = NewsItem(key=NewsItem.create_key(ndb_allocate_id(NewsItem)),
                                 sticky=sticky,
                                 sticky_until=sticky_until if sticky else 0,
                                 sender=sender,
                                 community_ids=send_to_community_ids,
                                 timestamp=now() if is_empty(timestamp) else timestamp,
                                 type=news_type,
                                 version=1,
                                 scheduled_at=scheduled_at,
                                 published=scheduled_at is 0)

            if news_item.published:
                news_item.status = NewsItem.STATUS_PUBLISHED if service_visible else NewsItem.STATUS_INVISIBLE
            else:
                news_item.status = NewsItem.STATUS_SCHEDULED

        if news_item.type == NewsItem.TYPE_QR_CODE:
            if is_set(qr_code_caption):
                news_item.qr_code_caption = qr_code_caption
            if is_set(qr_code_content):
                news_item.qr_code_content = qr_code_content
        if media_changed:
            news_item.media = media and NewsMedia(content=news_item_image_id,
                                                  url=None if news_item_image_id else media.content,
                                                  **media.to_dict(exclude=['content']))
        if is_set(title):
            news_item.title = title
        if is_set(message):
            news_item.message = message
        news_item.group_types_ordered = group_types
        news_item.group_types = group_types
        news_item.group_ids = group_ids

        max_button_count = NewsItem.MAX_BUTTON_COUNT
        if is_flag_set(NewsItem.FLAG_ACTION_FOLLOW, item_flags):
            max_button_count -= 1
        if is_flag_set(NewsItem.FLAG_ACTION_ROGERTHAT, item_flags):
            max_button_count -= 1
        if len(buttons) > max_button_count:
            raise TooManyNewsButtonsException()

        news_item.buttons = buttons
        news_item.flags = item_flags
        if tags and is_set(tags):
            news_item.tags = tags
        else:
            news_item.tags = [u'news']
        news_item.update_timestamp = now()
        news_item.order_timestamp = order_timestamp
        if news_item.scheduled_at:
            news_item.published_timestamp = news_item.scheduled_at
        else:
            news_item.published_timestamp = news_item.timestamp

        if not existing_news_item or not existing_news_item_published:
            if target_audience is not None:
                news_item.target_audience_enabled = True
                news_item.target_audience_min_age = target_audience.min_age
                news_item.target_audience_max_age = target_audience.max_age
                news_item.target_audience_gender = target_audience.gender
                news_item.connected_users_only = target_audience.connected_users_only
            else:
                news_item.target_audience_enabled = False

            if locations_set:
                news_item.has_locations = True
                news_item.location_match_required = locations.match_required
                for address in locations.addresses:
                    if address.level != NewsItemAddress.LEVEL_STREET:
                        raise BusinessException('Invalid address level: %s' % address.level)
                news_item.locations = NewsItemLocation(
                    geo_addresses=[NewsItemGeoAddress(
                        geo_location=ndb.GeoPt(geo_address.latitude, geo_address.longitude),
                        distance=geo_address.distance,
                    ) for geo_address in locations.geo_addresses],
                    addresses=[NewsItemAddress(
                        level=address.level,
                        country_code=address.country_code,
                        city=address.city,
                        zip_code=address.zip_code,
                        street_name=address.street_name,
                        address_uid=UserProfileInfoAddress.create_uid([address.country_code, address.zip_code,
                                                                       address.street_name])
                    ) for address in locations.addresses]
                )
            if not is_empty(group_visible_until):
                news_item.group_visible_until = None
                if news_item.scheduled_at:
                    if group_visible_until > news_item.scheduled_at:
                        news_item.group_visible_until = datetime.utcfromtimestamp(group_visible_until)
                elif group_visible_until > now():
                    news_item.group_visible_until = datetime.utcfromtimestamp(group_visible_until)

        to_put.append(news_item)
        map_service = MapService.create_key(sender.email()).get()  # type: MapService
        if map_service and not map_service.has_news:
            map_service.has_news = True
            to_put.append(map_service)
        ndb.put_multi(to_put)
        return news_item

    news_item = trans(existing_news_item.id if existing_news_item else None, news_type)

    # TODO homescreen: Update homescreens with news block
    if not news_item.published and is_set(scheduled_at) and scheduled_at != 0:
        if scheduled_at_changed or news_item.scheduled_task_name is None:
            schedule_news(news_item)
    else:
        deferred.defer(create_matches_for_news_item_key, news_item.key, old_group_ids, is_empty(news_id),
                       _transactional=db.is_in_transaction(),
                       _queue=NEWS_MATCHING_QUEUE)
        deferred.defer(re_index_news_item_by_key, news_item.key, _countdown=2, _queue=NEWS_MATCHING_QUEUE)

    return news_item


def get_and_validate_media_info(type_, content):
    media = MediaTO(type=type_, content=content)
    decoded_image = None
    if media.type == MediaType.IMAGE:
        if media.content.startswith('http'):
            # Allow http image urls on dev server
            if not DEBUG and not media.content.startswith('https://'):
                logging.debug('get_and_validate_media_info.from: %s', media.content)
                parsed_url = urlparse.urlparse(media.content)
                media.content = urlparse.urlunparse(('https',
                                                     parsed_url.netloc.split(':', 1)[0],
                                                     parsed_url.path,
                                                     parsed_url.params,
                                                     parsed_url.query,
                                                     parsed_url.fragment))
                logging.debug('get_and_validate_media_info.to: %s', media.content)
            try:
                image_result = urlfetch.fetch(media.content)  # type: urlfetch._URLFetchResult
                if image_result.status_code != 200:
                    raise Exception('Failed to download image')
                result = image_result.content
            except:
                logging.debug('Failed to download image', exc_info=True)
                raise BusinessException('Invalid image url. Please ensure the image is accessible via https.')

            img = images.Image(result)
            orig_width = img.width
            orig_height = img.height
            _validate_img_aspect_ratio(orig_width, orig_height)
        else:
            try:
                _meta, img_b64 = media.content.split(',')
                decoded_image = base64.b64decode(img_b64)
            except Exception as e:
                logging.debug(e, exc_info=True)
                raise BusinessException('Invalid image')

            image_type = imghdr.what(None, decoded_image)
            img = images.Image(decoded_image)
            orig_width = img.width
            orig_height = img.height
            _validate_img_aspect_ratio(orig_width, orig_height)

            orig_image = decoded_image
            size = min(100, 100 * 4000 / max(orig_width, orig_height))  # max 4000 wide/high
            while len(decoded_image) > IMAGE_MAX_SIZE:
                size -= size / 10
                if size < 10:
                    raise BusinessException('Image size too big')
                img = images.Image(orig_image)
                img.resize(orig_width * size / 100, orig_height * size / 100)
                decoded_image = img.execute_transforms(images.JPEG if image_type == 'jpeg' else images.PNG)
                logging.debug("transforming image size %s %s" % (size, len(decoded_image)))
        media.height = img.height
        media.width = img.width
    elif media.type == MediaType.VIDEO_YOUTUBE:
        embed_url = 'https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=%s&format=json' % media.content
        result = urlfetch.fetch(embed_url)  # type: urlfetch._URLFetchResult
        if result.status_code != 200:
            raise BusinessException('Invalid YouTube video. Please ensure the video is published.')
        if DEBUG:
            logging.debug('Video info: %s', result.content)
        try:
            video_info = json.loads(result.content)
            media.width = video_info['width']
            media.height = video_info['height']
        except ValueError:
            if result.content == 'Unauthorized':
                raise BusinessException('Please ensure playback on other websites has been enabled for the video.')
            else:
                logging.debug('Video info: %s', result.content)
                raise BusinessException('Invalid YouTube video. Please ensure the video is published.')
    return media, decoded_image


def _validate_img_aspect_ratio(width, height):
    aspect_ratio = float(width) / float(height)
    if aspect_ratio > 3 or aspect_ratio < 1.0 / 3.0:
        raise BusinessException('Image has an invalid aspect ratio, a maximum width/height ratio of 3 is allowed.')


def _save_models(models):
    db.put(models)


def schedule_news(news_item):
    # type: (NewsItem) -> None
    if news_item.scheduled_task_name:
        # remove the old scheduled task
        task_name = str(news_item.scheduled_task_name)
        taskqueue.Queue(SCHEDULED_QUEUE).delete_tasks_by_name(task_name)

    news_item_id = news_item.id
    task = deferred.defer(send_delayed_realtime_updates, news_item_id, _countdown=news_item.scheduled_at - now(),
                          _queue=SCHEDULED_QUEUE, _transactional=db.is_in_transaction())

    news_item.scheduled_task_name = task.name
    news_item.put()


# excuse the irony
def send_delayed_realtime_updates(news_item_id, *args):
    # type: (int, Any) -> None
    news_item = NewsItem.get_by_id(news_item_id)
    if not news_item:
        logging.warn('Scheduled news item %d not found', news_item_id)
        return
    if news_item.published:
        raise BusinessException('Not sending realtime news update for already published news item %d' % news_item_id)
    news_item.update_timestamp = now()  # to make sure the getNews call returns this news item
    news_item.published = True
    if news_item.status == NewsItem.STATUS_SCHEDULED:
        service_visible = get_service_visible_non_transactional(news_item.sender)
        news_item.status = NewsItem.STATUS_PUBLISHED if service_visible else NewsItem.STATUS_INVISIBLE
    news_item.put()

    re_index_news_item(news_item)
    create_matches_for_news_item(news_item, [], True)


def news_statistics(app_user, news_type, news_ids):
    # type: (users.User, unicode, List[int]) -> None
    # news_type is one NewsItemAction prefixed with 'news.'
    model_stats = []
    matches = {}

    news_ds_objects = get_news_by_ids(news_ids)
    for news_id, news_item in zip(news_ids, news_ds_objects):
        if not news_item:
            continue
        if news_type not in NewsStatisticAction.all():
            logging.error('Unexpected news statistics type: %s', news_type)
        model_stats.append({
            'id': news_id,
            'action': news_type.split('.')[1],
            'uid': guid()
        })

        if news_id not in matches:
            matches[news_id] = []
        matches[news_id].append(news_type.split('.')[1])

    try_or_defer(_save_statistics, app_user, model_stats, matches, datetime.utcnow(), _queue=NEWS_STATS_QUEUE)


def _save_statistics(app_user, model_stats, matches, action_date):
    # type: (users.User, Dict, Dict[int, List[str]], datetime) -> None
    models = save_statistics_to_matches(app_user, matches, action_date)
    models.extend(save_statistics_to_model(app_user, model_stats, action_date))
    ndb.put_multi(models)


def save_statistics_to_model(app_user, stats, action_date):
    user_profile = get_user_profile(app_user)
    age_lbl = NewsItemStatistics.get_age_label(NewsItemStatistics.get_age_index(user_profile.age))
    gender_index = NewsItemStatistics.get_gender_index(user_profile.gender)
    gender_lbl = NewsItemStatistics.gender_translation_key(gender_index)

    return [NewsItemActionStatistics(key=NewsItemActionStatistics.create_key(app_user, s['uid']),
                                     app_id=get_app_id_from_app_user(app_user),
                                     created=action_date,
                                     news_id=s['id'],
                                     action=s['action'],
                                     age=age_lbl,
                                     gender=gender_lbl) for s in stats]


def save_web_news_item_action_statistic(session, app_id, news_id, action, date):
    # type: (WebClientSession, str, int, str, datetime) -> None
    stats_key = NewsItemWebActions.create_key(session.key, news_id)
    stats = stats_key.get() or NewsItemWebActions(key=stats_key)
    should_save = stats.add_action(action, date)
    if should_save:
        item_stats = NewsItemActionStatistics(
            key=NewsItemActionStatistics.create_key(session.key, guid()),
            app_id=app_id,
            created=date,
            news_id=news_id,
            action=action
        )
        ndb.put_multi([stats, item_stats])


def save_statistics_to_matches(app_user, new_actions, action_date):
    to_put = []
    keys = list({NewsItemActions.create_key(app_user, news_id) for news_id in new_actions})
    models = {news_item_actions.news_id: news_item_actions for news_item_actions in ndb.get_multi(list(keys)) if news_item_actions}

    for news_id, actions in new_actions.iteritems():
        news_item_actions = models.get(news_id)
        should_save = False
        if not news_item_actions:
            news_item_actions = NewsItemActions.create(app_user, news_id)
            models[news_id] = news_item_actions

        for action in actions:
            remove_action = None
            if action == NewsItemAction.UNPINNED:
                remove_action = NewsItemAction.PINNED
            elif action == NewsItemAction.UNROGERED:
                remove_action = NewsItemAction.ROGERED
            elif action not in news_item_actions.actions:
                news_item_actions.add_action(action, action_date)
                should_save = True

            if remove_action and remove_action in news_item_actions.actions:
                news_item_actions.remove_action(remove_action)
                should_save = True

        if should_save:
            to_put.append(news_item_actions)
    return to_put


def processed_timeout_stickied_news():
    to_put = []
    for news_item in NewsItem.get_expired_sponsored_news_keys():
        news_item.sticky = False
        to_put.append(news_item)
    ndb.put_multi(to_put)


def create_notification(app_user, group_id=None, news_id=None, location_match=False):
    user_profile = get_user_profile(app_user)
    if not user_profile:
        return
    if not user_profile.mobiles:
        return
    lang = user_profile.language
    news_item = None
    si = None
    service = None
    if news_id:
        news_item = NewsItem.create_key(news_id).get()  # type: NewsItem
        si = get_service_identity(news_item.sender)
    if group_id:
        news_group, news_stream = ndb.get_multi([NewsGroup.create_key(group_id),
                                                 NewsStream.create_key(user_profile.community_id)])
        type_city = False
        if news_stream and news_stream.stream_type == NewsStream.TYPE_CITY:
            type_city = True

        if not news_group.send_notifications:
            logging.debug('debugging_news create_notification cancelled send_notifications was False')
            return
        group_title = get_group_title(type_city, news_group, lang)
        if news_item:
            if location_match:
                title = '%s - %s - %s' % (localize(lang, 'around_you'), group_title, si.name)
            else:
                title = '%s - %s' % (group_title, si.name)
            if news_item.type == NewsItem.TYPE_QR_CODE:
                short_message = news_item.qr_code_caption
                long_message = None
            else:
                short_message = news_item.title
                long_message = news_item.message

            if news_group.service_filter:
                service = remove_slash_default(news_item.sender).email()
        else:
            title = group_title
            short_message = localize(lang, 'new_news_available_for_group', group=group_title)
            long_message = None
    else:
        if si:
            title = si.name

        if not news_item:
            title = None
            short_message = localize(lang, 'new_news_available')
            long_message = None
        elif news_item.type == NewsItem.TYPE_QR_CODE:
            short_message = news_item.qr_code_caption
            long_message = None
        else:
            short_message = news_item.title
            long_message = news_item.message

    mobiles = db.get([get_mobile_key_by_account(mobile_detail.account) for mobile_detail in user_profile.mobiles])
    # Don't send these to client
    for mobile in mobiles:
        kwargs = {DO_NOT_SAVE_RPCCALL_OBJECTS: True, CAPI_KEYWORD_ARG_PRIORITY: PRIORITY_HIGH}
        if mobile.is_ios and mobile.iOSPushId:
            kwargs[CAPI_KEYWORD_ARG_APPLE_PUSH_MESSAGE] = _create_news_stream_notification(title, short_message,
                                                                                           news_id, group_id, service)
        elif mobile.is_android:
            kwargs[CAPI_KEYWORD_PUSH_DATA] = NewsStreamNotification(
                title, short_message, long_message, news_id, group_id, service)
        createNotification(create_notification_response_handler, logError, app_user,
                           request=CreateNotificationRequestTO(), MOBILE_ACCOUNT=mobile, **kwargs)


def _create_news_stream_notification(title, short_message, news_id, group_id, service):
    smaller_args = lambda args, too_big: [title, _ellipsize_for_json(args[1], _len_for_json(args[1]) - too_big)]
    notification = construct_push_notification('NM', [title, short_message], 'n.aiff', smaller_args, b=news_id,
                                               g=group_id, s=service)
    return base64.encodestring(notification)


@returns(unicode)
@arguments(news_item=(NewsItemTO, NewsStreamItemTO))
def create_push_notification(news_item):
    sender = news_item.sender.name
    message = (news_item.title or u"").strip()
    if news_item.message:
        message += u"\n%s" % news_item.message.strip()

    smaller_args = lambda args, too_big: [sender, _ellipsize_for_json(args[1], _len_for_json(args[1]) - too_big)]
    return construct_push_notification('NM', [sender, message], 'n.aiff', smaller_args, b=news_item.id)


@returns(NewsItem)
@arguments(service_identity_user=users.User, news_id=(int, long))
def get_and_validate_news_item(news_id, service_identity_user):
    # type: (long, users.User) -> NewsItem
    """
    Returns news by an id

    Args:
        service_identity_user (users.User)
        news_id (long)
    Returns:
        NewsItem
    Raises:
        NoPermissionToNewsException
        NewsNotFoundException
    """
    news_item = NewsItem.get_by_id(news_id)
    if not news_item or news_item.deleted:
        raise NewsNotFoundException(news_id)
    if news_item.sender != service_identity_user:
        raise NoPermissionToNewsException(service_identity_user.email())
    return news_item


def get_and_validate_news_items(news_ids, service_identity_user):
    # type: (List[long], users.User) -> List[NewsItem]
    """
    Returns news by id

    Raises:
        NoPermissionToNewsException: raised when user has no permission to this news.
        NewsNotFoundException: raised when news was not found with specified id
    """
    news_items = ndb.get_multi([NewsItem.create_key(news_id) for news_id in news_ids])  # type: List[NewsItem]
    for news_id, news_item in zip(news_ids, news_items):
        if not news_item or news_item.deleted:
            raise NewsNotFoundException(news_id)
        if news_item.sender != service_identity_user:
            raise NoPermissionToNewsException(service_identity_user.email())
    return news_items


@returns()
@arguments(service_identity_user=users.User, news_id=(int, long), members=[BaseMemberTO])
def disable_news(service_identity_user, news_id, members):
    get_and_validate_news_item(news_id, service_identity_user)
    for members_50 in chunks(members, 50):
        deferred.defer(send_disable_news_request_to_users, news_id, members_50)

    to_put = []
    for member in members:
        app_user = create_app_user(users.User(member.member), member.app_id)
        news_item_actions = NewsItemActions.create_key(app_user, news_id).get()
        if not news_item_actions:
            news_item_actions = NewsItemActions.create(app_user, news_id)
        news_item_actions.disabled = True
        to_put.append(news_item_actions)

    put_in_chunks(to_put, is_ndb=True)


@returns()
@arguments(news_id=(int, long), members=[BaseMemberTO])
def send_disable_news_request_to_users(news_id, members):
    """
    Args:
        news_id (int)
        members (list of BaseMemberTO)
    """
    request = DisableNewsRequestTO(news_id)
    for member in members:
        app_user = create_app_user(users.User(member.member), member.app_id)
        disableNews(disable_news_response_handler, logError, app_user, request=request)


@mapping('com.mobicage.capi.news.disable_news_response_handler')
@returns(NoneType)
@arguments(context=RpcCAPICall, result=DisableNewsResponseTO)
def disable_news_response_handler(context, result):
    pass


@mapping('com.mobicage.capi.news.create_notification_response_handler')
@returns(NoneType)
@arguments(context=RpcCAPICall, result=CreateNotificationResponseTO)
def create_notification_response_handler(context, result):
    pass


@mapping('com.mobicage.capi.news.update_badge_count_response_handler')
@returns(NoneType)
@arguments(context=RpcCAPICall, result=UpdateBadgeCountResponseTO)
def update_badge_count_response_handler(context, result):
    pass


@returns(bool)
@arguments(news_id=(int, long), service_identity_user=users.User)
def delete(news_id, service_identity_user):
    """
    Args:
        news_id (long)
        service_identity_user (users.User)

    Returns:
        bool: True if the item existed when trying to delete, else False

    Raises:
        NoPermissionToNewsException: raised when user has no permission to this news.
    """
    to_delete = []
    try:
        news_item = get_and_validate_news_item(news_id, service_identity_user)
    except NewsNotFoundException:
        return False

    if news_item.published:
        news_item.deleted = True
        news_item.status = NewsItem.STATUS_DELETED
        news_item.update_timestamp = now()
        news_item.put()
        re_index_news_item(news_item)
        do_callback_for_delete(news_item.sender, news_id)
        return True
    if news_item.media and news_item.media.content:
        to_delete.append(NewsItemImage.create_key(news_item.media.content))
    if news_item.scheduled_task_name:
        taskqueue.Queue(SCHEDULED_QUEUE).delete_tasks_by_name(str(news_item.scheduled_task_name))
    to_delete.append(news_item.key)
    ndb.delete_multi(to_delete)
    return True


def do_callback_for_create(news_item):
    from rogerthat.service.api.news import news_created
    news_item_to, service_identity, service_profile = _get_news_item_to(news_item)
    news_created(None, logServiceError, service_profile, news_item=news_item_to,
                 service_identity=service_identity.identifier)


def _get_news_item_to(news_item):
    # type: (NewsItem) -> Tuple[NewsItemTO, ServiceIdentity, ServiceProfile]
    service_user = get_service_user_from_service_identity_user(news_item.sender)
    service_profile = get_service_profile(service_user)
    service_identity = get_service_identity(news_item.sender)
    server_settings = get_server_settings()
    share_base_url = get_news_share_base_url(server_settings.webClientUrl, community_id=service_profile.community_id)
    share_url = get_news_share_url(share_base_url, news_item.id)
    news_item_to = NewsItemTO.from_model(news_item, server_settings.baseUrl, service_profile, service_identity,
                                         share_url=share_url)
    return news_item_to, service_identity, service_profile


def do_callback_for_update(news_item):
    from rogerthat.service.api.news import news_updated
    news_item_to, service_identity, service_profile = _get_news_item_to(news_item)
    news_updated(None, logServiceError, service_profile, news_item=news_item_to,
                 service_identity=service_identity.identifier)


def do_callback_for_delete(service_identity_user, news_id):
    from rogerthat.service.api.news import news_deleted
    service_user, service_identity = get_service_identity_tuple(service_identity_user)
    news_deleted(None, logServiceError, get_service_profile(service_user), news_id=news_id,
                 service_identity=service_identity)
