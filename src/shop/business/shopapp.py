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
import os

from google.appengine.ext import ndb

from shop.models import ShopApp

POSTAL_CODES = {}  # type: dict[str, list[dict]]
POSTAL_CODE_NAME_MAPPING = {}  # type: dict[str, list[str]]


def _get_postal_codes():
    global POSTAL_CODES
    if not POSTAL_CODES:
        with open(os.path.join(os.path.dirname(__file__), 'postal_codes_belgium.json')) as f:
            POSTAL_CODES = json.load(f)
    return POSTAL_CODES


def _get_post_code_name_mapping():
    global POSTAL_CODE_NAME_MAPPING
    if not POSTAL_CODE_NAME_MAPPING:
        codes = _get_postal_codes()
        for code in codes:
            # Municipalities can have same postcode as their 'parent' city/municipality
            for municipality in codes[code]:
                POSTAL_CODE_NAME_MAPPING[municipality['name'].lower()] = codes[code]
    return POSTAL_CODE_NAME_MAPPING


def set_postal_codes_for_shopapp(shop_app):
    # type: (ShopApp) -> ShopApp
    mapping = _get_post_code_name_mapping()
    lower_name = shop_app.name.lower()
    if lower_name in mapping:
        new_postal_codes = list({city['post_code'] for city in mapping[lower_name]})
        logging.info('Updating postal codes for %s from %s to %s', shop_app.app_id, shop_app.postal_codes,
                     new_postal_codes)
        shop_app.postal_codes = new_postal_codes
    return shop_app


def set_postal_codes_for_all_shopapps():
    ndb.put_multi([set_postal_codes_for_shopapp(shop_app) for shop_app in ShopApp.query()
                   if shop_app.app_id.startswith('be-')])
