# -*- coding: utf-8 -*-
# Copyright 2020 Green Valley NV
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
from datetime import datetime
from os.path import join, dirname

import cloudstorage
import xlwt
from google.appengine.ext.deferred import deferred
from typing import List, Dict
from xlwt import Worksheet

from rogerthat.bizz.gcs import get_serving_url
from rogerthat.bizz.maps.services.places.i18n_utils import _get_translations, DEFAULT_LANGUAGE
from rogerthat.consts import FILES_BUCKET, DAY, SCHEDULED_QUEUE, FA_ICONS


def export_place_types():
    file_name = 'place-types-translations-%s.xlsx' % datetime.now().isoformat()
    gcs_path = '/%s/tmp/%s' % (FILES_BUCKET, file_name)

    verticals = _get_json_file('verticals.json')
    classification = _get_json_file('classification.json')
    category_details = _get_json_file('categories.json')
    classicication_reverse = {}  # mapping of key: category id, value: vertical
    for vertical_key, categories in classification.iteritems():
        for category in categories:
            classicication_reverse[category] = vertical_key
    translations = _get_translations()
    languages = translations.keys()
    translation_keys = sorted(translations[DEFAULT_LANGUAGE].keys())
    with cloudstorage.open(gcs_path, 'w',
                           content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet') as gcs_file:
        book = xlwt.Workbook(encoding='utf-8')
        # Verticals
        rows = []
        for vertical, data in verticals.iteritems():
            data['name'] = vertical
            rows.append(data)
        _write_dict_sheet(book.add_sheet('verticals'), ['name', 'icon', 'color'], rows)
        _write_dict_sheet(book.add_sheet('icons'), ['name'], [{'name': icon} for icon in FA_ICONS])

        # Verticals - categories mapping
        rows = []
        for category_id in translation_keys:
            vertical = classicication_reverse.get(category_id)
            details = category_details.get(category_id, {})
            if not vertical:
                vertical = _guess_vertical(category_id)
            rows.append({'key': category_id, 'vertical': vertical, 'icon': details.get('icon')})
        _write_dict_sheet(book.add_sheet('classification'), ['key', 'vertical', 'icon'], rows)

        # Categories translations
        key_column = 'key'
        field_names = [key_column] + languages
        rows = []
        for translation_key in translation_keys:
            row = {
                key_column: translation_key,
            }
            for language in translations:
                translation = translations[language].get(translation_key, '').encode('utf-8')
                row[language] = translation
            rows.append(row)
        _write_dict_sheet(book.add_sheet('translations'), field_names, rows)
        book.save(gcs_file)

    deferred.defer(cloudstorage.delete, gcs_path, _countdown=DAY, _queue=SCHEDULED_QUEUE)
    return get_serving_url(gcs_path)


def _write_dict_sheet(sheet, columns, dictionary):
    # type: (Worksheet, List[str], List[dict]) -> None
    row_num = 0
    for column, label in enumerate(columns):
        sheet.write(row_num, column, label)
    row_num = 1
    for row in dictionary:
        for column, label in enumerate(columns):
            sheet.write(row_num, column, row.get(label))
        row_num += 1


def _get_json_file(filename):
    # type: (str) -> Dict[str, List[str]]
    return json.load(open(join(dirname(__file__), filename)))


def _guess_vertical(category_id):
    # type: (str) -> str
    if 'restaurant' in category_id or category_id.startswith('bar_') or category_id.endswith('_cafe'):
        return 'Food & Drink'
    if category_id.endswith('_dealer'):
        if category_id == 'arts_dealer':
            return 'Arts & Entertainment'
        elif category_id in ('coin_dealer', 'diamond_dealer', 'gold_dealer', 'iron_ware_dealer', 'junk_dealer',
                             'livestock_dealer', 'metalware_dealer', 'modular_home_dealer', 'scrap_metal_dealer'):
            return None
        else:
            return 'Autos & Vehicles'
