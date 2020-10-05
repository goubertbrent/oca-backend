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

from datetime import date, datetime
import logging

from google.appengine.ext import ndb, deferred, db

from rogerthat.bizz.job import run_job
from rogerthat.bizz.news.groups import update_stream_layout, get_groups_for_community
from rogerthat.capi.news import updateBadgeCount
from rogerthat.consts import NEWS_MATCHING_QUEUE
from rogerthat.dal.friend import get_friends_map_cached
from rogerthat.dal.mobile import get_mobile_key_by_account
from rogerthat.dal.profile import get_user_profile
from rogerthat.models import UserProfile, UserProfileInfo
from rogerthat.models.news import NewsItem, NewsSettingsUser, NewsSettingsUserService, NewsItemAddress, NewsGroup, \
    NewsNotificationStatus, NewsNotificationFilter, NewsStream, NewsItemActions, NewsMatchType, UserNewsGroupSettings
from rogerthat.rpc import users
from rogerthat.rpc.rpc import logError
from rogerthat.to.news import UpdateBadgeCountRequestTO
from rogerthat.utils import calculate_age_from_date, is_flag_set, get_epoch_from_datetime,\
    get_backend_service
from rogerthat.utils.location import haversine
from rogerthat.utils.service import remove_slash_default
from typing import Dict, List, Tuple, Optional


def setup_default_settings(app_user):
    # type: (users.User) -> NewsSettingsUser
    s_key = NewsSettingsUser.create_key(app_user)
    news_user_settings = NewsSettingsUser(key=s_key)
    news_user_settings.last_get_groups_request = datetime.utcnow()
    news_user_settings.put()
    return news_user_settings


def create_matches_for_news_item_key(news_item_key, old_group_ids, should_create_notification=False):
    news_item = news_item_key.get()
    create_matches_for_news_item(news_item, old_group_ids, should_create_notification)


def create_matches_for_news_item(news_item, old_group_ids, should_create_notification=False):
    # type: (NewsItem, List[unicode], bool) -> None
    from rogerthat.bizz.news import do_callback_for_create, do_callback_for_update

    if news_item.group_visible_until and NewsGroup.TYPE_POLLS in news_item.group_types:
        update_stream_layout(news_item.group_ids, NewsGroup.TYPE_POLLS, news_item.group_visible_until)

    deferred.defer(_update_service_filters, news_item.group_ids, news_item.sender, _queue=NEWS_MATCHING_QUEUE)
    stream_keys = [NewsStream.create_key(community_id) for community_id in news_item.community_ids]
    streams = {s.community_id: s for s in ndb.get_multi(stream_keys)}  # type: Dict[long, NewsStream]
    for community_id in news_item.community_ids:
        stream = streams[community_id]
        stream_group_ids = [group_id for group_id in news_item.group_ids if group_id in stream.group_ids]
        groups = ndb.get_multi([NewsGroup.create_key(group_id)
                                for group_id in stream_group_ids])  # type: List[NewsGroup]
        groups_info = {group.group_id: group.default_notifications_enabled for group in groups}
        run_job(_get_users_by_community, [community_id], _process_news_item_for_user,
                [news_item.id, should_create_notification, groups_info], worker_queue=NEWS_MATCHING_QUEUE, job_target=get_backend_service())

    if old_group_ids:
        do_callback_for_update(news_item)
    else:
        do_callback_for_create(news_item)


def _update_service_filters(group_ids, service_identity_user):
    for group_id in group_ids:
        deferred.defer(_update_service_filter, group_id, service_identity_user, _queue=NEWS_MATCHING_QUEUE)


@ndb.transactional(xg=True)
def _update_service_filter(group_id, service_identity_user):
    group = NewsGroup.create_key(group_id).get()
    if not group.service_filter or service_identity_user in group.services:
        return
    group.services.append(service_identity_user)
    group.put()


def _get_users_by_community(community_id):
    return UserProfile.list_by_community(community_id, keys_only=True)


def should_send_notification_for_group(user_group, send_notification_by_default, app_user, news_item_sender):
    # type: (UserNewsGroupSettings, bool, users.User, users.User) -> bool
    if not user_group or user_group.notifications == NewsNotificationFilter.NOT_SET:
        return send_notification_by_default
    if user_group.notifications in (NewsNotificationFilter.HIDDEN, NewsNotificationFilter.NONE):
        return False
    if user_group.notifications == NewsNotificationFilter.ALL:
        user_svc_settings = NewsSettingsUserService.create_key(app_user, user_group.group_id, news_item_sender).get()
        if user_svc_settings and user_svc_settings.notifications == NewsNotificationStatus.DISABLED:
            return False
        return True
    if user_group.notifications == NewsNotificationFilter.SPECIFIED:
        user_svc_settings = NewsSettingsUserService.create_key(app_user, user_group.group_id, news_item_sender).get()
        if user_svc_settings and user_svc_settings.notifications == NewsNotificationStatus.ENABLED:
            return True
        return False
    return send_notification_by_default


def _process_news_item_for_user(profile_key, news_id, should_create_notification, groups_info):
    # type: (db.Key, long, bool, Dict[unicode, bool]) -> None
    from rogerthat.bizz.news import create_notification
    app_user = users.User(profile_key.name())
    keys = [NewsSettingsUser.create_key(app_user), NewsItem.create_key(news_id)]
    user_settings, news_item = ndb.get_multi(keys)  # type: NewsSettingsUser, NewsItem
    if not user_settings:
        return

    t = _create_news_item_match(user_settings, news_item)
    if not t:
        return
    created_match, matches_location = t
    if not created_match:
        return

    group_ids = groups_info.keys()
    deferred.defer(calculate_and_update_badge_count, app_user, group_ids, _queue=NEWS_MATCHING_QUEUE)

    if not should_create_notification or is_flag_set(NewsItem.FLAG_SILENT, news_item.flags):
        return

    notification_group_id = None

    for group_id in group_ids:
        user_group = user_settings.get_group_by_id(group_id)
        send_notification_by_default = groups_info[group_id]
        if should_send_notification_for_group(user_group, send_notification_by_default, app_user, news_item.sender):
            notification_group_id = group_id
            break
    if notification_group_id:
        deferred.defer(create_notification, app_user, notification_group_id, news_item.id, matches_location,
                       _queue=NEWS_MATCHING_QUEUE)


def get_news_item_match_type(user_settings, news_item):
    if not news_item:
        logging.debug('debugging_news news item not found')
        return NewsMatchType.NO_MATCH

    if not news_item.published:
        logging.debug('debugging_news news item not published')
        return NewsMatchType.NO_MATCH

    if news_item.deleted:
        logging.debug('debugging_news news item deleted')
        return NewsMatchType.NO_MATCH

    if not user_settings:
        logging.debug('debugging_news user settings not found')
        return NewsMatchType.NO_MATCH

    if not _match_target_audience_of_item(user_settings.app_user, news_item):
        logging.debug('debugging_news no target_audience match')
        return NewsMatchType.NO_MATCH

    if news_item.has_locations:
        matches_location = _match_locations_of_item(user_settings.app_user, news_item)
        if news_item.location_match_required and not matches_location:
            logging.debug('debugging_news no location match')
            return NewsMatchType.NO_MATCH
    else:
        matches_location = False

    if matches_location:
        return NewsMatchType.LOCATION
    return NewsMatchType.NORMAL


def _create_news_item_match(user_settings, news_item):
    # type: (NewsSettingsUser, NewsItem) -> Optional[Tuple[bool, bool]]
    match_type = get_news_item_match_type(user_settings, news_item)
    if match_type == NewsMatchType.NO_MATCH:
        return
    created_match = False
    news_item_actions = NewsItemActions.create_key(user_settings.app_user, news_item.id).get()
    if not news_item_actions:
        created_match = True

    return created_match, match_type == NewsMatchType.LOCATION


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


def should_match_location(ni_lat, ni_lon, ni_distance, my_lat, my_lon, my_distance):
    distance_meter = long(haversine(my_lon, my_lat, ni_lon, ni_lat) * 1000)
    if distance_meter > sum([ni_distance, my_distance]):
        return False
    return True


def calculate_and_update_badge_count(app_user, group_ids):
    user_profile = get_user_profile(app_user)
    if not user_profile or not user_profile.mobiles:
        logging.debug('Not updating badge count: no user profile or mobiles for user %s', app_user)
        return
    keys = [NewsGroup.create_key(group_id) for group_id in group_ids] + [NewsSettingsUser.create_key(app_user)]
    models = ndb.get_multi(keys)
    news_settings_user = models.pop()
    if not news_settings_user:
        return
    news_groups = models  # type: List[NewsGroup]
    mobiles = db.get([get_mobile_key_by_account(mobile_detail.account) for mobile_detail in user_profile.mobiles])
    to_put = []
    for news_group in news_groups:
        details = news_settings_user.get_group_by_id(news_group.group_id)
        start_timestamp = get_epoch_from_datetime(details.last_load_request) if details else 0
        badge_count = NewsItem.count_unread(news_group.group_id, start_timestamp).get_result()
        to_put.extend(update_badge_count_user(app_user, news_group, badge_count, mobiles, save_capi_calls=False))
    db.put(to_put)


def update_badge_count_user(app_user, group_or_id, badge_count, mobiles=None, save_capi_calls=True):
    from rogerthat.bizz.news import update_badge_count_response_handler
    if not mobiles:
        user_profile = get_user_profile(app_user)
        if not user_profile or not user_profile.mobiles:
            logging.debug('Not updating badge count: no user profile or mobiles for user %s', app_user)
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
    # type: (users.User, users.User) -> None
    """Enables notifications for this service if one of the following conditions are true:
    - the user has set his notification filter to 'specified'
    - the user has not set his notification filter to anything (NewsNotificationFilter.NOT_SET), and the default
    notification filter is set to NewsNotificationFilter.SPECIFIED
    """
    news_settings = NewsSettingsUser.create_key(app_user).get()  # type: NewsSettingsUser
    if not news_settings:
        return
    user_profile = get_user_profile(app_user)
    groups_dict = get_groups_for_community(user_profile.community_id)
    to_put = []
    for groups in groups_dict.itervalues():
        for group in groups:
            group_id = group.group_id
            user_group = news_settings.get_group_by_id(group_id)
            should_enable_notifications = False
            if user_group:
                if user_group.notifications == NewsNotificationFilter.SPECIFIED:
                    # User has manually enabled notifications for specific services
                    should_enable_notifications = True
                elif user_group.notifications == NewsNotificationFilter.NOT_SET:
                    should_enable_notifications = group.default_notification_filter == NewsNotificationFilter.SPECIFIED
            elif group.default_notification_filter == NewsNotificationFilter.SPECIFIED:
                should_enable_notifications = True
            if should_enable_notifications:
                logging.debug('Enabling notifications for group %s(%s)', group.group_id, group.name)
                key = NewsSettingsUserService.create_key(app_user, group_id, service_identity_user)
                settings = key.get()  # type: NewsSettingsUserService
                if not settings or settings.notifications != NewsNotificationStatus.ENABLED:
                    settings = NewsSettingsUserService(key=key, group_id=group_id)
                    settings.notifications = NewsNotificationStatus.ENABLED
                    to_put.append(settings)
    ndb.put_multi(to_put)
