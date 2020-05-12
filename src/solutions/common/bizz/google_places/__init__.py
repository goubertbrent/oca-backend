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

import json
import logging
import urllib

from google.appengine.api import urlfetch

from mcfw.exceptions import HttpException
from rogerthat.settings import get_server_settings


def search_places(query, location):
    if not query and not location:
        return []
    
    google_maps_key = get_server_settings().googleMapsKey
    
    parameters = {
        'key': google_maps_key,
        'fields': 'geometry,name,place_id,formatted_address',
    }
    if location:
        parameters.update({'location': location, 'keyword': query, 'rankby': 'distance'})
        api = 'nearbysearch'
    else:
        parameters.update({'inputtype': 'textquery', 'input': query})
        api = 'findplacefromtext'
    url = 'https://maps.googleapis.com/maps/api/place/%s/json?%s' % (api, urllib.urlencode(parameters))
    result = urlfetch.fetch(url)  # type: urlfetch._URLFetchResult
    err = HttpException(result.content)
    if result.status_code == 200:
        content = json.loads(result.content)
        if content['status'] in ('OK', 'ZERO_RESULTS'):
            if api == 'nearbysearch':
                return content['results']
            else:
                return content['candidates']
        else:
            err.http_code = 400
    else:
        err.http_code = result.status_code
    logging.error('Error while searching for places: %s', result.content)
    raise err


def get_place_details(place_id, fields):
    google_maps_key = get_server_settings().googleMapsKey
    parameters = {
        'key': google_maps_key,
        'placeid': place_id,
        'fields': ','.join(fields),
    }
    url = 'https://maps.googleapis.com/maps/api/place/details/json?%s' % (urllib.urlencode(parameters))
    result = urlfetch.fetch(url)
    if result.status_code == 200:
        content = json.loads(result.content)
        if content['status'] == 'OK':
            return content['result']
    err = HttpException(result.content)
    err.http_code = result.status_code
    raise err
