# -*- coding: utf-8 -*-
# Copyright 2018 Mobicage NV
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
# @@license_version:1.3@@

import json
from os import path

import dbf

# From https://download.vlaanderen.be/Producten/Detail?id=72&title=CRAB_stratenlijst
directory = path.dirname(__file__)


def get_street_data():
    table = dbf.Db3Table(filename=path.join(directory, 'query2.dbf')).open(mode=dbf.READ_ONLY)
    q = table.query('SELECT *')
    results = {}  # key: nis code
    for record in q:
        if record.nisgemcode not in results:
            results[record.nisgemcode] = {}
        postal_code = record.pkancode
        if postal_code not in results[record.nisgemcode]:
            results[record.nisgemcode][postal_code] = {
                'postal_code': postal_code,
                'name': record.gemnm.strip(),
                'streets': []
            }
        street_name = record.straatnm.strip()
        street_id = record.straatnmid
        results[record.nisgemcode][postal_code]['streets'].append({
            'name': street_name,
            'id': street_id,
        })
    return results


if __name__ == '__main__':
    data = get_street_data()
    with open(path.join(directory, 'be-street-mapping.json'), 'w') as f:
        json.dump(data, f)

# Importer
"""
from solutions.common.models.news import CityAppLocations, Locality, Street, LocationBounds

from google.appengine.api import urlfetch
from google.appengine.ext import ndb
from rogerthat.utils.location import geo_code
import json

id_mapping = {
    'be-veurne': 38025,
    'be-haaltert': 41024,
    'be-dendermonde': 42006,
    'be-neerpelt': 72043,
    'be-wetteren': 42025,
    'be-koksijde': 38014,
    'be-bocholt2': 72003,
    'be-kruisem': 45068,
    'be-wortegem-petegem': 45061,
    'be-zottegem': 41081,
    'be-bornem': 12007,
    'be-nieuwerkerken': 71045,
    'be-diepenbeek': 71011,
    'be-sint-lievens-houtem': 41063,
    'be-edegem': 11013,
    'be-lovendegem': 44085,
    'be-zulte': 44081,
    'be-lo-reninge': 32030,
    'be-diksmuide': 32003,
    'be-zele': 42028,
    'be-oudenaarde': 45035,
    'be-gistel': 35005,
    'be-zandhoven': 11054,
    'be-heers': 73022,
    'be-zonnebeke': 33037,
    'be-herne': 23032,
    'be-lede': 41034,
    'be-erpe-mere': 41082,
    'be-hooglede': 36006,
    'be-affligem': 23105,
    'be-anzegem': 34002,
    'be-lierde': 45063,
    'be-eeklo': 43005,
    'be-glabbeek': 24137,
    'be-geetbets': 24028,
    'be-meulebeke': 37007,
    'be-sint-truiden': 71053,
    'be-borgloon': 73009,
    'be-ninove': 41048,
    'be-nazareth': 44048,
    'be-maldegem': 43010,
    'be-langemark-poelkapelle': 33040,
    'be-dilbeek': 23016,
    'be-beringen': 71004,
    'be-wielsbeke': 37017,
    'be-halen': 71020,
    'be-hoeilaart': 23033,
    'be-scherpenheuvel-zichem': 24134,
    'be-herzele': 41027,
    'be-niel': 11030,
    'be-tienen': 24107,
    'be-lanaken': 73042,
    'be-aalter': 44084,
    'be-alken': 73001,
    'be-brakel': 45059,
    'be-vleteren': 33041,
    'be-destelbergen': 44013,
    'be-hemiksem': 11018,
    'be-wichelen': 42026,
    'be-berlare': 42003,
    'be-lokeren': 46014,
    'be-bree': 72004,
    'be-merchtem': 23052,
    'be-loc': 44034,
    'be-herentals': 13011,
    'be-aalst': 41002,
    'be-horebeke': 45062,
    'be-assenede': 43002,
    'be-geraardsbergen': 41018,
    'be-putte': 12029,
    'be-staden': 36019,
    'be-beveren': 46003,
    'be-herk-de-stad': 71024,
    'be-laarne': 42010,
    'be-halle': 23027,
    'be-moorslede': 36012,
    'be-hove': 11021,

    'osa-demo2': 44034,  # Lochristi
}


def _sort_street(item):
    # type: (Street) -> str
    return item.name


_geo_cache = {}


def _geo_code(search_str, extra_fields):
    if search_str in _geo_cache:
        return _geo_cache[search_str]
    result = geo_code(search_str, extra_fields)
    _geo_cache[search_str] = result
    return result


def _import_app(country_code, app_id, nis_code, data):
    model = CityAppLocations(
        key=CityAppLocations.create_key(app_id),
        official_id=nis_code,
        country_code=country_code,
    )
    data_in_city = data[str(nis_code)]
    for postal_code, locality in data_in_city.iteritems():
        geocoded = _geo_code(locality['name'], {'components': 'country:%s' % country_code})
        geometry = geocoded['geometry']
        if 'bounds' not in geometry:
            return 'No bounds found', locality['name'], geocoded
        model.localities.append(Locality(
            postal_code=str(locality['postal_code']),
            name=locality['name'],
            bounds=LocationBounds(
                northeast=ndb.GeoPt(geometry['bounds']['northeast']['lat'],
                                    geometry['bounds']['northeast']['lng']),
                southwest=ndb.GeoPt(geometry['bounds']['southwest']['lat'],
                                    geometry['bounds']['southwest']['lng'])),
            location=ndb.GeoPt(geometry['location']['lat'], geometry['location']['lng']),
            streets=sorted((Street(name=street['name'], id=street['id']) for street in locality['streets']),
                           key=_sort_street)))
    return model


def import_all():
    data = json.loads(urlfetch.fetch('https://storage.googleapis.com/oca-files/tmp/be-street-mapping.json').content)
    to_put = []
    country_code = 'BE'
    for app_id, nis_code in id_mapping.iteritems():
        to_put.append(_import_app(country_code, app_id, nis_code, data))
    ndb.put_multi(to_put)
"""
