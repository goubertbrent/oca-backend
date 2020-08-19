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
import logging
from collections import defaultdict
from os.path import join, dirname
from sys import argv

from pandas import read_excel, ExcelFile, Series

logging.basicConfig(level=logging.DEBUG)


def import_place_types(path):
    # requires `pip install pandas` locally
    excel_file = ExcelFile(path)
    classification = read_excel(excel_file, sheet_name='classification')
    translations = read_excel(excel_file, sheet_name='translations')

    verticals = read_excel(excel_file, sheet_name='verticals')
    verticals_data = {}
    logging.info('importing verticals')
    for index, values in verticals.iterrows():  # type: [int, Series]
        name = values.pop('name')
        verticals_data[name] = values.to_dict()
    _write_file(verticals_data, 'verticals.json')

    classification_data = {vertical: [] for vertical in verticals_data}
    logging.info('importing classification & categories')
    categories_data = {}
    for index, values in classification.iterrows():  # type: [int, Series]
        key = values.get('key')
        vertical = values.get('vertical')
        if not isinstance(vertical, float):
            classification_data[vertical].append(key)
        icon = values.get('icon')
        if isinstance(icon, float):
            icon = None
        if icon:
            categories_data[key] = {'icon': icon}
    _write_file(categories_data, 'categories.json')
    _write_file(classification_data, 'classification.json')

    logging.info('importing translations')
    translations_data = defaultdict(dict)
    for index, values in translations.iterrows():
        key = values.pop('key')
        for language, translation in values.to_dict().items():
            translations_data[language][key] = translation
    for language in translations_data:
        _write_file(translations_data[language], join('i18n', language + '.json'))


def _write_file(data, filename):
    current_dir = dirname(__file__)
    complete_path = join(current_dir, '..', 'src', 'rogerthat', 'bizz', 'maps', 'services', 'places', filename)
    logging.info('Writing to file: ' + complete_path)
    json.dump(data, open(complete_path, 'w'), indent=2, sort_keys=True, separators=(',', ': '))


if __name__ == '__main__':
    if len(argv) == 2:
        filename = argv[1]
    else:
        filename = join(dirname(__file__), 'Plaats types.xlsx')
    import_place_types(filename)
