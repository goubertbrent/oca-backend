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
from math import radians, cos, sin, asin, sqrt, degrees

import requests
from google.appengine.api import urlfetch

from mcfw.cache import cached
from mcfw.rpc import returns, arguments
from rogerthat.settings import get_server_settings

VERY_FAR = 100000  # Distance larger than any distance on earth


def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance in km between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    km = 6371 * c
#     km = 6378.1370 * c
    return km


def geo_offset(lat, lng, north, east):
    # Earth’s radius, sphere
    R = 6378137.0

    new_lat = lat + degrees(north / R)
    new_lng = lng + degrees(east / (R * cos(radians(lat))))

    return new_lat, new_lng


class GeoCodeException(Exception):
    pass


class GeoCodeZeroResultsException(GeoCodeException):
    pass


class GeoCodeStatusException(GeoCodeException):
    pass


@cached(1, lifetime=86400)
@returns(dict)
@arguments(address=unicode, extra_params=dict)
def geo_code(address, extra_params=None):
    logging.debug('Geo-coding:\n%s', address)
    url = 'https://maps.googleapis.com/maps/api/geocode/json?'
    address = address.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    param_dict = {
        'address': address.encode('utf8'),
        'sensor': 'false',
        'key': get_server_settings().googleMapsKey
    }
    if extra_params:
        param_dict.update(extra_params)
    response = urlfetch.fetch(url + urllib.urlencode(param_dict))
    result = json.loads(response.content)
    status = result['status']
    if status == 'ZERO_RESULTS':
        raise GeoCodeZeroResultsException()
    elif status != 'OK':
        raise GeoCodeStatusException(status)

    return result['results'][0]


@cached(1)
@returns(dict)
@arguments(lat=float, lon=float)
def get_timezone_from_latlon(lat, lon):
    """See https://developers.google.com/maps/documentation/timezone/overview
    Example:
{
   "dstOffset" : 0,
   "rawOffset" : -28800,
   "status" : "OK",
   "timeZoneId" : "America/Los_Angeles",
   "timeZoneName" : "Pacific Standard Time"
}"""
    # TODO: PY3: use offline library (e.g. https://pypi.org/project/timezonefinder)
    # 5.00$ / 1000 calls
    url = 'https://maps.googleapis.com/maps/api/timezone/json'
    params = {
        'location': u'%s,%s' % (lat, lon),
        'key': get_server_settings().googleMapsKey
    }
    result = requests.get(url, params=params)
    if result.status_code == 200:
        return json.loads(result.content)
    else:
        logging.error('%s: %s', result.status_code, result.content)
        raise Exception('Invalid response from Google Maps')


def address_to_coordinates(address, postal_code_required=True):
    """
    Converts an address to latitude and longitude coordinates.

    Args:
        address: The address of the location.

    Returns:
        tuple(long, long, unicode, unicode, unicode): latitude, longitude, Google place id, postal code, formatted address.

    """
    result = geo_code(address)
    lat = result['geometry']['location']['lat']
    lon = result['geometry']['location']['lng']
    address_components = result['address_components']
    postal_code = None
    for a in address_components:
        if 'postal_code' in a['types']:
            postal_code = a['short_name']
    if postal_code_required and not postal_code:
        raise GeoCodeException('Could not resolve address to coordinates')
    place_id = result['place_id']
    formatted_address = result['formatted_address']
    return lat, lon, place_id, postal_code, formatted_address


@cached(1, lifetime=86400)
@returns(dict)
@arguments(lat=float, lon=float)
def _coordinates_to_address(lat, lon):
    url = "https://maps.googleapis.com/maps/api/geocode/json?"
    params = urllib.urlencode(dict(latlng=u'%s,%s' % (lat, lon),
                                   key=get_server_settings().googleMapsKey))
    result = urlfetch.fetch(url + params)
    results = json.loads(result.content)
    if results['status'] == 'ZERO_RESULTS':
        raise GeoCodeZeroResultsException()
    elif results["status"] != "OK":
        raise GeoCodeStatusException(results['status'])
    return results


def coordinates_to_address(lat, lon):
    """
    Converts coordinates to a human readable address.

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        tuple(unicode, unicode, unicode): Address, Postal Code, Google place id
    """

    results = _coordinates_to_address(lat, lon)

    for r in results['results']:
        address = r.get('formatted_address')
        place_id = r.get('place_id')
        postal_code = None
        for res in r['address_components']:
            if 'postal_code' in res['types']:
                postal_code = res['short_name']
        if address and place_id and postal_code:
            return address, postal_code, place_id

    logging.debug(results)
    raise GeoCodeException('Could not resolve coordinates to address')


def coordinates_to_city(lat, lon):
    CITY_TYPES = ['administrative_area_level_1',
                  'administrative_area_level_2',
                  'administrative_area_level_3',
                  'administrative_area_level_4',
                  'administrative_area_level_5',
                  'locality',
                  'sublocality',
                  'sublocality_level_1',
                  'sublocality_level_2',
                  'sublocality_level_3',
                  'sublocality_level_4',
                  'sublocality_level_5',
                  'neighborhood']
    results = _coordinates_to_address(lat, lon)
    for result in results['results']:
        city = None
        city_lvl = -1
        for res in result['address_components']:
            if set(CITY_TYPES).intersection(res['types']):
                for i, v in enumerate(CITY_TYPES):
                    if v not in res['types']:
                        continue
                    if i <= city_lvl:
                        continue
                    city = res['long_name']
                    city_lvl = i
        if city:
            return city
    logging.debug(results)
    raise GeoCodeException('Could not resolve coordinates to address')
