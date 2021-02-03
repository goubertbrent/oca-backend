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
from typing import List

from mcfw.properties import typed_property, unicode_property, unicode_list_property, long_property, bool_property
from rogerthat.bizz.maps.poi.models import PointOfInterest, POILocation
from rogerthat.to import TO, PaginatedResultTO
from rogerthat.to.maps import OpeningHoursTO, LatLonTO
from solutions.common.to.forms import MediaItemTO


class POILocationTO(TO):
    coordinates = typed_property('coordinates', LatLonTO)  # type: LatLonTO
    google_maps_place_id = unicode_property('google_maps_place_id', default=None)
    country = unicode_property('country', default=None)
    locality = unicode_property('locality', default=None)
    postal_code = unicode_property('postal_code', default=None)
    street = unicode_property('street', default=None)
    street_number = unicode_property('street_number', default=None)

    def to_model(self, timezone):
        return POILocation(
            coordinates=GeoPt(self.coordinates.lat, self.coordinates.lon),
            google_maps_place_id=self.google_maps_place_id,
            country=self.country,
            locality=self.locality,
            postal_code=self.postal_code,
            street=self.street,
            street_number=self.street_number,
            timezone=timezone,
        )


class PointOfInterestTO(TO):
    id = long_property('id')
    title = unicode_property('title')
    description = unicode_property('description', default=None)
    location = typed_property('location', POILocationTO)  # type: POILocationTO
    main_place_type = unicode_property('main_place_type')
    place_types = unicode_list_property('place_types')
    opening_hours = typed_property('opening_hours', OpeningHoursTO)
    media = typed_property('media', MediaItemTO, True)  # type: List[MediaItemTO]
    visible = bool_property('visible')
    status = long_property('status')

    @classmethod
    def from_model(cls, m):
        # type: (PointOfInterest) -> PointOfInterestTO
        return cls(
            id=m.id,
            title=m.title,
            description=m.description,
            location=POILocationTO.from_model(m.location),
            main_place_type=m.main_place_type,
            place_types=m.place_types,
            opening_hours=OpeningHoursTO.from_model(m.opening_hours),
            media=[MediaItemTO.from_media_item(media) for media in m.media],
            visible=m.visible,
            status=m.status,
        )


class PointOfInterestListTO(PaginatedResultTO):
    results = typed_property('results', PointOfInterestTO, True)  # type: List[PointOfInterestTO]
