# -*- coding: utf-8 -*-
# Copyright 2021 Green Valley NV
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

from google.appengine.ext.ndb.model import GeoPt

from rogerthat.bizz.communities.models import CommunityMapSettings, MapLayers, MapLayerSettings
from rogerthat.bizz.communities.to import CommunityMapSettingsTO
from rogerthat.bizz.maps.gipod import GIPOD_TAG
from rogerthat.bizz.maps.poi.map import POI_TAG
from rogerthat.bizz.maps.reports import REPORTS_TAG
from rogerthat.bizz.maps.services import SERVICES_TAG


def get_community_map_settings(community_id):
    # type: (int) -> CommunityMapSettings
    key = CommunityMapSettings.create_key(community_id)
    return key.get() or CommunityMapSettings.get_default(community_id)


def update_community_map_settings(community_id, data):
    # type: (int, CommunityMapSettingsTO) -> CommunityMapSettings
    settings = get_community_map_settings(community_id)
    settings.center = GeoPt(data.center.lat, data.center.lon)
    settings.distance = min(data.distance, 2000)
    layers = MapLayers()
    # Save each non-empty layer to datastore.
    for layer_name in [GIPOD_TAG, POI_TAG, REPORTS_TAG, SERVICES_TAG]:
        layer = MapLayerSettings.from_to(getattr(data.layers, layer_name))
        if layer:
            setattr(layers, layer_name, layer)
    settings.layers = layers
    settings.put()
    return settings
