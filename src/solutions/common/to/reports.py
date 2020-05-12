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

from mcfw.properties import unicode_list_property, unicode_property, typed_property, long_property
from rogerthat.to import TO
from rogerthat.to.maps import MapButtonTO
from solutions.common.to import LatLonTO


class MapConfigTO(TO):
    center = typed_property('center', LatLonTO, default=None)  # type: LatLonTO
    distance = long_property('distance', default=0)
    filters = unicode_list_property('filters', default=[])
    default_filter = unicode_property('default_filter', default=None)
    buttons = typed_property('buttons', MapButtonTO, True, default=[])

    @classmethod
    def from_model(cls, m):
        to = MapConfigTO()
        if m:
            to.center = LatLonTO(lat=m.center.lat, lon=m.center.lon)
            to.distance = m.distance
            to.filters = m.filters
            to.default_filter = m.default_filter
            to.buttons = m.buttons
        else:
            to.center = LatLonTO(lat=51.0974612, lon=3.8378242)
            to.distance = 7287
            to.max_distance = 15000
        return to
