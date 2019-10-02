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
