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
from typing import List

from mcfw.properties import unicode_property, long_property, bool_property, typed_property, unicode_list_property, \
    long_list_property
from rogerthat.bizz.communities.models import MapLayerSettings
from rogerthat.to import TO
from rogerthat.to.jobs import LatLonTO
from rogerthat.to.maps import MapButtonTO


class AutoConnectedServiceTO(TO):
    service_email = unicode_property('service_email')
    removable = bool_property('removable')


class BaseCommunityTO(TO):
    auto_connected_services = typed_property('auto_connected_services', AutoConnectedServiceTO,
                                             True)  # type: List[AutoConnectedServiceTO]
    country = unicode_property('country')
    create_date = unicode_property('create_date')
    default_app = unicode_property('default_app')
    demo = bool_property('demo')
    embedded_apps = unicode_list_property('embedded_apps')
    features = unicode_list_property('features')
    customization_features = long_list_property('customization_features')
    name = unicode_property('name')
    main_service = unicode_property('main_service')
    signup_enabled = bool_property('signup_enabled')


class CommunityTO(BaseCommunityTO):
    id = long_property('id')


class CommunityLocationTO(TO):
    locality = unicode_property('locality')
    postal_code = unicode_property('postal_code')


class GeoFenceGeometryTO(TO):
    center = typed_property('center', LatLonTO)
    max_distance = long_property('max_distance')


class CommunityGeoFenceTO(TO):
    country = unicode_property('country')
    defaults = typed_property('defaults', CommunityLocationTO, default=None)
    geometry = typed_property('geometry', GeoFenceGeometryTO, default=None)

    @classmethod
    def from_model(cls, m):
        return cls(
            country=m.country,
            defaults=CommunityLocationTO.from_model(m.defaults) if m.defaults else None,
            geometry=GeoFenceGeometryTO.from_model(m.geometry) if m.geometry else None,
        )


class MapLayerSettingsTO(TO):
    filters = unicode_list_property('filters', default=[])
    default_filter = unicode_property('default_filter', default=None)
    buttons = typed_property('buttons', MapButtonTO, True, default=[])  # type: List[MapButtonTO]

    @classmethod
    def from_model(cls, m):
        return super(MapLayerSettingsTO, cls).from_model(m or MapLayerSettings())


class MapLayersTO(TO):
    gipod = typed_property('gipod', MapLayerSettingsTO)  # type: MapLayerSettingsTO
    poi = typed_property('poi', MapLayerSettingsTO)  # type: MapLayerSettingsTO
    reports = typed_property('reports', MapLayerSettingsTO)  # type: MapLayerSettingsTO
    services = typed_property('services', MapLayerSettingsTO)  # type: MapLayerSettingsTO

    @classmethod
    def from_model(cls, m):
        to = cls()
        to.gipod = MapLayerSettingsTO.from_model(m.gipod)
        to.poi = MapLayerSettingsTO.from_model(m.poi)
        to.reports = MapLayerSettingsTO.from_model(m.reports)
        to.services = MapLayerSettingsTO.from_model(m.services)
        return to


class CommunityMapSettingsTO(TO):
    center = typed_property('center', LatLonTO)
    distance = long_property('distance')
    layers = typed_property('layers', MapLayersTO)

    @classmethod
    def from_model(cls, m):
        to = cls()
        to.center = LatLonTO.from_model(m.center) if m.center else None
        to.distance = m.distance
        to.layers = MapLayersTO.from_model(m.layers)
        return to
