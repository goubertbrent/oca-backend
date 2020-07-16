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
import random
import urllib2
import urlparse
from datetime import datetime
from types import NoneType

from google.appengine.api import urlfetch, images, taskqueue
from google.appengine.ext import db, ndb
from google.appengine.ext.deferred import deferred
from google.appengine.ext.ndb.query import Cursor
from typing import List, Dict, Tuple

from mcfw.consts import MISSING
from mcfw.rpc import returns, arguments
from mcfw.utils import chunks
from rogerthat.bizz.job import run_job
from rogerthat.bizz.log_analysis import NEWS_CREATED, NEWS_ROGERED, NEWS_REACHED, NEWS, NEWS_SPONSORING_TIMED_OUT, \
    NEWS_UPDATED, NEWS_NEW_FOLLOWER, NEWS_ACTION
from rogerthat.bizz.messaging import ALLOWED_BUTTON_ACTIONS, UnsupportedActionTypeException, _ellipsize_for_json, \
    _len_for_json
from rogerthat.bizz.news.groups import get_group_types_for_service, \
    get_group_ids_for_type, get_group_info, validate_group_type
from rogerthat.bizz.news.matching import create_matches_for_news_item, \
    setup_default_settings, block_matches, reactivate_blocked_matches, \
    delete_news_matches, enabled_filter, disable_filter, update_visibility_news_matches, \
    update_badge_count_user, create_matches_for_news_item_key
from rogerthat.bizz.news.searching import find_news, re_index_news_item, re_index_news_item_by_key
from rogerthat.bizz.service import _validate_roles
from rogerthat.capi.news import disableNews, createNotification
from rogerthat.consts import SCHEDULED_QUEUE, DEBUG, NEWS_STATS_QUEUE, NEWS_MATCHING_QUEUE
from rogerthat.dal import put_in_chunks
from rogerthat.dal.mobile import get_mobile_key_by_account
from rogerthat.dal.profile import get_user_profile, get_service_profile, get_service_profiles
from rogerthat.dal.service import get_service_identity, \
    ndb_get_service_menu_items, get_service_identities_not_cached, get_default_service_identity
from rogerthat.exceptions.news import NewsNotFoundException, CannotUnstickNewsException, TooManyNewsButtonsException, \
    CannotChangePropertyException, MissingNewsArgumentException, InvalidNewsTypeException, NoPermissionToNewsException, \
    ValueTooLongException, DemoServiceException, InvalidScheduledTimestamp, \
    EmptyActionButtonCaption, InvalidActionButtonRoles, InvalidActionButtonFlowParamsException
from rogerthat.models import ServiceProfile, PokeTagMap, ServiceMenuDef, NdbApp, \
    UserProfileInfoAddress, NdbProfile, UserProfileInfo, NdbUserProfile, ServiceIdentity, NdbServiceProfile
from rogerthat.models.maps import MapService
from rogerthat.models.news import NewsItem, NewsItemImage, NewsItemActionStatistics, NewsGroup, NewsSettingsUser, \
    NewsItemMatch, NewsSettingsService, NewsSettingsUserService, \
    NewsMedia, NewsStream, NewsItemLocation, NewsItemGeoAddress, NewsItemAddress, \
    NewsNotificationStatus, NewsNotificationFilter, NewsStreamCustomLayout, NewsItemAction, MediaType, \
    NewsSettingsUserGroup, NewsSettingsServiceGroup
from rogerthat.models.properties.news import NewsItemStatistics, NewsStatisticPerApp, NewsButtons, NewsButton
from rogerthat.models.utils import ndb_allocate_id
from rogerthat.rpc import users
from rogerthat.rpc.models import RpcCAPICall
from rogerthat.rpc.rpc import logError, mapping, CAPI_KEYWORD_ARG_PRIORITY, PRIORITY_HIGH, \
    CAPI_KEYWORD_ARG_APPLE_PUSH_MESSAGE, CAPI_KEYWORD_PUSH_DATA, DO_NOT_SAVE_RPCCALL_OBJECTS
from rogerthat.rpc.service import BusinessException, logServiceError
from rogerthat.settings import get_server_settings
from rogerthat.to.messaging import BaseMemberTO
from rogerthat.to.news import NewsActionButtonTO, NewsItemTO, NewsItemListResultTO, DisableNewsRequestTO, \
    DisableNewsResponseTO, NewsTargetAudienceTO, \
    NewsItemAppStatisticsTO, NewsItemStatisticsTO, BaseMediaTO, MediaTO, \
    GetNewsGroupsResponseTO, IfEmtpyScreenTO, NewsGroupRowTO, NewsGroupTO, NewsGroupTabInfoTO, NewsGroupFilterInfoTO, \
    NewsGroupLayoutTO, GetNewsStreamItemsResponseTO, NewsStreamItemTO, GetNewsGroupServicesResponseTO, NewsSenderTO, \
    SaveNewsGroupServicesResponseTO, SaveNewsGroupFiltersResponseTO, CreateNotificationRequestTO, \
    CreateNotificationResponseTO, NewsLocationsTO, UpdateBadgeCountResponseTO, GetNewsGroupResponseTO
from rogerthat.to.push import NewsStreamNotification
from rogerthat.translations import localize
from rogerthat.utils import now, slog, is_flag_set, try_or_defer, guid, bizz_check
from rogerthat.utils.app import get_app_id_from_app_user, create_app_user
from rogerthat.utils.iOS import construct_push_notification
from rogerthat.utils.service import add_slash_default, get_service_user_from_service_identity_user, \
    remove_slash_default, get_service_identity_tuple
from rogerthat.utils.transactions import run_in_transaction

_DEFAULT_LIMIT = 100
ALLOWED_NEWS_BUTTON_ACTIONS = list(ALLOWED_BUTTON_ACTIONS) + ['poke']
IMAGE_MAX_SIZE = 409600  # 400kb


def create_default_news_settings(service_user, organization_type):
    nss_key = NewsSettingsService.create_key(service_user)
    nss = nss_key.get()
    if nss:
        return

    si = get_default_service_identity(service_user)
    nss = NewsSettingsService(key=nss_key)
    nss.default_app_id = si.app_id
    nss.groups = []
    ns = NewsStream.create_key(nss.default_app_id).get()
    if organization_type and organization_type == ServiceProfile.ORGANIZATION_TYPE_CITY:
        nss.setup_needed_id = 1
    else:
        group_types = []
        if ns:
            for ng in NewsGroup.list_by_app_id(nss.default_app_id):
                group_types.append(ng.group_type)

        if NewsGroup.TYPE_PROMOTIONS in group_types:
            nss.groups.append(NewsSettingsServiceGroup(group_type=NewsGroup.TYPE_PROMOTIONS,
                                                       filter=NewsGroup.FILTER_PROMOTIONS_OTHER))
        if NewsGroup.TYPE_EVENTS in group_types:
            nss.groups.append(NewsSettingsServiceGroup(group_type=NewsGroup.TYPE_EVENTS,
                                                       filter=None))
        if nss.groups:
            nss.setup_needed_id = 0
        else:
            nss.setup_needed_id = random.randint(2, 10)
    nss.put()

    if ns and not ns.services_need_setup and nss.setup_needed_id != 0:
        ns.services_need_setup = True
        ns.put()


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
    news_item.put()
    delete_news_matches(news_item.id)
    re_index_news_item(news_item)


def update_visibility_news_items(service_identity_user, visible):
    run_job(_query_news_items_service, [service_identity_user],
            _worker_update_visibility_news_items, [visible],
            worker_queue=NEWS_MATCHING_QUEUE)


def _worker_update_visibility_news_items(ni_key, visible):
    news_item = ni_key.get()
    update_visibility_news_matches(news_item.id, visible)
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
    app_id = get_app_id_from_app_user(app_user)

    response = GetNewsGroupsResponseTO(rows=[], if_empty=None, has_locations=False)
    up, profile_info, news_user_settings, news_stream = ndb.get_multi([NdbProfile.createKey(app_user),
                                                                       UserProfileInfo.create_key(app_user),
                                                                       NewsSettingsUser.create_key(app_user),
                                                                       NewsStream.create_key(app_id)])
    lang = up.language
    fresh_setup = False if news_user_settings else True
    if fresh_setup:
        news_user_settings = setup_default_settings(app_user, set_last_used=True)
        if news_user_settings.group_ids:
            # In case of an app update we need to reset the badge count
            deferred.defer(update_badge_count_user, app_user, news_user_settings.group_ids[0], 0)

    else:
        news_user_settings.last_get_groups_request = datetime.utcnow()
        news_user_settings.put()

    if not news_user_settings.groups:
        logging.debug('debugging_news get_groups_for_user no groups user:%s', app_user)
        response.if_empty = IfEmtpyScreenTO(title=localize(lang, u'No news yet'),
                                            message=localize(lang, u"News hasn't been setup yet for this app"))

        return response

    response.has_locations = has_profile_addresses(profile_info)

    keys = [NewsGroup.create_key(group_id) for group_id in news_user_settings.group_ids]
    if news_stream:
        news_stream_layout = news_stream.layout
        if news_stream.custom_layout_id:
            keys.append(NewsStreamCustomLayout.create_key(news_stream.custom_layout_id, app_id))
    else:
        news_stream_layout = None
    models = ndb.get_multi(keys)
    if news_stream and news_stream.custom_layout_id:
        custom_layout = models.pop()
        if custom_layout and custom_layout.layout:
            news_stream_layout = custom_layout.layout
    news_groups_mapping = {group.group_id: group for group in models}  # type: Dict[str, NewsGroup]

    base_url = get_server_settings().baseUrl
    type_city = news_stream and news_stream.stream_type == NewsStream.TYPE_CITY
    row_data = {}

    badge_count_rpcs = {}
    for news_user_group in news_user_settings.groups:
        for group_details in news_user_group.details:
            if not fresh_setup:
                badge_count_rpcs[group_details.group_id] = NewsItemMatch.count_unread(app_user,
                                                                                      group_details.group_id,
                                                                                      group_details.last_load_request)

    si_users = _get_service_identity_users_for_groups(news_groups_mapping.values())
    service_profiles, services_identities = get_service_profiles_and_identities(si_users)
    for news_user_group in news_user_settings.get_groups_sorted():
        key = news_user_group.details[0].group_id if len(news_user_group.details) == 1 else news_user_group.group_type
        tabs = get_tabs_for_group(lang, news_groups_mapping, news_user_group)

        if not tabs:
            continue

        news_group = news_groups_mapping[tabs[0].key]

        badge_count_rpc = badge_count_rpcs.get(news_group.group_id)
        badge_count = badge_count_rpc and badge_count_rpc.get_result() or 0
        layout = get_layout_params_for_group(base_url, type_city, app_user, lang, news_group, badge_count)
        row_data[news_user_group.group_type] = NewsGroupTO(
            key=key,
            name=get_group_title(type_city, news_group, lang),
            if_empty=get_if_empty_for_group_type(news_user_group.group_type, lang),
            tabs=tabs,
            layout=layout,
            services=_get_news_group_services_from_mapping(base_url, news_group, service_profiles, services_identities)
        )

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
        for t in types:
            group_details = row_data.get(t)
            if group_details:
                row.items.append(group_details)
        if row.items:
            response.rows.append(row)
    return response


def get_tabs_for_group(lang, news_groups_mapping, news_user_group):
    # type: (str, Dict[str, NewsGroup], NewsSettingsUserGroup) -> List[NewsGroupTabInfoTO]
    tabs = []
    for group_details in news_user_group.get_details_sorted():
        news_group = news_groups_mapping.get(group_details.group_id)
        if not news_group:
            continue
        regional = news_group.regional
        tab = NewsGroupTabInfoTO(key=group_details.group_id,
                                 name=localize(lang, u'Regional') if regional else localize(lang, u'Local'),
                                 notifications=group_details.notifications,
                                 filters=[])

        for group_filter in news_group.filters:
            tab.filters.append(NewsGroupFilterInfoTO(key=group_filter,
                                                     name=group_filter,
                                                     enabled=group_filter in group_details.filters))

        tabs.append(tab)
    return tabs


def get_news_group_response(app_user, group_id):
    app_id = get_app_id_from_app_user(app_user)
    keys = [NewsStream.create_key(app_id), NewsGroup.create_key(group_id), NewsSettingsUser.create_key(app_user),
            NdbUserProfile.createKey(app_user)]
    models = ndb.get_multi(keys)  # type: Tuple[NewsStream, NewsGroup,NewsSettingsUser, NdbUserProfile]
    news_stream, news_group, user_group_settings, user_profile = models
    all_groups = ndb.get_multi([NewsGroup.create_key(i) for i in user_group_settings.group_ids])
    group_mapping = {group.group_id: group for group in all_groups}
    news_user_group = user_group_settings.get_group(group_id)
    base_url = get_server_settings().baseUrl
    lang = user_profile.language
    group_details = user_group_settings.get_group_details(group_id)
    if group_details:
        badge_count = NewsItemMatch.count_unread(app_user, group_id, group_details.last_load_request).get_result()
    else:
        badge_count = 0
    type_city = news_stream and news_stream.stream_type == NewsStream.TYPE_CITY

    si_users = _get_service_identity_users_for_groups([news_group])
    service_profiles, services_identities = get_service_profiles_and_identities(si_users)
    group = NewsGroupTO(
        key=group_id,
        name=get_group_title(type_city, news_group, lang),
        if_empty=get_if_empty_for_group_type(news_group.group_type, lang),
        tabs=get_tabs_for_group(lang, group_mapping, news_user_group),
        layout=get_layout_params_for_group(base_url, type_city, app_user, lang, news_group, badge_count),
        services=_get_news_group_services_from_mapping(base_url, news_group, service_profiles, services_identities),
    )
    return GetNewsGroupResponseTO(group=group)


def get_layout_params_for_group(base_url, type_city, app_user, lang, group, badge_count):
    # type: (str, str, users.User, str, NewsGroup, int) -> NewsGroupLayoutTO
    layout = NewsGroupLayoutTO()
    layout.badge_count = badge_count

    if group.tile:
        layout.background_image_url = group.tile.background_image_url
        layout.promo_image_url = group.tile.promo_image_url
    layout.title = get_group_title(type_city, group, lang)
    layout.subtitle = get_group_subtitle(type_city, group, lang)

    if group.group_type != NewsGroup.TYPE_PROMOTIONS:
        return layout

    # todo news_stream last promoted news item instead of last item
    ni = get_latest_item_for_user_by_group(app_user, group.group_id)
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
@arguments(app_user=users.User, group_id=unicode)
def get_latest_item_for_user_by_group(app_user, group_id):
    nm = NewsItemMatch.list_visible_by_group_id(app_user, group_id).get()
    if not nm:
        return None
    return NewsItem.get_by_id(nm.news_id)


def _save_last_load_request_news_group(app_user, group_id, d):
    nsu = NewsSettingsUser.create_key(app_user).get()
    if not nsu:
        return
    details = nsu.get_group_details(group_id)
    if not details:
        return

    details.last_load_request = d
    nsu.put()


@returns(GetNewsStreamItemsResponseTO)
@arguments(app_user=users.User, group_id=unicode, cursor=unicode, news_ids=[(int, long)])
def get_items_for_user_by_group(app_user, group_id, cursor, news_ids):
    if cursor is None:
        deferred.defer(_save_last_load_request_news_group, app_user, group_id, datetime.utcnow())
        deferred.defer(update_badge_count_user, app_user, group_id, 0)

    r = GetNewsStreamItemsResponseTO(cursor=None, items=[], group_id=group_id)
    batch_count = 50 if cursor else 10

    if group_id == u'pinned':
        qry = NewsItemMatch.list_by_action(app_user, NewsItemAction.PINNED)
    else:
        qry = NewsItemMatch.list_visible_by_group_id(app_user, group_id)
    news_ids = list(news_ids)  # making a copy to not alter the news_ids list of the request
    items, new_cursor, has_more = qry.fetch_page(
        batch_count, start_cursor=Cursor.from_websafe_string(cursor) if cursor else None, keys_only=True)
    for item in items:
        if item.id() not in news_ids:
            news_ids.append(item.id())
    if has_more:
        r.cursor = new_cursor.to_websafe_string().decode('utf-8') if new_cursor else None
    else:
        r.cursor = None

    r.items = _get_news_stream_items_for_user(app_user, news_ids, None if group_id == u'pinned' else group_id)
    return r


@returns(GetNewsStreamItemsResponseTO)
@arguments(app_user=users.User, service_identity_email=unicode, group_id=unicode, cursor=unicode)
def get_items_for_user_by_service(app_user, service_identity_email, group_id=None, cursor=None):
    if group_id and cursor is None:
        deferred.defer(_save_last_load_request_news_group, app_user, group_id, datetime.utcnow())
        deferred.defer(update_badge_count_user, app_user, group_id, 0)

    batch_count = 50 if cursor else 10
    app_id = get_app_id_from_app_user(app_user)

    service_identity_user = add_slash_default(users.User(service_identity_email))
    if group_id:
        qry = NewsItemMatch.list_visible_by_sender_and_group_id(app_user, service_identity_user, group_id)
    else:
        qry = NewsItem.list_published_by_sender(service_identity_user, app_id, keys_only=True)

    items, new_cursor, has_more = qry.fetch_page(
        batch_count, start_cursor=Cursor.from_websafe_string(cursor) if cursor else None, keys_only=True)

    r = GetNewsStreamItemsResponseTO()
    r.group_id = group_id
    if has_more:
        r.cursor = new_cursor.to_websafe_string().decode('utf-8') if new_cursor else None
    else:
        r.cursor = None
    r.items = _get_news_stream_items_for_user(app_user, [ni_key.id() for ni_key in items], group_id)
    return r


@returns(GetNewsStreamItemsResponseTO)
@arguments(app_user=users.User, search_string=unicode, cursor=unicode)
def get_items_for_user_by_search_string(app_user, search_string, cursor):
    r = GetNewsStreamItemsResponseTO(cursor=None, items=[])
    if not search_string:
        return r
    news_r = find_news(get_app_id_from_app_user(app_user), search_string, cursor)
    if not news_r:
        return r
    results, new_cursor = news_r
    news_ids = []
    for result in results:
        news_ids.append(long(result.fields[0].value))
    r.cursor = new_cursor
    r.items = _get_news_stream_items_for_user(app_user, news_ids, None)
    return r


@returns([NewsStreamItemTO])
@arguments(app_user=users.User, ids=[(int, long)], group_id=unicode)
def _get_news_stream_items_for_user(app_user, ids, group_id):
    news_items = get_news_by_ids(ids)
    base_url = get_server_settings().baseUrl
    service_profiles, service_identities = get_service_profiles_and_identities(list({item.sender
                                                                                     for item in news_items}))

    news_items_dict = {news_item.id: NewsItemTO.from_model(
        news_item,
        base_url,
        service_profiles[get_service_user_from_service_identity_user(news_item.sender)],
        service_identities[news_item.sender]
    ) for news_item in news_items}

    if group_id:
        model_keys = []
        for news_id in ids:
            service_identity_user = add_slash_default(users.User(news_items_dict[news_id].sender.email))
            model_keys.append(NewsItemMatch.create_key(app_user, news_id))
            model_keys.append(NewsSettingsUserService.create_key(app_user, group_id, service_identity_user))

        models = ndb.get_multi(model_keys)
        items = []
        for news_id, chunk_ in zip(ids, chunks(models, 2)):
            match, news_settings = chunk_  # type: (NewsItemMatch, NewsSettingsUserService)
            notifications = news_settings.notifications if news_settings else NewsNotificationStatus.NOT_SET
            blocked = news_settings.blocked if news_settings else False
            items.append(NewsStreamItemTO.from_model(app_user, match, news_items_dict[news_id], notifications,
                                                     blocked))
        return items
    else:
        matches = ndb.get_multi([NewsItemMatch.create_key(app_user, news_id) for news_id in ids])
        return [NewsStreamItemTO.from_model(app_user, match, news_items_dict[news_id])
                for news_id, match in zip(ids, matches)]


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
    elif key == u'blocked':
        qry = NewsSettingsUserService.list_blocked(app_user, group_id)
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
    s = NewsSettingsUser.create_key(app_user).get()
    if not s:
        return SaveNewsGroupServicesResponseTO()

    if service:
        should_put = False
        service_identity_user = add_slash_default(users.User(service))
        nsus_key = NewsSettingsUserService.create_key(app_user, group_id, service_identity_user)
        nsus = nsus_key.get()
        if not nsus:
            nsus = NewsSettingsUserService(key=nsus_key,
                                           group_id=group_id,
                                           notifications=NewsNotificationStatus.NOT_SET,
                                           blocked=False)

        if key == u'notifications':
            group_details = s.get_group_details(group_id)
            default_notification = group_details.notifications if group_details else None
            if action == u'enable':
                if default_notification == NewsNotificationFilter.ALL:
                    nsus.notifications = NewsNotificationStatus.NOT_SET
                else:
                    nsus.notifications = NewsNotificationStatus.ENABLED
                should_put = True
            elif action == u'disable':
                if default_notification == NewsNotificationFilter.SPECIFIED:
                    nsus.notifications = NewsNotificationStatus.NOT_SET
                else:
                    nsus.notifications = NewsNotificationStatus.DISABLED
                should_put = True
        elif key == u'blocked':
            if action == u'block':
                nsus.blocked = True
                should_put = True
                block_matches(app_user, service_identity_user, group_id)
            elif action == u'unblock':
                nsus.blocked = False
                should_put = True
                reactivate_blocked_matches(app_user, service_identity_user, group_id)

        if should_put:
            nsus.put()
    elif key == u'notifications':
        if action in (NewsSettingsUser.NOTIFICATION_ENABLED_FOR_NONE,
                      NewsSettingsUser.NOTIFICATION_ENABLED_FOR_ALL,
                      NewsSettingsUser.NOTIFICATION_ENABLED_FOR_SPECIFIED):
            group_details = s.get_group_details(group_id)
            if group_details:
                group_details.notifications = NewsSettingsUser.FILTER_MAPPING[action]
                s.put()
        else:
            logging.error('Unexpected action "%s" for key "%s"', action, key)

    return SaveNewsGroupServicesResponseTO()


@returns(SaveNewsGroupFiltersResponseTO)
@arguments(app_user=users.User, group_id=unicode, enabled_filters=[unicode])
def save_group_filters(app_user, group_id, enabled_filters):
    s = NewsSettingsUser.create_key(app_user).get()
    if not s:
        return SaveNewsGroupFiltersResponseTO()

    d = s.get_group_details(group_id)
    if d:
        filter_matches = list(set(enabled_filters) & set(d.filters))
        if len(filter_matches) != len(enabled_filters):
            for f in enabled_filters:
                if f not in d.filters:
                    enabled_filter(app_user, group_id, f)
            for f in d.filters:
                if f not in enabled_filters:
                    disable_filter(app_user, group_id, f)
            d.filters = enabled_filters
            s.put()

    return SaveNewsGroupFiltersResponseTO()


@returns(NewsItemListResultTO)
@arguments(cursor=unicode, batch_count=(int, long), service_identity_user=users.User, updated_since=(int, long),
           tag=unicode)
def get_news_by_service(cursor, batch_count, service_identity_user, updated_since=0, tag=None):
    service_user = get_service_user_from_service_identity_user(service_identity_user)
    base_url = get_server_settings().baseUrl

    qry = NewsItem.list_by_sender(service_identity_user, updated_since, tag)
    c = ndb.Cursor.from_websafe_string(cursor) if cursor else None
    results, new_cursor, has_more = qry.fetch_page(batch_count,
                                                   start_cursor=c)  # type: List[NewsItem], ndb.Cursor, bool
    news_items = replace_hashed_news_button_tags_with_real_tag(results, service_user)
    news_statistics_to_fill = []
    for news_item in news_items:
        if news_item.statistics_type and news_item.statistics_type == NewsItem.STATISTICS_TYPE_INFLUX_DB:
            continue
        if news_item.follow_count >= 0:
            continue
        news_statistics_to_fill.append(news_item.id)

    for news_id in news_statistics_to_fill:
        deferred.defer(setup_news_statistics_count_for_news_id, news_id)
    r_cursor = new_cursor and new_cursor.to_websafe_string().decode('utf-8')
    service_profile = get_service_profile(service_user)
    service_identity = get_service_identity(service_identity_user)
    return NewsItemListResultTO(news_items, has_more, r_cursor, base_url, service_profile, service_identity)


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


@returns()
@arguments(news_id=(int, long))
def setup_news_statistics_count_for_news_id(news_id):

    def trans():
        news_item = NewsItem.get_by_id(news_id)
        setup_news_statistics_count_for_news_item(news_item)
        news_item.put()

    run_in_transaction(trans)


@returns()
@arguments(news_item=NewsItem)
def setup_news_statistics_count_for_news_item(news_item):
    news_item.follow_count = 0
    news_item.action_count = 0
    for _, stats in news_item.statistics.iteritems():
        news_item.follow_count += stats.followed_total
        news_item.action_count += stats.action_total


def get_news_items_statistics(news_items, include_details=False):
    # type: (List[NewsItem], bool) -> List[NewsItemStatisticsTO]
    from rogerthat.bizz.news.influx import get_news_items_statistics as get_news_items_statistics_influx
    stats_per_news_item = {}
    influx_items = []
    for news_item in news_items:
        if news_item.statistics_type == NewsItem.STATISTICS_TYPE_INFLUX_DB:
            influx_items.append(news_item)
        else:
            stats_per_news_item[news_item.id] = transform_ds_news_statistics(news_item, include_details)

    if influx_items:
        try:
            stats_per_news_item.update(get_news_items_statistics_influx(influx_items, include_details))
        except Exception as e:
            if DEBUG:
                logging.exception(e.message)
            else:
                raise

    return [stats_per_news_item.get(news_item.id) for news_item in news_items]


@returns([(NewsItem, NoneType)])
@arguments(news_ids=[(int, long)])
def get_news_by_ids(news_ids):
    # type: (List[int]) -> List[NewsItem]
    return ndb.get_multi([NewsItem.create_key(i) for i in news_ids])


def validate_menu_item_roles(service_identity_user, role_ids, tag):
    items = ndb_get_service_menu_items(service_identity_user)
    for item in items:
        if item.tag == tag:
            for role_id in item.roles:
                if role_id not in role_ids:
                    raise InvalidActionButtonRoles()


@ndb.non_transactional()
def _get_group_info(service_identity_user, group_type=None, app_ids=None, news_item=None):
    try:
        return get_group_info(service_identity_user,
                              group_type=group_type,
                              app_ids=app_ids,
                              news_item=news_item)
    except:
        logging.debug('debugging_news _get_group_info', exc_info=True)

    return [], []


@returns(NewsItem)
@arguments(sender=users.User, sticky=bool, sticky_until=(int, long), title=unicode, message=unicode,
           image=unicode, news_type=int, news_buttons=[NewsActionButtonTO],
           qr_code_content=unicode, qr_code_caption=unicode, app_ids=[unicode], scheduled_at=(int, long),
           flags=int, news_id=(int, long, NoneType), target_audience=NewsTargetAudienceTO, role_ids=[(int, long)],
           tags=[unicode], media=BaseMediaTO, locations=NewsLocationsTO, group_type=unicode,
           group_visible_until=(int, long, NoneType), timestamp=(int, long, NoneType))
def put_news(sender, sticky, sticky_until, title, message, image, news_type, news_buttons,
             qr_code_content, qr_code_caption, app_ids, scheduled_at, flags, news_id=None, target_audience=None,
             role_ids=None, tags=None, media=MISSING, locations=None, group_type=MISSING,
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
        app_ids (list of unicode): List of apps where the news should be shown. Apps can only be added, not removed.
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
    server_settings = get_server_settings()

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
        if is_empty(app_ids):
            raise MissingNewsArgumentException(u'app_ids')

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
                    validate_menu_item_roles(sender, role_ids, btn.action[6:])
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

    @ndb.non_transactional()
    def get_service_identity_non_transactional():
        return get_service_identity(sender)

    si = get_service_identity_non_transactional()
    default_app = NdbApp.create_key(si.defaultAppId).get()
    if default_app.demo:
        for app in ndb.get_multi([NdbApp.create_key(i) for i in app_ids]):
            if not app.demo:
                raise DemoServiceException(app.app_id)

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
    if not existing_news_item or not existing_news_item_published:
        if role_ids:
            _validate_roles(service_user, role_ids)

    locations_set = not is_empty(locations)

    group_types, group_ids = _get_group_info(sender,
                                             group_type=group_type,
                                             app_ids=list(set(app_ids)) if app_ids and app_ids is not MISSING else [],
                                             news_item=existing_news_item)

    # noinspection PyShadowingNames
    @ndb.transactional(xg=True)
    def trans(news_item_id, news_type):
        news_item = None
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
        send_to_app_ids = set(app_ids) if app_ids and app_ids is not MISSING else set()

        order_timestamp = max(scheduled_at, now())
        if news_item:
            if not news_item.sticky and sticky:
                news_item.sticky = sticky
                news_item.sticky_until = sticky_until
            for app_id in news_item.app_ids:
                send_to_app_ids.add(app_id)
            news_item.app_ids = list(send_to_app_ids)
            news_item.version += 1

            if not is_set(flags):
                item_flags = news_item.flags
            else:
                item_flags = flags

            # set the new scheduling timestamp if it has changed only
            if not news_item.published and scheduled_at_changed:
                news_item.scheduled_at = scheduled_at
        else:
            if server_settings.news_statistics_influxdb_host:
                statistics_type = NewsItem.STATISTICS_TYPE_INFLUX_DB
            else:
                statistics_type = None

            default_statistics = NewsStatisticPerApp()
            for app_id in send_to_app_ids:
                default_statistics[app_id] = NewsItemStatistics.default_statistics()

            if not is_set(flags):
                item_flags = NewsItem.DEFAULT_FLAGS
            else:
                item_flags = flags

            news_item = NewsItem(key=NewsItem.create_key(ndb_allocate_id(NewsItem)),
                                 sticky=sticky,
                                 sticky_until=sticky_until if sticky else 0,
                                 sender=sender,
                                 app_ids=list(send_to_app_ids),
                                 timestamp=now() if is_empty(timestamp) else timestamp,
                                 type=news_type,
                                 rogered=False,
                                 version=1,
                                 scheduled_at=scheduled_at,
                                 published=scheduled_at is 0,
                                 statistics_type=statistics_type,
                                 statistics=default_statistics)

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

            if role_ids is None:
                news_item.role_ids = []
            else:
                news_item.role_ids = role_ids

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
    action = NEWS_CREATED if not news_id else NEWS_UPDATED
    slog('News item saved', sender.email(), NEWS, action=action, news_id=news_item.id, app_ids=news_item.app_ids,
         sticky=sticky)

    if not news_item.published and is_set(scheduled_at) and scheduled_at != 0:
        if scheduled_at_changed or news_item.scheduled_task_name is None:
            schedule_news(news_item, sender, si.descriptionBranding)
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
        video_info = json.loads(result.content)
        media.width = video_info['width']
        media.height = video_info['height']
    return media, decoded_image


def _validate_img_aspect_ratio(width, height):
    aspect_ratio = float(width) / float(height)
    if aspect_ratio > 3 or aspect_ratio < 1.0 / 3.0:
        raise BusinessException('Image has an invalid aspect ratio, a maximum width/height ratio of 3 is allowed.')


def _save_models(models):
    db.put(models)


def schedule_news(news_item, sender, description_branding):
    """
    Args:
        description_branding:
        news_item (NewsItem)
        sender (users.User): service identity user
    """
    if news_item.scheduled_task_name:
        # remove the old shceduled task
        task_name = str(news_item.scheduled_task_name)
        taskqueue.Queue(SCHEDULED_QUEUE).delete_tasks_by_name(task_name)

    news_item_id = news_item.id
    task = deferred.defer(send_delayed_realtime_updates, news_item_id, sender,
                          description_branding, _countdown=news_item.scheduled_at - now(),
                          _queue=SCHEDULED_QUEUE, _transactional=db.is_in_transaction())

    news_item.scheduled_task_name = task.name
    news_item.put()


# excuse the irony
def send_delayed_realtime_updates(news_item_id, sender, *args):
    """
    Args:
        news_item_id (long)
        sender (users.User): service identity user
    """
    news_item = NewsItem.get_by_id(news_item_id)
    if not news_item:
        logging.warn('Scheduled news item %d not found', news_item_id)
        return
    if news_item.published:
        raise BusinessException('Not sending realtime news update for already published news item %d' % news_item_id)
    news_item.update_timestamp = now()  # to make sure the getNews call returns this news item
    news_item.published = True
    news_item.put()

    re_index_news_item(news_item)
    create_matches_for_news_item(news_item, [], True)


@returns()
@arguments(app_user=users.User, news_type=unicode, news_ids=[(int, long)])
def news_statistics(app_user, news_type, news_ids):
    app_id = get_app_id_from_app_user(app_user)

    stats = {
        'news_item': [],
        'model': [],
        'matches': {}
    }

    news_ds_objects = get_news_by_ids(news_ids)
    for news_id, news_item in zip(news_ids, news_ds_objects):
        if not news_item:
            continue

        if news_item.statistics_type == NewsItem.STATISTICS_TYPE_INFLUX_DB:
            stats['model'].append({
                'id': news_id,
                'action': news_type.split('.')[1],
                'uid': guid()
            })
        else:
            stats['news_item'].append(news_id)

        if news_id not in stats['matches']:
            stats['matches'][news_id] = []
        stats['matches'][news_id].append(news_type.split('.')[1])

    if stats['news_item']:
        common_kwargs = {
            'news_ids': stats['news_item'],
            'app_id': app_id,
            'action': news_type
        }
        if news_type == NEWS_REACHED:
            # slog processing will increase news.reached and invalidate get_all_news
            slog('News items read', app_user.email(), NEWS, **common_kwargs)
        elif news_type == NEWS_ROGERED:
            # slog processing will add the user to news.users_that_rogered and set news.rogered=True
            # and invalidate get_all_news
            slog('News item rogered', app_user.email(), NEWS, **common_kwargs)
        elif news_type == NEWS_NEW_FOLLOWER:
            slog('New follower', app_user.email(), NEWS, **common_kwargs)
        elif news_type == NEWS_ACTION:
            slog('News action button pressed', app_user.email(), NEWS, **common_kwargs)

    if stats['model']:
        try_or_defer(save_statistics_to_model, app_user, stats['model'], datetime.utcnow(), _queue=NEWS_STATS_QUEUE)

    deferred.defer(save_statistics_to_matches, app_user, stats['matches'], _queue=NEWS_MATCHING_QUEUE)


def save_statistics_to_model(app_user, stats, action_date):
    user_profile = get_user_profile(app_user)
    age_lbl = NewsItemStatistics.get_age_label(NewsItemStatistics.get_age_index(user_profile.age))
    gender_index = NewsItemStatistics.get_gender_index(user_profile.gender)
    gender_lbl = NewsItemStatistics.gender_translation_key(gender_index)

    to_put = [NewsItemActionStatistics(key=NewsItemActionStatistics.create_key(app_user, s['uid']),
                                       created=action_date,
                                       news_id=s['id'],
                                       action=s['action'],
                                       age=age_lbl,
                                       gender=gender_lbl) for s in stats]
    put_in_chunks(to_put, is_ndb=True)


def save_statistics_to_matches(app_user, new_actions):
    to_put = []
    for news_id, actions in new_actions.iteritems():
        nm = NewsItemMatch.create_key(app_user, news_id).get()
        if not nm:
            ni = NewsItem.get_by_id(news_id)
            nm = NewsItemMatch.create(
                app_user, news_id, ni.stream_publish_timestamp, ni.stream_sort_timestamp, ni.sender)

        should_save = False
        for action in actions:
            remove_action = None
            if action == NewsItemAction.UNPINNED:
                remove_action = NewsItemAction.PINNED
            elif action == NewsItemAction.UNROGERED:
                remove_action = NewsItemAction.ROGERED
            elif action not in nm.actions:
                nm.actions.append(action)
                should_save = True

            if remove_action and remove_action in nm.actions:
                nm.actions.remove(remove_action)
                should_save = True

        if should_save:
            to_put.append(nm)

    put_in_chunks(to_put, is_ndb=True)


def transform_ds_news_statistics(news_item, include_details):
    # type: (NewsItem, bool) -> NewsItemStatisticsTO
    result = NewsItemStatisticsTO(news_item.id, users_that_rogered=[u.email() for u in news_item.users_that_rogered])
    if include_details:
        result.details = [NewsItemAppStatisticsTO.from_model(app_id, stats, news_item.timestamp)
                          for app_id, stats in news_item.statistics.iteritems()]
    for item in news_item.statistics:  # type: NewsItemStatistics
        result.total_action += item.action_total
        result.total_reached += item.reached_total
        result.total_followed += item.followed_total
    return result


@returns()
@arguments()
def processed_timeout_stickied_news():
    # slog processing will set news.sticky=False and invalidate get_all_news
    for key in NewsItem.get_expired_sponsored_news_keys().fetch(keys_only=True):
        slog('News item is no longer sticky', None, NEWS, action=NEWS_SPONSORING_TIMED_OUT, news_id=key.id())


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
        app_id = get_app_id_from_app_user(app_user)
        news_stream = NewsStream.create_key(app_id).get()
        type_city = False
        if news_stream and news_stream.stream_type == NewsStream.TYPE_CITY:
            type_city = True

        news_group = NewsGroup.create_key(group_id).get()
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
    ni = get_and_validate_news_item(news_id, service_identity_user)
    for members_50 in chunks(members, 50):
        deferred.defer(send_disable_news_request_to_users, news_id, members_50)

    publish_time = ni.stream_publish_timestamp
    sort_time = ni.stream_sort_timestamp

    to_put = []
    for member in members:
        app_user = create_app_user(users.User(member.member), member.app_id)
        nm = NewsItemMatch.create_key(app_user, news_id).get()
        if not nm:
            nm = NewsItemMatch.create(app_user, news_id, publish_time, sort_time, service_identity_user)
        nm.disabled = True
        to_put.append(nm)

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
        news_item.update_timestamp = now()
        news_item.put()
        delete_news_matches(news_id)
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
    service_user = get_service_user_from_service_identity_user(news_item.sender)
    service_profile = get_service_profile(service_user)
    service_identity = get_service_identity(news_item.sender)
    news_item_to = NewsItemTO.from_model(news_item, get_server_settings().baseUrl, service_profile, service_identity)
    news_created(None, logServiceError, service_profile, news_item=news_item_to,
                 service_identity=service_identity.identifier)


def do_callback_for_update(news_item):
    from rogerthat.service.api.news import news_updated
    service_user = get_service_user_from_service_identity_user(news_item.sender)
    service_profile = get_service_profile(service_user)
    service_identity = get_service_identity(news_item.sender)
    news_item_to = NewsItemTO.from_model(news_item, get_server_settings().baseUrl, service_profile, service_identity)
    news_updated(None, logServiceError, service_profile, news_item=news_item_to,
                 service_identity=service_identity.identifier)


def do_callback_for_delete(service_identity_user, news_id):
    from rogerthat.service.api.news import news_deleted
    service_user, service_identity = get_service_identity_tuple(service_identity_user)
    news_deleted(None, logServiceError, get_service_profile(service_user), news_id=news_id,
                 service_identity=service_identity)
