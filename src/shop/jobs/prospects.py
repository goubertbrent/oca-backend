# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
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

import json
import logging
import urllib
from collections import namedtuple

from google.appengine.api import urlfetch
from google.appengine.ext import deferred, db

from mcfw.properties import azzert
from mcfw.rpc import returns, arguments
from mcfw.utils import chunks
from rogerthat.bizz.job import run_job
from rogerthat.consts import HIGH_LOAD_WORKER_QUEUE
from rogerthat.dal.app import get_app_by_id
from rogerthat.settings import get_server_settings
from rogerthat.utils.location import geo_offset, haversine
from shop.bizz import broadcast_prospect_creation
from shop.business.prospect import re_index_prospect
from shop.constants import MAPS_CONTROLLER_QUEUE, MAPS_QUEUE
from shop.models import Prospect, ShopApp, ShopAppGridPoints

Point = namedtuple('Point', 'x y')
Size = namedtuple('Size', 'w h')


@returns()
@arguments(app_id=unicode, postal_codes=[unicode], sw_lat=float, sw_lon=float, ne_lat=float, ne_lon=float,
           city_name=unicode, check_phone_number=bool, radius=(int, long))
def find_prospects(app_id, postal_codes, sw_lat, sw_lon, ne_lat, ne_lon, city_name, check_phone_number, radius=200):
    logging.info('Finding prospects for %s', dict(app_id=app_id,
                                                  postal_codes=postal_codes,
                                                  south_west=(sw_lat, sw_lon),
                                                  north_east=(ne_lat, ne_lon),
                                                  check_phone_number=check_phone_number,
                                                  city_name=city_name))

    google_maps_key = get_server_settings().googleMapsKey
    shop_app_key = ShopApp.create_key(app_id)

    def trans():
        app = get_app_by_id(app_id)
        azzert(app)

        shop_app = db.get(shop_app_key)
        if not shop_app:
            shop_app = ShopApp(key=shop_app_key)

        shop_app.name = app.name
        shop_app.searched_south_west_bounds.append(db.GeoPt(sw_lat, sw_lon))
        shop_app.searched_north_east_bounds.append(db.GeoPt(ne_lat, ne_lon))
        shop_app.postal_codes = postal_codes
        shop_app.put()

        deferred.defer(_start_building_grid, google_maps_key, app_id, postal_codes, radius, sw_lat, sw_lon, ne_lat,
                       ne_lon, city_name, check_phone_number,
                       _transactional=True, _queue=HIGH_LOAD_WORKER_QUEUE)

    xg_on = db.create_transaction_options(xg=True)
    db.run_in_transaction_options(xg_on, trans)


@returns([Point])
@arguments(sw_lat=float, sw_lon=float, ne_lat=float, ne_lon=float, radius=(int, long))
def get_grid(sw_lat, sw_lon, ne_lat, ne_lon, radius=200):
    # grid_size = (distance(sw, se), distance(sw, nw)) - rounded up
    grid_size = Size(1000 * haversine(sw_lon, sw_lat, ne_lon, sw_lat),
                     1000 * haversine(sw_lon, sw_lat, sw_lon, ne_lat))
    logging.info('Grid size in meters: %s', grid_size)

    offset = radius * 2.0
    logging.info('Offset: %s', offset)

    grid = list()

    point_count_east_west = int((grid_size.w + radius) / offset) + 1
    point_count_north_south = int((grid_size.h + radius) / offset) + 1

    logging.info('Grid division: %s east-west, %s north-south', point_count_east_west, point_count_north_south)
    logging.info('Point count: %s', 2 * point_count_east_west * point_count_north_south)
    _fill_grid(ne_lat, ne_lon, offset, point_count_east_west, point_count_north_south, grid)

    lat, lon = geo_offset(ne_lat, ne_lon, -radius, -radius)
    _fill_grid(lat, lon, offset, point_count_east_west, point_count_north_south, grid)

    return grid


def _fill_grid(ne_lat, ne_lon, offset, point_count_east_west, point_count_north_south, grid):
    for ns in xrange(point_count_north_south):
        for ew in xrange(point_count_east_west):
            lat, lon = geo_offset(ne_lat, ne_lon, -offset * ns, -offset * ew)
            grid.append(Point(lat, lon))


def _start_building_grid(google_maps_key, app_id, postal_codes, radius, sw_lat, sw_lon, ne_lat, ne_lon, city_name,
                         check_phone_number):
    grid = get_grid(sw_lat, sw_lon, ne_lat, ne_lon, radius)

    todo_count = len(grid)
    logging.info('Total points count: %s', todo_count)
    for points in chunks(grid, 4000):
        todo_count -= len(points)
        is_last = (todo_count == 0)
        deferred.defer(_store_grid_points, google_maps_key, app_id, postal_codes, radius, points, is_last, city_name,
                       check_phone_number,
                       _queue=HIGH_LOAD_WORKER_QUEUE)


def _store_grid_points(google_maps_key, app_id, postal_codes, radius, points, is_last, city_name, check_phone_number):
    def trans():
        db.put(ShopAppGridPoints(parent=ShopApp.create_key(app_id),
                                 points=[db.GeoPt(*p) for p in points]))
        if is_last:
            deferred.defer(run_grid, google_maps_key, app_id, postal_codes, radius, city_name, check_phone_number,
                           _transactional=True, _queue=MAPS_CONTROLLER_QUEUE)

    db.run_in_transaction(trans)


def run_grid(google_maps_key, app_id, postal_codes, radius, city_name, check_phone_number):
    def trans():
        models = ShopAppGridPoints.all().ancestor(ShopApp.create_key(app_id)).fetch(1)
        for model in models:
            for _ in xrange(4):
                try:
                    geo_pt = model.points.pop()
                except IndexError:
                    break

                deferred.defer(find_places, google_maps_key, app_id, postal_codes, radius, (geo_pt.lat, geo_pt.lon),
                               city_name, check_phone_number,
                               _transactional=True, _queue=MAPS_QUEUE)

            if model.points:
                logging.debug('%s points remaining on this model', len(model.points))
                model.put()
            else:
                db.delete(model)

        if models:
            # grid is not empty
            deferred.defer(run_grid, google_maps_key, app_id, postal_codes, radius, city_name, check_phone_number,
                           _transactional=True, _queue=MAPS_CONTROLLER_QUEUE)

    db.run_in_transaction(trans)


def run_places(google_maps_key, app_id, postal_codes, places, city_name, check_phone_number):
    def trans():
        for _ in xrange(4):
            try:
                place = places.pop()
            except IndexError:
                return

            deferred.defer(get_place_details, google_maps_key, app_id, postal_codes, place, city_name,
                           check_phone_number,
                           _transactional=True, _queue=MAPS_QUEUE)

        if places:
            # places is not empty
            deferred.defer(run_places, google_maps_key, app_id, postal_codes, places, city_name, check_phone_number,
                           _transactional=True, _queue=MAPS_CONTROLLER_QUEUE)

    db.run_in_transaction(trans)


def find_places(google_maps_key, app_id, postal_codes, radius, coords, city_name, check_phone_number,
                next_page_token=""):
    """
    Finds places on Google maps and adds them as prospects

    Args:
        google_maps_key: Google maps API key
        app_id: The app id from the app where the prospect should be added to
        postal_codes: Comma separated string of postal codes.
        radius: Search radius
        coords: tuple of coordinates (latitude, longitude)
        city_name: Name of the city to search in. This ensures the prospects that are found are from this city.
        check_phone_number: Wether or not to skip prospects that have no phone number.
        next_page_token: Returns the next 20 results from a previously run search. Setting a pagetoken parameter will execute a search with the same parameters used previously — all parameters other than pagetoken will be ignored.
    """
    lat, lng = coords

    query = dict(key=google_maps_key)
    if next_page_token:
        query["pagetoken"] = next_page_token
    else:
        query["location"] = "%s,%s" % (lat, lng)
        query["radius"] = radius

    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?%s" % urllib.urlencode(query)

    result = urlfetch.fetch(url)
    if result.status_code != 200:
        raise Exception("Find places for coords %s failed with status_code: %s" % (coords, result.status_code))

    response = json.loads(result.content)
    if response['status'] != "OK":
        logging.info('result.content:\n%s', result.content)
        if response['status'] == 'ZERO_RESULTS':
            return
        raise Exception("Find places for coords %s failed with status: %s" % (coords, response['status']))

    place_ids = [result['place_id'] for result in response['results']]

    def trans():
        if place_ids:
            deferred.defer(run_places, google_maps_key, app_id, postal_codes, place_ids, city_name, check_phone_number,
                           _transactional=True, _queue=MAPS_CONTROLLER_QUEUE)

        next_page_token = response.get("next_page_token", None)
        if next_page_token:
            deferred.defer(find_places, google_maps_key, app_id, postal_codes, radius, coords, city_name,
                           check_phone_number, next_page_token,
                           _transactional=True, _queue=MAPS_QUEUE)

    db.run_in_transaction(trans)


def get_place_details(google_maps_key, app_id, postal_codes, place_id, city_name, check_phone_number):
    existing_prospect = db.run_in_transaction(Prospect.get_by_key_name, place_id)
    if existing_prospect:
        logging.debug('There already was a prospect for place %s', place_id)
        return

    query = dict(key=google_maps_key, placeid=place_id)
    url = "https://maps.googleapis.com/maps/api/place/details/json?%s" % urllib.urlencode(query)
    result = urlfetch.fetch(url)
    if result.status_code != 200:
        raise Exception("Get place details for place %s failed with status_code: %s" % (place_id, result.status_code))

    response = json.loads(result.content)
    if response['status'] != "OK":
        logging.info('result.content:\n%s', result.content)
        raise Exception("Get place details for place %s failed with status: %s" % (place_id, response['status']))

    result = response['result']
    address = result['formatted_address']
    if not address:
        logging.info('No address:\n%s', result)
        return
    for adc in result.get('address_components', []):
        if "postal_code" in adc["types"] and adc["short_name"] in postal_codes:
            break
        if city_name in address and "establishment" in result["types"]:
            break
    else:
        logging.info('Incorrect or missing postal code, and city name does not match:\n%s', result)
        return

    phone_number = result.get('international_phone_number', "")
    if not phone_number and check_phone_number:
        logging.info('No phone number:\n %s', result)
        return

    location = result['geometry']['location']

    def trans():
        prospect = Prospect.get_by_key_name(place_id)
        if prospect:
            logging.debug('There already was a prospect for place %s', place_id)
            return

        prospect = Prospect(key_name=place_id,
                            app_id=app_id,
                            name=result['name'],
                            type=result['types'],
                            categories=Prospect.convert_place_types(result['types']),
                            address=address,
                            geo_point=db.GeoPt(location['lat'], location['lng']),
                            phone=phone_number,
                            website=result.get('website'))
        prospect.put()
        deferred.defer(re_index_prospect, prospect, _transactional=True)
        deferred.defer(broadcast_prospect_creation, None, prospect, _transactional=True)

    db.run_in_transaction(trans)


def _get_all_prospects():
    return Prospect.all()


def re_index_all_prospects(queue=HIGH_LOAD_WORKER_QUEUE):
    run_job(_get_all_prospects, [], re_index_prospect, [], worker_queue=queue)
