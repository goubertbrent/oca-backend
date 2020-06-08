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

from __future__ import unicode_literals

import json
import logging
import urllib

from google.appengine.api import urlfetch
from google.appengine.ext import ndb

from mcfw.exceptions import HttpException
from mcfw.rpc import returns, arguments, parse_complex_value
from mcfw.utils import Enum
from rogerthat.bizz.maps.shared import get_map_response
from rogerthat.consts import DEBUG
from rogerthat.dal.profile import get_user_profile
from rogerthat.models import UserProfileInfo
from rogerthat.models.maps import MapConfig, MapSettings
from rogerthat.rpc import users
from rogerthat.to.maps import GetMapResponseTO, GetMapItemsResponseTO, \
    GetMapItemsRequestTO, GetMapItemDetailsResponseTO, \
    GetMapItemDetailsRequestTO, MapFilterTO, \
    SaveMapItemVoteResponseTO, SaveMapItemVoteRequestTO, MapBaseUrlsTO, \
    MapAnnouncementTO, MapFunctionality
from rogerthat.translations import localize
from rogerthat.utils.app import get_app_id_from_app_user

REPORTS_TAG = 'reports'


class ReportsFilter(Enum):
    ALL = 'all'
    NEW = 'new'
    IN_PROGRESS = 'in_progress'
    RESOLVED = 'resolved'


@returns(GetMapResponseTO)
@arguments(app_user=users.User)
def get_map(app_user):
    language = get_user_profile(app_user).language
    filters = [
        MapFilterTO(key=ReportsFilter.ALL, label=localize(language, 'all')),
        MapFilterTO(key=ReportsFilter.NEW, label=localize(language, 'Reported')),
        MapFilterTO(key=ReportsFilter.IN_PROGRESS, label=localize(language, 'In Progress')),
        MapFilterTO(key=ReportsFilter.RESOLVED, label=localize(language, 'Resolved'))
    ]
    app_id = get_app_id_from_app_user(app_user)
    models = ndb.get_multi([MapConfig.create_key(app_id, REPORTS_TAG),
                            MapSettings.create_key(REPORTS_TAG),
                            UserProfileInfo.create_key(app_user)])
    map_config, map_settings, user_profile_info = models  # type: MapConfig, MapSettings, UserProfileInfo
    response = get_map_response(map_config, user_profile_info, filters)
    response.functionalities = [MapFunctionality.ADDRESSES]
    base_urls = MapBaseUrlsTO(icon_pin=None, icon_transparent=None)
    if map_settings and map_settings.data:
        base_url = map_settings.data.get('server_url')
        if base_url:
            base_urls.icon_pin = u'%s/static/plugins/reports/icons/pin' % base_url
            base_urls.icon_transparent = u'%s/static/plugins/reports/icons/transparent' % base_url
    response.base_urls = base_urls
    response.title = localize(language, 'reports_around_you')
    response.empty_text = localize(language, 'no_reports_at_location')
    response.announcement = _get_announcement(app_user)
    return response


@returns(GetMapItemsResponseTO)
@arguments(app_user=users.User, request=GetMapItemsRequestTO)
def get_map_items(app_user, request):
    center_lat = request.coords.lat
    center_lon = request.coords.lon
    distance = request.distance
    result = _get_items(app_user, center_lat, center_lon, distance, request.filter, cursor=request.cursor)
    return GetMapItemsResponseTO.from_dict(result)


@returns(GetMapItemDetailsResponseTO)
@arguments(app_user=users.User, request=GetMapItemDetailsRequestTO)
def get_map_item_details(app_user, request):
    return GetMapItemDetailsResponseTO.from_dict(_get_item_details(app_user, request.ids))


@returns(SaveMapItemVoteResponseTO)
@arguments(app_user=users.User, request=SaveMapItemVoteRequestTO)
def save_map_item_vote(app_user, request):
    return SaveMapItemVoteResponseTO.from_dict(_save_item_vote(app_user,
                                                               request.item_id,
                                                               request.vote_id,
                                                               request.option_id))


def _do_request(base_url, method=urlfetch.GET, params=None, language=None, authorization=None):
    settings = MapSettings.create_key(REPORTS_TAG).get()

    headers = {
        'Authorization': authorization or settings.data['server_key'],
        'Accept-Language': language or 'en',
    }
    url_params = ('?' + urllib.urlencode(params)) if params and method == urlfetch.GET else ''
    url = '%s/api/plugins/reports/v1.0%s%s' % (settings.data['server_url'], base_url, url_params)
    logging.debug('%s\n%s', url, params)

    payload = None if method == urlfetch.GET else json.dumps(params)
    result = urlfetch.fetch(url, payload, method, headers=headers, deadline=30,
                            follow_redirects=False)  # type: urlfetch._URLFetchResult
    if result.status_code != 200:
        logging.debug('Status: %s\nContent: %s', result.status_code, result.content)
        raise HttpException.from_urlfetchresult(result)
    elif DEBUG:
        logging.debug(result.content)

    return json.loads(result.content)


def _get_announcement(app_user):
    try:
        params = {
            'user_id': app_user.email()
        }
        language = get_user_profile(app_user).language
        result = _do_request('/map', urlfetch.GET, params, language)
        if result.get('announcement'):
            return parse_complex_value(MapAnnouncementTO(), result['announcement'], False)
    except:
        logging.debug('Failed to get announcement', exc_info=True)
    return None


def _get_items(app_user, lat, lon, distance, status, limit=100, cursor=None):
    params = {
        'user_id': app_user.email(),
        'lat': lat,
        'lon': lon,
        'distance': distance,
        'status': status,
        'limit': limit
    }
    if cursor:
        params['cursor'] = cursor
    language = get_user_profile(app_user).language
    return _do_request('/items', urlfetch.GET, params, language)


def _get_item_details(app_user, ids):
    params = {
        'user_id': app_user.email(),
        'ids': ','.join(ids)
    }
    language = get_user_profile(app_user).language
    return _do_request('/items/detail', urlfetch.GET, params, language)


def _save_item_vote(app_user, item_id, vote_id, option_id):
    params = {
        'user_id': app_user.email(),
        'vote_id': vote_id,
        'option_id': option_id
    }
    language = get_user_profile(app_user).language
    return _do_request('/items/%s/vote' % item_id, urlfetch.POST, params, language)
