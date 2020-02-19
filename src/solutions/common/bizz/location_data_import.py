# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley NV
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

from google.appengine.api import urlfetch
from google.appengine.ext import ndb

from mcfw.cache import cached
from mcfw.rpc import arguments, returns
from rogerthat.utils.location import geo_code
from solutions.common.models.news import CityAppLocations, LocationBounds, Street, Locality


def _sort_street(item):
    # type: (Street) -> str
    return item.name


def import_location_data(app_id, country_code, official_id):
    # type: (unicode, unicode, unicode) -> CityAppLocations
    if country_code != 'BE':
        return
    # Run script in scripts/locations.py to update this file
    data = json.loads(urlfetch.fetch('https://storage.googleapis.com/oca-files/tmp/be-street-mapping.json').content)
    locations_data = _import_location_data(data, app_id, country_code, official_id)
    locations_data.put()
    return locations_data


@cached(1)
@returns(dict)
@arguments(search_str=unicode, extra_fields=dict)
def _geo_code(search_str, extra_fields):
    # type: (unicode, unicode) -> dict
    return geo_code(search_str, extra_fields)


def _import_location_data(data, app_id, country_code, official_id):
    # type: (dict, unicode, unicode, unicode) -> CityAppLocations

    model = CityAppLocations(
        key=CityAppLocations.create_key(app_id),
        official_id=official_id,
        country_code=country_code,
    )
    data_in_city = data[str(official_id)]
    for locality in data_in_city.itervalues():
        geocoded = _geo_code(locality['name'], {'components': 'country:%s' % country_code})
        geometry = geocoded['geometry']
        if 'bounds' not in geometry:
            logging.debug(geocoded)
            raise Exception('No bounds found for %s' % (locality['name'], geocoded))
        model.localities.append(Locality(
            postal_code=str(locality['postal_code']),
            name=locality['name'],
            bounds=LocationBounds(
                northeast=ndb.GeoPt(geometry['bounds']['northeast']['lat'],
                                    geometry['bounds']['northeast']['lng']),
                southwest=ndb.GeoPt(geometry['bounds']['southwest']['lat'],
                                    geometry['bounds']['southwest']['lng'])),
            location=ndb.GeoPt(geometry['location']['lat'], geometry['location']['lng']),
            # TODO: use data from ProfileStreets instead
            streets=sorted((Street(name=street['name'], id=street['id']) for street in locality['streets']),
                           key=_sort_street)))
    return model
