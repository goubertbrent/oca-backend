# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
# NOTICE: THIS FILE HAS BEEN MODIFIED BY GREEN VALLEY BELGIUM NV IN ACCORDANCE WITH THE APACHE LICENSE VERSION 2.0
# Copyright 2018 GIG Technology NV
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
# @@license_version:1.6@@

from mcfw.properties import unicode_property
from rogerthat.bizz.maps.services.places.i18n_utils import get_dict_for_language, \
    translate
from rogerthat.to import TO


class PlaceDetails(TO):
    fa_icon = unicode_property('fa_icon', default=None)
    png_icon = unicode_property('png_icon', default='fa5-map-marker')
    title = unicode_property('title', default=None)


def get_place_types(language):
    return get_dict_for_language(language)


def get_place_type_keys():
    return get_dict_for_language('en').keys()


def get_place_details(place_type, language):
    title = translate(language, place_type)
    if not title:
        return None
    return PlaceDetails(title=title)


def get_icon_color(icon_id):
    icon_color_1 = '#f07b0e'  # orange
    icon_color_2 = '#c71906'  # red
    icon_color_3 = '#1e1af0'  # blue
    icon_color_4 = '#18990f'  # green
    icon_color_5 = '#ccc610'  # yellow
    if not icon_id:
        return icon_color_5
 
    if icon_id.startswith('fa1-') or icon_id.startswith('c1-'):
        return icon_color_1
    if icon_id.startswith('fa2-') or icon_id.startswith('c2-'):
        return icon_color_2
    if icon_id.startswith('fa3-') or icon_id.startswith('c3-'):
        return icon_color_3
    if icon_id.startswith('fa4-') or icon_id.startswith('c4-'):
        return icon_color_4
    if icon_id.startswith('fa5-') or icon_id.startswith('c5-'):
        return icon_color_5
    return icon_color_5