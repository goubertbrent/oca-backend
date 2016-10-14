# -*- coding: utf-8 -*-
# COPYRIGHT (C) 2011-2014 MOBICAGE NV
# ALL RIGHTS RESERVED.
#
# ALTHOUGH YOU MAY BE ABLE TO READ THE CONTENT OF THIS FILE, THIS FILE
# CONTAINS CONFIDENTIAL INFORMATION OF MOBICAGE NV. YOU ARE NOT ALLOWED
# TO MODIFY, REPRODUCE, DISCLOSE, PUBLISH OR DISTRIBUTE ITS CONTENT,
# EMBED IT IN OTHER SOFTWARE, OR CREATE DERIVATIVE WORKS, UNLESS PRIOR
# WRITTEN PERMISSION IS OBTAINED FROM MOBICAGE NV.
#
# THE COPYRIGHT NOTICE ABOVE DOES NOT EVIDENCE ANY ACTUAL OR INTENDED
# PUBLICATION OF SUCH SOURCE CODE.
#
# @@license_version:1.7@@

import math
from multiprocessing.pool import ThreadPool
import sys, urllib, json, pprint, csv, time

GOOGLE_API_KEY = "AIzaSyAA_Ibn_RJtMTOkqbRDybn5SAF5lsV-zXA"

lat = float(sys.argv[1])
lng = float(sys.argv[2])
grid_size = float(sys.argv[3])
postcode_filter = sys.argv[4]
radius = 200

def geo_offset(lat, lng, lat_offset, lng_offset):
    # Earth’s radius, sphere
    R = 6378137.0

    latO = lat + (180 / math.pi) * (lat_offset / R)
    lngO = lng + (180 / math.pi) * (lng_offset / R) / math.cos(lat)

    return latO, lngO

def get_places(coords):
    lat, lng = coords
    places = list()
    next_page_token = ""
    while True:
        query = dict((("key", GOOGLE_API_KEY),))
        if next_page_token:
            query["pagetoken"] = next_page_token
        else:
            query["location"] = "%s,%s" % (lat, lng)
            query["radius"] = radius
        attempt = 0
        while True:
            attempt += 1
            url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?%s" % urllib.urlencode(query)
            response = json.load(urllib.urlopen(url))
            if not response['status'] == "OK":
                if attempt >= 5:
                    pprint.pprint(response)
                    raise Exception("Search query failed")
            else:
                break
        for result in response['results']:
            places.append(result['place_id'])
        next_page_token = response.get("next_page_token", None)
        if next_page_token is None:
            break
        time.sleep(2)
    return places

def get_place_details(place):
    query = dict((("key", GOOGLE_API_KEY), ("placeid", place)))
    url = "https://maps.googleapis.com/maps/api/place/details/json?%s" % urllib.urlencode(query)
    attempt = 0
    while True:
        attempt += 1
        response = json.load(urllib.urlopen(url))
        if not response['status'] == "OK":
            if attempt >= 5:
                pprint.pprint(response)
                raise Exception("Search query failed")
        else:
            break
    result = response['result']
    for adc in result.get('address_components', []):
        if "postal_code" in adc["types"] and adc["short_name"] in postcode_filter:
            break
    else:
        return
    address = result['formatted_address'].encode('utf8')
    if not address:
        return
    phone_number = result.get('international_phone_number', "")
    if not phone_number:
        return
    return [result['name'].encode('utf8'),
            address,
            phone_number,
            result.get('website', ""),
            '|'.join(result['types'])]

lat_start, lng_start = geo_offset(lat, lng, int(grid_size / 2), int(grid_size / 2))
grid = [(lat_start, lng_start), ]
point_count = int(grid_size / (radius * 2 / 3))
offset = int(grid_size / point_count)
for x in range(point_count):
    for y in range(point_count):
        grid.append(geo_offset(lat_start, lng_start, -(x + 1) * offset, -(y + 1) * offset))

pool = ThreadPool(50)
places = set()
for results in pool.map(get_places, grid):
    places.update(results)

# Get place details
writer = csv.writer(sys.stdout)
for place_details in (x for x in pool.map(get_place_details, places) if not x is None):
    writer.writerow(place_details)
