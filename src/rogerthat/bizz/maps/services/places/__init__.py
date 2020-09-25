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
import os

from mcfw.properties import unicode_property
from rogerthat.bizz.maps.services.places.i18n_utils import get_dict_for_language, \
    translate
from rogerthat.to import TO

_classifications = None
_verticals = None
_categories = None


def _get_classifications():
    global _classifications
    if _classifications:
        return _classifications
    with open(os.path.join(os.path.dirname(__file__), 'classification.json')) as f:
        _classifications = json.load(f)
    return _classifications


def _get_verticals():
    global _verticals
    if _verticals:
        return _verticals
    with open(os.path.join(os.path.dirname(__file__), 'verticals.json')) as f:
        _verticals = json.load(f)
    return _verticals


def _get_vertical_for_place_type(place_type):
    all_classifications = _get_classifications()
    for vertical, place_types in all_classifications.iteritems():
        if place_type in place_types:
            return vertical
    return None


def _get_categories():
    global _categories
    if _categories:
        return _categories
    with open(os.path.join(os.path.dirname(__file__), 'categories.json')) as f:
        _categories = json.load(f)
    return _categories


def _get_vertical_details(vertical):
    all_verticals = _get_verticals()
    for current_vertical, details in all_verticals.iteritems():
        if current_vertical == vertical:
            return details
    return None


def get_vertical_details_for_place_type(place_type):
    vertical = _get_vertical_for_place_type(place_type)
    if not vertical:
        return None
    return _get_vertical_details(vertical)


class PlaceDetails(TO):
    title = unicode_property('title', default=None)
    fa_icon = unicode_property('fa_icon', default='fa-flag')
    icon_color = unicode_property('icon_color', default='#eb7bb8')
    png_icon = unicode_property('png_icon', default='fa-flag-eb7bb8')


def get_place_types(language):
    return get_dict_for_language(language)


def get_place_type_keys():
    return get_place_types('en').keys()


def get_place_details(place_type, language):
    title = translate(language, place_type)
    if not title:
        return None
    details = get_vertical_details_for_place_type(place_type)
    if not details:
        return None
    categories = _get_categories()
    icon = categories.get(place_type, {}).get('icon') or details['icon']
    return PlaceDetails(title=title,
                        fa_icon=icon,
                        icon_color=details['color'],
                        png_icon='{}-{}'.format(icon, details['color'].replace('#', '')))
