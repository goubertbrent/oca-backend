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

from datetime import date, datetime
import logging

from google.appengine.ext import ndb, deferred, db
from google.appengine.ext.ndb.query import Cursor

from mcfw.rpc import returns, arguments
from rogerthat.bizz.job import run_job, MODE_BATCH
from rogerthat.bizz.news.groups import get_groups_for_app_id, \
    update_stream_layout
from rogerthat.bizz.roles import has_role
from rogerthat.capi.news import updateBadgeCount
from rogerthat.consts import NEWS_MATCHING_QUEUE
from rogerthat.dal import put_in_chunks
from rogerthat.dal.friend import get_friends_map_cached, get_friends_map
from rogerthat.dal.mobile import get_mobile_key_by_account
from rogerthat.dal.profile import get_user_profile
from rogerthat.dal.roles import get_service_roles_by_ids
from rogerthat.dal.service import get_service_identity
from rogerthat.models import UserProfile, UserProfileInfo, SearchConfig
from rogerthat.models.news import NewsItem, NewsSettingsUser, NewsItemMatch, \
    NewsSettingsUserGroup, NewsSettingsUserGroupDetails, NewsSettingsUserService, \
    NewsSettingsService, NewsItemAddress, NewsGroup, NewsNotificationStatus, NewsNotificationFilter, \
    NewsStream, NewsStreamCustomLayout
from rogerthat.models.properties.friend import FriendDetail
from rogerthat.rpc import users
from rogerthat.rpc.rpc import logError
from rogerthat.to.friends import FRIEND_TYPE_SERVICE
from rogerthat.to.news import UpdateBadgeCountRequestTO
from rogerthat.utils import calculate_age_from_date, is_flag_set
from rogerthat.utils.app import get_app_id_from_app_user
from rogerthat.utils.location import haversine
from rogerthat.utils.service import get_service_user_from_service_identity_user, \
    remove_slash_default, add_slash_default


def setup_default_settings(app_user, set_last_used=False):
    app_id = get_app_id_from_app_user(app_user)
    s_key = NewsSettingsUser.create_key(app_user)
    news_user_settings = s_key.get()  # type: NewsSettingsUser
    if not news_user_settings:
        logging.debug('debugging_news setup_default_settings creating user:%s', app_user)
        news_user_settings = NewsSettingsUser(key=s_key)
        news_user_settings.app_id = app_id
        news_user_settings.last_get_groups_request = None
        news_user_settings.group_ids = []
        news_user_settings.groups = []

    new_group_ids = []
    if not news_user_settings.groups:
        groups_dict = get_groups_for_app_id(app_id)
        logging.debug('debugging_news setup_default_settings user:%s groups_dict:%s', app_user, groups_dict)
        if groups_dict:
            d = datetime.utcnow()
            for group_type, groups in groups_dict.iteritems():
                ug = NewsSettingsUserGroup()
                ug.group_type = group_type
                ug.order = groups[0].default_order
                ug.details = []
                for g in groups:
                    ugd = NewsSettingsUserGroupDetails()
                    ugd.group_id = g.group_id
                    ugd.order = 20 if g.regional else 10
                    ugd.filters = g.filters
                    if g.default_notifications_enabled:
                        ugd.notifications = NewsNotificationFilter.ALL
                    else:
                        ugd.notifications = NewsNotificationFilter.SPECIFIED

                    ugd.last_load_request = d

                    ug.details.append(ugd)

                    news_user_settings.group_ids.append(g.group_id)
                    new_group_ids.append(g.group_id)

                news_user_settings.groups.append(ug)
            if set_last_used:
                news_user_settings.last_get_groups_request = d
            news_user_settings.put()
            deferred.defer(migrate_notification_settings_for_user, app_user, _queue=NEWS_MATCHING_QUEUE)

    for group_id in new_group_ids:
        deferred.defer(create_matches_for_user, app_user, group_id, _queue=NEWS_MATCHING_QUEUE)

    return news_user_settings


def create_matches_for_user(app_user, group_id, cursor=None):
    logging.debug('debugging_news create_matches_for_user user:%s group:%s', app_user, group_id)

    user_settings = NewsSettingsUser.create_key(app_user).get()

    batch_count = 50
    qry = NewsItem.list_published_by_group_id(group_id)
    start_cursor = Cursor.from_websafe_string(cursor) if cursor else None
    items, new_cursor, has_more = qry.fetch_page(batch_count, start_cursor=start_cursor)
    si_users = []
    for news_item in items:
        if news_item.sender in si_users:
            continue
        si_users.append(news_item.sender)

    to_put = []
    for news_item in items:
        t = _create_news_item_match(user_settings, news_item)
        if not t:
            continue
        m, _ = t
        to_put.append(m)
    if to_put:
        put_in_chunks(to_put, is_ndb=True)

    if has_more and new_cursor:
        new_cursor_str = new_cursor.to_websafe_string().decode('utf-8')
        deferred.defer(create_matches_for_user, app_user, group_id, new_cursor_str, _queue=NEWS_MATCHING_QUEUE)


def delete_matches_for_user(app_user, group_id):
    logging.debug('debugging_news delete_matches_for_user user:%s group:%s', app_user, group_id)

    batch_count = 200
    qry = NewsItemMatch.list_by_group_id(app_user, group_id)
    items, _, has_more = qry.fetch_page(batch_count)
    to_put = []
    for nim in items:
        if group_id not in nim.group_ids:
            continue
        nim.group_ids.remove(group_id)
        if not nim.group_ids:
            nim.visible = False
        to_put.append(nim)

    if to_put:
        put_in_chunks(to_put, is_ndb=True)

    if has_more:
        deferred.defer(delete_matches_for_user, app_user, group_id, _countdown=2, _queue=NEWS_MATCHING_QUEUE)


def create_matches_for_news_item_key(news_item_key, old_group_ids, should_create_notification=False):
    news_item = news_item_key.get()
    create_matches_for_news_item(news_item, old_group_ids, should_create_notification)


def create_matches_for_news_item(news_item, old_group_ids, should_create_notification=False):
    logging.debug('debugging_news create_matches_for_news_item %s', news_item.id)
    logging.debug('debugging_news old_group_ids: %s' % old_group_ids)
    logging.debug('debugging_news new_group_ids: %s' % news_item.group_ids)

    if news_item.group_visible_until and NewsGroup.TYPE_POLLS in news_item.group_types:
        update_stream_layout(news_item.group_ids, NewsGroup.TYPE_POLLS, news_item.group_visible_until)

    for group_id in old_group_ids:
        if group_id in news_item.group_ids:
            continue
        run_job(_qry_by_news_and_group_id, [news_item.id, group_id],
                _delete_group_matches_for_news_item_worker, [group_id], worker_queue=NEWS_MATCHING_QUEUE)

    for group_id in news_item.group_ids:
        if group_id in old_group_ids:
            continue
        deferred.defer(_update_service_filter, group_id, news_item.sender, _queue=NEWS_MATCHING_QUEUE)
        run_job(_create_matches_for_news_item_qry, [group_id],
                _create_matches_for_news_item_worker, [news_item.id, should_create_notification], worker_queue=NEWS_MATCHING_QUEUE)


@ndb.transactional(xg=True)
def _update_service_filter(group_id, service_identity_user):
    ng = NewsGroup.create_key(group_id).get()
    if not ng.service_filter:
        return
    if service_identity_user in ng.services:
        return
    ng.services.append(service_identity_user)
    ng.put()


def _create_matches_for_news_item_qry(group_id):
    return NewsSettingsUser.list_by_group_id(group_id)


@ndb.transactional(xg=True)
@returns()
@arguments(news_settings_key=ndb.Key, news_id=(int, long), should_create_notification=bool)
def _create_matches_for_news_item_worker(news_settings_key, news_id, should_create_notification=False):
    from rogerthat.bizz.news import create_notification
    user_settings = news_settings_key.get()
    if not user_settings:
        return
    logging.debug('debugging_news _create_matches_for_news_id_worker user:%s news_id:%s',
                  user_settings.app_user, news_id)

    news_item = get_news_item(news_id)
    t = _create_news_item_match(user_settings, news_item)
    if not t:
        return
    m, created_match = t
    m.put()
    if not m.visible:
        return

    if not created_match:
        return

    if m.group_ids:
        deferred.defer(calculate_and_update_badge_count, user_settings.app_user, m.group_ids, _transactional=True, _queue=NEWS_MATCHING_QUEUE)

    if not should_create_notification:
        return

    notification_group_id = None
    if not is_flag_set(NewsItem.FLAG_SILENT, news_item.flags):
        groups = []
        for group_id in m.group_ids:
            g = user_settings.get_group(group_id)
            if g and g not in groups:
                groups.append(g)

        group_types_ordered = news_item.group_types_ordered
        if not group_types_ordered:
            group_types_ordered = news_item.group_types

        sorted_groups = sorted(groups, key=lambda x: group_types_ordered.index(x.group_type))

        for g in sorted_groups:
            for d in g.details:
                if notification_group_id:
                    break
                if d.group_id not in m.group_ids:
                    continue
                if d.notifications == NewsNotificationFilter.HIDDEN:
                    continue
                if d.notifications == NewsNotificationFilter.NONE:
                    continue
                if d.notifications == NewsNotificationFilter.ALL:
                    nsus = NewsSettingsUserService.create_key(user_settings.app_user, d.group_id, news_item.sender).get()
                    if nsus and nsus.notifications == NewsNotificationStatus.DISABLED:
                        continue
                    notification_group_id = d.group_id
                    break
                if d.notifications == NewsNotificationFilter.SPECIFIED:
                    nsus = NewsSettingsUserService.create_key(user_settings.app_user, d.group_id, news_item.sender).get()
                    if nsus and nsus.notifications == NewsNotificationStatus.ENABLED:
                        notification_group_id = d.group_id
                        break

    if notification_group_id:
        deferred.defer(create_notification, user_settings.app_user, notification_group_id, news_item.id, location_match=m.location_match,
                       _transactional=True, _queue=NEWS_MATCHING_QUEUE)


def _create_news_item_match(user_settings, news_item):
    if not news_item:
        logging.debug('debugging_news news item not found')
        return

    if not news_item.published:
        logging.debug('debugging_news news item not published')
        return

    if not user_settings:
        logging.debug('debugging_news user settings not found')
        return

    if not user_settings.group_ids:
        logging.debug('debugging_news user groups empty')
        return

    group_ids = list(set(news_item.group_ids) & set(user_settings.group_ids))
    if not group_ids:
        logging.debug('debugging_news no groups matches')
        return

    if not _match_target_audience_of_item(user_settings.app_user, news_item):
        logging.debug('debugging_news no target_audience match')
        return

    if not _match_roles_of_item(user_settings.app_user, news_item):
        logging.debug('debugging_news no roles match')
        return

    if news_item.has_locations:
        matches_location = _match_locations_of_item(user_settings.app_user, news_item)
        if news_item.location_match_required and not matches_location:
            logging.debug('debugging_news no location match')
            return
    else:
        matches_location = False

    if not group_ids:
        logging.debug('debugging_news no groups matches after location matching')
        return

    filter_key = None
    nss = get_news_settings_service(get_service_user_from_service_identity_user(news_item.sender))
    if nss:
        for g in nss.groups:
            if g.group_type in news_item.group_types:
                if g.filter:
                    filter_key = g.filter
                    break

    created_match = False
    m = NewsItemMatch.create_key(user_settings.app_user, news_item.id).get()
    if m:
        group_id_matches = list(set(group_ids) & set(m.group_ids))
        if len(group_id_matches) != len(group_ids):
            m.group_ids = group_ids
        m.publish_time = news_item.stream_publish_timestamp
        m.sort_time = news_item.stream_sort_timestamp
        m.location_match = matches_location
    elif news_item.deleted:
        return
    else:
        created_match = True
        m = NewsItemMatch.create(user_settings.app_user, news_item.id, news_item.stream_publish_timestamp,
                                 news_item.stream_sort_timestamp, news_item.sender, group_ids, filter_key, matches_location)

    invisible_reasons = set()

    if news_item.deleted:
        invisible_reasons.add(NewsItemMatch.REASON_DELETED)

    if filter_key:
        for group_id in m.group_ids:
            if filter_key not in user_settings.get_group_details(group_id).filters:
                invisible_reasons.add(NewsItemMatch.REASON_FILTERED)
                break

    for group_id in m.group_ids:
        nsus = NewsSettingsUserService.create_key(user_settings.app_user, group_id, news_item.sender).get()
        if not nsus:
            continue
        if nsus.blocked:
            invisible_reasons.add(NewsItemMatch.REASON_BLOCKED)
            break
    
    service_visible = get_service_visible(news_item.sender)
    if not service_visible:
        invisible_reasons.add(NewsItemMatch.REASON_SERVICE_INVISIBLE)

    if invisible_reasons:
        m.invisible_reasons = list(invisible_reasons)
        m.visible = False
    else:
        m.visible = True

    return m, created_match


@ndb.non_transactional
def get_news_item(news_id):
    return NewsItem.get_by_id(news_id)


@ndb.non_transactional
def get_news_group(group_id):
    return NewsGroup.create_key(group_id).get()


@ndb.non_transactional
def get_service_visible(service_identity_user):
    sc = SearchConfig.get(SearchConfig.create_key(service_identity_user))
    return bool(sc and sc.enabled)


@ndb.non_transactional
def get_news_settings_service(service_user):
    return NewsSettingsService.create_key(service_user).get()


def _match_target_audience_of_item(app_user, news_item):
    target_audience = news_item.target_audience
    if not target_audience:
        return True
    profile = get_user_profile(app_user)
    if not profile:
        return False
    if profile.birthdate is None or not profile.gender >= 0:
        return False

    news_item_gender = target_audience.gender
    any_gender = (UserProfile.GENDER_MALE_OR_FEMALE, UserProfile.GENDER_CUSTOM)
    if news_item_gender not in any_gender:
        if profile.gender != news_item_gender:
            return False

    min_age = target_audience.min_age
    max_age = target_audience.max_age
    user_birthdate = date.fromtimestamp(profile.birthdate)
    user_age = calculate_age_from_date(user_birthdate)
    if not (min_age <= user_age <= max_age):
        return False

    if target_audience.connected_users_only:
        friends_map = get_friends_map_cached(app_user)
        if remove_slash_default(news_item.sender) not in friends_map.friends:
            return False
    return True


def _match_roles_of_item(app_user, news_item):
    if not news_item.has_roles():
        return True

    service_user = get_service_user_from_service_identity_user(news_item.sender)
    role_ids = news_item.role_ids
    roles = [role for role in get_service_roles_by_ids(service_user, role_ids) if role is not None]
    user_profile = get_user_profile(app_user)
    service_identity = get_service_identity(news_item.sender)
    return any([has_role(service_identity, user_profile, role) for role in roles])


def _match_locations_of_item(app_user, news_item):
    if not news_item.locations:
        return False
    user_profile_info = UserProfileInfo.create_key(app_user).get()  # type: UserProfileInfo
    if not user_profile_info or not user_profile_info.addresses:
        return False
    for user_address in user_profile_info.addresses:
        for geo_address in news_item.locations.geo_addresses:
            if should_match_location(geo_address.geo_location.lat,
                                     geo_address.geo_location.lon,
                                     geo_address.distance,
                                     user_address.geo_location.lat,
                                     user_address.geo_location.lon,
                                     user_address.distance):
                return True
        for address in news_item.locations.addresses:
            if address.level != NewsItemAddress.LEVEL_STREET:
                continue
            if address.address_uid == user_address.street_uid:
                return True
    return False


def block_matches(app_user, service_identity_user, group_id):
    run_job(_qry_service_matches, [app_user, service_identity_user, group_id],
            _worker_block_matches, [True, datetime.utcnow()], worker_queue=NEWS_MATCHING_QUEUE)


def reactivate_blocked_matches(app_user, service_identity_user, group_id):
    run_job(_qry_service_matches, [app_user, service_identity_user, group_id],
            _worker_block_matches, [False, datetime.utcnow()], worker_queue=NEWS_MATCHING_QUEUE)


def _qry_service_matches(app_user, service_identity_user, group_id):
    return NewsItemMatch.list_by_sender(app_user, service_identity_user, group_id)


@ndb.transactional()
def _worker_block_matches(nim_key, should_block, update_date):
    nim = nim_key.get()
    if nim.update_time_blocked and nim.update_time_blocked > update_date:
        return
    nim.update_time_blocked = update_date
    if should_block and NewsItemMatch.REASON_BLOCKED not in nim.invisible_reasons:
        nim.invisible_reasons.append(NewsItemMatch.REASON_BLOCKED)
        nim.visible = False
        nim.put()
    if not should_block and NewsItemMatch.REASON_BLOCKED in nim.invisible_reasons:
        nim.invisible_reasons.remove(NewsItemMatch.REASON_BLOCKED)
        nim.visible = True if len(nim.invisible_reasons) == 0 else False
        nim.put()


def enabled_filter(app_user, group_id, filter_):
    run_job(_qry_filter_matches, [app_user, group_id, filter_],
            _worker_filter_matches, [True], worker_queue=NEWS_MATCHING_QUEUE)


def disable_filter(app_user, group_id, filter_):
    run_job(_qry_filter_matches, [app_user, group_id, filter_],
            _worker_filter_matches, [False], worker_queue=NEWS_MATCHING_QUEUE)


def _qry_filter_matches(app_user, group_id, filter_):
    return NewsItemMatch.list_by_filter(app_user, group_id, filter_)


@ndb.transactional()
def _worker_filter_matches(nim_key, should_enable):
    nim = nim_key.get()
    if should_enable and NewsItemMatch.REASON_FILTERED in nim.invisible_reasons:
        nim.invisible_reasons.remove(NewsItemMatch.REASON_FILTERED)
        nim.visible = True if len(nim.invisible_reasons) == 0 else False
        nim.put()
    if not should_enable and NewsItemMatch.REASON_FILTERED not in nim.invisible_reasons:
        nim.invisible_reasons.append(NewsItemMatch.REASON_FILTERED)
        nim.visible = False
        nim.put()


def delete_news_matches(news_id):
    run_job(_qry_news_id_matches, [news_id],
            _worker_delete_matches, [], worker_queue=NEWS_MATCHING_QUEUE)


def _qry_news_id_matches(news_id):
    return NewsItemMatch.list_by_news_id(news_id)


@ndb.transactional()
def _worker_delete_matches(nim_key):
    nim = nim_key.get()
    if not nim:
        return
    if NewsItemMatch.REASON_DELETED not in nim.invisible_reasons:
        nim.invisible_reasons.append(NewsItemMatch.REASON_DELETED)
        nim.visible = False
        nim.put()


def update_visibility_news_matches(news_id, visible):
    run_job(_qry_news_id_matches, [news_id],
            _worker_update_visibility_matches, [visible], worker_queue=NEWS_MATCHING_QUEUE,
            mode=MODE_BATCH, batch_size=25)


@ndb.transactional(xg=True)
def _worker_update_visibility_matches(nim_keys, visible):
    to_put = []
    for nim in ndb.get_multi(nim_keys):
        if not nim:
            continue
        if visible:
            if NewsItemMatch.REASON_SERVICE_INVISIBLE in nim.invisible_reasons:
                nim.invisible_reasons.remove(NewsItemMatch.REASON_SERVICE_INVISIBLE)
                nim.visible = True if len(nim.invisible_reasons) == 0 else False
                to_put.append(nim)
        elif NewsItemMatch.REASON_SERVICE_INVISIBLE not in nim.invisible_reasons:
            nim.invisible_reasons.append(NewsItemMatch.REASON_SERVICE_INVISIBLE)
            nim.visible = False
            to_put.append(nim)
    ndb.put_multi(to_put)


def _qry_by_news_and_group_id(news_id, group_id):
    return NewsItemMatch.list_by_news_and_group_id(news_id, group_id)


@ndb.transactional()
@returns()
@arguments(nim_key=ndb.Key, group_id=unicode)
def _delete_group_matches_for_news_item_worker(nim_key, group_id):
    nim = nim_key.get()
    if group_id not in nim.group_ids:
        return
    logging.debug('debugging_news _delete_group_matches_for_news_item_worker user:%s news_id:%s group_id:%s',
                  nim.app_user, nim.news_id, group_id)

    nim.group_ids.remove(group_id)
    nim.put()


def should_match_location(ni_lat, ni_lon, ni_distance, my_lat, my_lon, my_distance):
    distance_meter = long(haversine(my_lon, my_lat, ni_lon, ni_lat) * 1000)
    if distance_meter > sum([ni_distance, my_distance]):
        return False
    return True


def calculate_and_update_badge_count(app_user, group_ids):
    news_settings_user = NewsSettingsUser.create_key(app_user).get()
    if not news_settings_user:
        return
    user_profile = get_user_profile(app_user)
    if not user_profile.mobiles:
        logging.info('debugging_news No mobiles for user %s, not calculating badge count', app_user)
        return
    mobiles = db.get([get_mobile_key_by_account(mobile_detail.account) for mobile_detail in user_profile.mobiles])
    to_put = []
    news_groups = ndb.get_multi(NewsGroup.create_key(group_id) for group_id in group_ids)

    news_stream = NewsStream.create_key(news_settings_user.app_id).get()
    news_stream_layout = None
    if news_stream:
        if news_stream.custom_layout_id:
            custom_layout = NewsStreamCustomLayout.create_key(news_stream.custom_layout_id, news_settings_user.app_id).get()
            if custom_layout and custom_layout.layout:
                news_stream_layout = custom_layout.layout
        if not news_stream_layout:
            news_stream_layout = news_stream.layout

    news_stream_group_types = []
    if news_stream_layout:
        for l in news_stream_layout:
            news_stream_group_types.extend(l.group_types)

    for news_group in news_groups:
        details = news_settings_user.get_group_details(news_group.group_id)
        if not details:
            continue
        if news_stream_group_types and news_group.group_type not in news_stream_group_types:
            badge_count = 0
        else:
            badge_count = NewsItemMatch.count_unread(app_user, news_group.group_id, details.last_load_request).get_result()
        to_put.extend(update_badge_count_user(app_user, news_group, badge_count, mobiles, save_capi_calls=False))
    db.put(to_put)


def update_badge_count_user(app_user, group_or_id, badge_count, mobiles=None, save_capi_calls=True):
    from rogerthat.bizz.news import update_badge_count_response_handler
    if not mobiles:
        user_profile = get_user_profile(app_user)
        if not user_profile:
            logging.debug('debugging_news update_badge_count_user failed no up %s', app_user)
            return []
        if not user_profile.mobiles:
            logging.debug('debugging_news update_badge_count_user failed no mobiles %s', app_user)
            return []
        mobiles = db.get([get_mobile_key_by_account(mobile_detail.account) for mobile_detail in user_profile.mobiles])
    if isinstance(group_or_id, NewsGroup):
        ng = group_or_id
    else:
        ng = NewsGroup.create_key(group_or_id).get()
    if not ng or ng.regional:
        return []

    request = UpdateBadgeCountRequestTO()
    request.group_id = ng.group_id
    request.group_type = ng.group_type
    request.badge_count = badge_count

    capi_calls = []
    for mobile in mobiles:
        capi_calls.extend(updateBadgeCount(update_badge_count_response_handler, logError, app_user, request=request,
                                           MOBILE_ACCOUNT=mobile, DO_NOT_SAVE_RPCCALL_OBJECTS=True))
    if save_capi_calls:
        db.put(capi_calls)
    return capi_calls


def setup_notification_settings_for_user(app_user, service_identity_user):
    s = NewsSettingsUser.create_key(app_user).get()
    if not s:
        return

    group_types = {}
    for g in s.get_groups_sorted():
        for d in g.get_details_sorted():
            if d.notifications == NewsNotificationFilter.SPECIFIED:
                if g.group_type not in group_types:
                    group_types[g.group_type] = []
                group_types[g.group_type].append(d.group_id)

    to_put = _setup_notification_settings_for_user(app_user, service_identity_user, group_types)
    logging.debug('setup_notification_settings_for_user len(to_put): %s', len(to_put))
    if to_put:
        ndb.put_multi(to_put)


def migrate_notification_settings_for_user(app_user):
    s = NewsSettingsUser.create_key(app_user).get()
    if not s:
        return

    group_types = {}
    for g in s.get_groups_sorted():
        for d in g.get_details_sorted():
            if d.notifications == NewsNotificationFilter.SPECIFIED:
                if g.group_type not in group_types:
                    group_types[g.group_type] = []
                group_types[g.group_type].append(d.group_id)

    logging.debug('migrate_notification_settings_for_user group_types: %s', group_types)

    to_put = []
    friendMap = get_friends_map(app_user)
    for fd in friendMap.friendDetails:
        if fd.type != FRIEND_TYPE_SERVICE:
            continue
        if fd.existence != FriendDetail.FRIEND_EXISTENCE_ACTIVE:
            continue
        service_identity_user = add_slash_default(users.User(fd.email))
        to_put.extend(_setup_notification_settings_for_user(app_user, service_identity_user, group_types))

    logging.debug('migrate_notification_settings_for_user len(to_put): %s', len(to_put))

    if to_put:
        ndb.put_multi(to_put)


def _setup_notification_settings_for_user(app_user, service_identity_user, group_types):
    logging.debug('_setup_notification_settings_for_user siu: %s', service_identity_user)
    logging.debug('_setup_notification_settings_for_user group_types: %s', group_types)
    service_user = get_service_user_from_service_identity_user(service_identity_user)
    nss = NewsSettingsService.create_key(service_user).get()
    if not nss:
        return []

    notifications_enabled_for_group_ids = []
    for group_type, group_ids in group_types.iteritems():
        g = nss.get_group(group_type)
        if not g:
            continue
        notifications_enabled_for_group_ids.extend(group_ids)

    logging.debug('_setup_notification_settings_for_user notifications_enabled_for_group_ids: %s', notifications_enabled_for_group_ids)
    if not notifications_enabled_for_group_ids:
        return []

    to_put = []
    for group_id in notifications_enabled_for_group_ids:
        nsus_key = NewsSettingsUserService.create_key(app_user, group_id, service_identity_user)
        nsus = nsus_key.get()
        if not nsus:
            nsus = NewsSettingsUserService(key=nsus_key,
                                           group_id=group_id,
                                           notifications=NewsNotificationStatus.NOT_SET,
                                           blocked=False)

        if nsus.notifications != NewsNotificationStatus.NOT_SET:
            continue

        nsus.notifications = NewsNotificationStatus.ENABLED
        to_put.append(nsus)

    return to_put
