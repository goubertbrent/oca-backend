# -*- coding: utf-8 -*-
# Copyright 2018 Mobicage NV
# NOTICE: THIS FILE HAS BEEN MODIFIED BY MOBICAGE NV IN ACCORDANCE WITH THE APACHE LICENSE VERSION 2.0
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
# @@license_version:1.5@@

import base64
import json
import logging
from datetime import datetime

from google.appengine.api import urlfetch
from google.appengine.ext import ndb, db, deferred

from dateutil.relativedelta import relativedelta
from mcfw.rpc import returns, arguments
from mcfw.utils import Enum
from rogerthat.bizz.job import run_job
from rogerthat.bizz.maps.shared import get_map_response
from rogerthat.bizz.messaging import _ellipsize_for_json, _len_for_json
from rogerthat.capi.news import createNotification
from rogerthat.consts import HIGH_LOAD_WORKER_QUEUE
from rogerthat.dal.mobile import get_mobile_key_by_account
from rogerthat.dal.profile import get_user_profile
from rogerthat.models import UserProfileInfo
from rogerthat.models.maps import MapSettings, MapConfig, MapNotifications
from rogerthat.rpc import users
from rogerthat.rpc.rpc import DO_NOT_SAVE_RPCCALL_OBJECTS, \
    CAPI_KEYWORD_ARG_PRIORITY, PRIORITY_HIGH, \
    CAPI_KEYWORD_ARG_APPLE_PUSH_MESSAGE, CAPI_KEYWORD_PUSH_DATA, logError
from rogerthat.to.maps import GetMapResponseTO, MapFilterTO, MapNotificationsTO, GetMapItemsResponseTO, \
    GetMapItemsRequestTO, \
    GetMapItemDetailsResponseTO, GetMapItemDetailsRequestTO, \
    SaveMapNotificationsResponseTO, SaveMapNotificationsRequestTO, MapBaseUrlsTO, MapFunctionality
from rogerthat.to.news import CreateNotificationRequestTO
from rogerthat.to.push import OpenMapNotification
from rogerthat.translations import localize
from rogerthat.utils.app import get_app_id_from_app_user
from rogerthat.utils.iOS import construct_push_notification

GIPOD_TAG = u'gipod'


class GipodFilter(Enum):
    NEXT_7D = 'next_7d'
    NEXT_30D = 'next_30d'
    ALL = 'all'


def send_notifications():
    run_job(_send_notifications_query, [], _send_notifications_worker, [])


def _send_notifications_query():
    return MapNotifications.list_by_tag(GIPOD_TAG)


@returns()
@arguments(mn_key=ndb.Key)
def _send_notifications_worker(mn_key):
    app_user = users.User(mn_key.parent().id().decode('utf8'))
    send_notification(app_user)


def send_notification(app_user):
    from rogerthat.bizz.news import create_notification_response_handler

    app_id = get_app_id_from_app_user(app_user)
    if app_id in ('be-halle',):
        return

    upi = UserProfileInfo.create_key(app_user).get()
    if not upi:
        return
    if not upi.addresses:
        return
    user_profile = get_user_profile(app_user)
    if not user_profile:
        return
    if not user_profile.mobiles:
        return

    today = datetime.today().date() + relativedelta(days=1)
    start_date = str(today)
    end_date = str(today + relativedelta(days=7))

    ids = set()
    for a in upi.addresses:
        cursor = None
        while True:
            if len(ids) > 99:
                break
            r = _get_new_items(app_user,
                               a.geo_location.lat,
                               a.geo_location.lon,
                               a.distance,
                               start_date,
                               end_date,
                               cursor=cursor)
            for i in r['ids']:
                ids.add(i)

            if not r['cursor']:
                break
            cursor = r['cursor']

    if len(ids) == 0:
        return

    lang = user_profile.language
    title = localize(lang, u'New location updates')
    count = u'99+' if len(ids) > 99 else unicode(len(ids))
    message = localize(
        lang, u'%(name)s this week there are %(count)s new works, festivities or events planned around you',
        name=user_profile.name, count=count)

    mobiles = db.get([get_mobile_key_by_account(mobile_detail.account) for mobile_detail in user_profile.mobiles])
    tag = GIPOD_TAG
    map_filter = GipodFilter.NEXT_7D
    for mobile in mobiles:
        kwargs = {DO_NOT_SAVE_RPCCALL_OBJECTS: True, CAPI_KEYWORD_ARG_PRIORITY: PRIORITY_HIGH}
        if mobile.is_ios and mobile.iOSPushId:
            kwargs[CAPI_KEYWORD_ARG_APPLE_PUSH_MESSAGE] = _create_apple_push_message(title, message, tag, map_filter)
        elif mobile.is_android:
            kwargs[CAPI_KEYWORD_PUSH_DATA] = OpenMapNotification(title, message, tag, map_filter)
        createNotification(create_notification_response_handler, logError, app_user,
                           request=CreateNotificationRequestTO(), MOBILE_ACCOUNT=mobile, **kwargs)


def _create_apple_push_message(title, short_message, tag, map_filter):
    smaller_args = lambda args, too_big: [title, _ellipsize_for_json(args[1], _len_for_json(args[1]) - too_big)]
    notification = construct_push_notification('NM', [title, short_message], 'n.aiff', smaller_args, m=tag,
                                               filter=map_filter)
    return base64.encodestring(notification)


@returns(GetMapResponseTO)
@arguments(app_user=users.User)
def get_map(app_user):
    app_id = get_app_id_from_app_user(app_user)
    models = ndb.get_multi([MapConfig.create_key(app_id, GIPOD_TAG), MapNotifications.create_key(GIPOD_TAG, app_user),
                            MapSettings.create_key(GIPOD_TAG), UserProfileInfo.create_key(app_user)])
    map_config, map_notifications, map_settings, user_profile_info = models  # type: MapConfig, MapNotifications, MapSettings, UserProfileInfo
    language = get_user_profile(app_user).language
    filters = [
        MapFilterTO(key=GipodFilter.NEXT_7D, label=localize(language, 'next_x_days', days=7)),
        MapFilterTO(key=GipodFilter.NEXT_30D, label=localize(language, 'next_x_days', days=30)),
        MapFilterTO(key=GipodFilter.ALL, label=localize(language, 'all'))
    ]

    base_urls = MapBaseUrlsTO(icon_pin=None, icon_transparent=None)
    if map_settings and map_settings.data:
        base_url = map_settings.data.get('server_url')
        if base_url:
            base_urls.icon_pin = u'%s/static/plugins/gipod/icons/pin' % base_url
            base_urls.icon_transparent = u'%s/static/plugins/gipod/icons/transparent' % base_url
    response = get_map_response(map_config, user_profile_info, filters)
    response.functionalities = [MapFunctionality.ADDRESSES,
                                MapFunctionality.AUTO_LOAD_DETAILS]
    response.base_urls = base_urls
    response.empty_text = localize(language, 'no_hindrance_at_location')
    response.title = localize(language, 'hindrance_around_you')
    response.notifications = MapNotificationsTO(enabled=map_notifications.enabled if map_notifications else False)
    deferred.defer(_get_map, app_user, _queue=HIGH_LOAD_WORKER_QUEUE)
    return response


@returns(GetMapItemsResponseTO)
@arguments(app_user=users.User, request=GetMapItemsRequestTO)
def get_map_items(app_user, request):
    center_lat = request.coords.lat
    center_lon = request.coords.lon
    distance = request.distance

    today = datetime.today().date()
    start_date = str(today)
    if request.filter == GipodFilter.ALL:
        end_date = None
    elif request.filter == GipodFilter.NEXT_30D:
        end_date = str(today + relativedelta(days=30))
    else:
        end_date = str(today + relativedelta(days=7))

    return GetMapItemsResponseTO.from_dict(_get_items(app_user, center_lat, center_lon, distance, start_date, end_date,
                                                      cursor=request.cursor))


@returns(GetMapItemDetailsResponseTO)
@arguments(app_user=users.User, request=GetMapItemDetailsRequestTO)
def get_map_item_details(app_user, request):
    return GetMapItemDetailsResponseTO.from_dict(_get_item_details(app_user, request.ids))


@returns(SaveMapNotificationsResponseTO)
@arguments(app_user=users.User, request=SaveMapNotificationsRequestTO)
def save_map_notifications(app_user, request):
    # type: (users.User, SaveMapNotificationsRequestTO) -> SaveMapNotificationsResponseTO
    lang = get_user_profile(app_user).language
    notifications_key = MapNotifications.create_key(request.tag, app_user)
    if request.notifications.enabled:
        notifications = MapNotifications(key=notifications_key)
        notifications.tag = request.tag
        notifications.enabled = True
        notifications.put()
    else:
        # When changing behaviour also change _send_notifications_query
        notifications_key.delete()

    translation_key = 'gipod_notification_msg' if request.notifications.enabled else 'gipod_notification_disabled_msg'
    message = localize(lang, translation_key)
    return SaveMapNotificationsResponseTO(notifications=MapNotificationsTO(enabled=request.notifications.enabled),
                                          message=message)


def _do_request(base_url, params):
    settings = MapSettings.create_key(GIPOD_TAG).get()
    if not settings and settings.data:
        return []
    if not settings.data.get('server_url') or not settings.data.get('server_key'):
        return []

    headers = {
        'consumer_key': settings.data['server_key']
    }

    url = '%s%s' % (settings.data['server_url'], base_url)
    logging.debug('_do_request: %s params %s', url, params)

    result = urlfetch.fetch(url, json.dumps(params), method=urlfetch.POST, headers=headers, deadline=30,
                            follow_redirects=False)
    if result.status_code != 200:
        raise Exception('Failed to get gipod data')

    return json.loads(result.content)


def _make_lat_lon_params(app_user, lat, lon, distance, start, end, limit=100, cursor=None):
    params = {
        'user_id': app_user.email(),
        'lat': lat,
        'lon': lon,
        'distance': distance,
        'start': start,
        'limit': limit
    }
    if end:
        params['end'] = end
    if cursor:
        params['cursor'] = cursor

    return params


def _get_new_items(app_user, lat, lon, distance, start, end, limit=100, cursor=None):
    params = _make_lat_lon_params(app_user, lat, lon, distance, start, end, limit, cursor)
    return _do_request('/plugins/gipod/items/new', params)


def _get_map(app_user):
    try:
        params = {
            'user_id': app_user.email()
        }
        _do_request('/plugins/gipod/map', params)
    except:
        logging.debug('Failed to get map', exc_info=True)


def _get_items(app_user, lat, lon, distance, start, end, limit=100, cursor=None):
    params = _make_lat_lon_params(app_user, lat, lon, distance, start, end, limit, cursor)
    return _do_request('/plugins/gipod/items', params)


def _get_item_details(app_user, ids):
    params = {
        'user_id': app_user.email(),
        'ids': ids
    }
    return _do_request('/plugins/gipod/items/detail', params)
