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

from typing import List

from rogerthat.bizz.system import get_profile_addresses_to
from rogerthat.models import UserProfileInfo, ServiceMenuDef
from rogerthat.models.maps import MapConfig
from rogerthat.to import GeoPointTO
from rogerthat.to.maps import GetMapResponseTO, MapDefaultsTO, MapFilterTO


def get_map_response(map_config, user_profile_info, filters, add_addresses=True):
    # type: (MapConfig, UserProfileInfo, List[MapFilterTO], bool) -> GetMapResponseTO
    defaults = MapDefaultsTO(coords=GeoPointTO(lat=51.0974612, lon=3.8378242),  # todo change to OSA office
                             distance=3000,
                             max_distance=15 * 1000)

    buttons = []
    if map_config:
        defaults.coords.lat = map_config.center.lat
        defaults.coords.lon = map_config.center.lon
        defaults.distance = map_config.distance
        if map_config.filters:
            filters = [f for f in filters if f.key in map_config.filters]
        if map_config.default_filter:
            results = [f for f in filters if f.key == map_config.default_filter]
            if results:
                defaults.filter = results[0].key
        if map_config.buttons:
            buttons = map_config.buttons
            for button in buttons:
                if button.action.startswith('smi://'):
                    button.action = 'smi://' + ServiceMenuDef.hash_tag(button.action[6:])
                if button.color and not button.color.startswith('#'):
                    button.color = '#%s' % button.color

    if not defaults.filter:
        defaults.filter = filters[0].key if filters else None

    if defaults.distance > defaults.max_distance:
        defaults.distance = defaults.max_distance

    return GetMapResponseTO(
        defaults=defaults,
        filters=filters,
        addresses=get_profile_addresses_to(user_profile_info) if add_addresses else [],
        notifications=None,
        buttons=buttons,
        announcement=None
    )
