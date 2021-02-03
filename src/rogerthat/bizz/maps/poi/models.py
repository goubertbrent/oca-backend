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

from babel import Locale
from google.appengine.ext import ndb
from google.appengine.ext.ndb.model import GeoPtProperty, GeoPt, StringProperty, TextProperty, IntegerProperty, \
    StructuredProperty, BooleanProperty
from typing import List

from mcfw.utils import Enum
from rogerthat.models import NdbModel, OpeningHours
from rogerthat.models.settings import MediaItem


class POILocation(NdbModel):
    coordinates = GeoPtProperty(required=True)  # type: GeoPt
    google_maps_place_id = StringProperty()
    country = TextProperty()  # BE
    locality = TextProperty()  # Nazareth
    postal_code = TextProperty()  # 9810
    street = TextProperty()  # Steenweg Deinze
    street_number = TextProperty()  # 154
    timezone = TextProperty(required=True)


class POIStatus(Enum):
    # Not visible because incomplete (e.g. missing place type or location)
    INCOMPLETE = 0
    # Visible on map
    VISIBLE = 1
    # Not visible on map
    INVISIBLE = 2


class PointOfInterest(NdbModel):
    community_id = IntegerProperty(required=True)
    title = TextProperty(required=True)
    description = TextProperty()
    location = StructuredProperty(POILocation, required=True, indexed=False)  # type: POILocation
    main_place_type = TextProperty()
    place_types = TextProperty(repeated=True)
    opening_hours = StructuredProperty(OpeningHours, required=True, indexed=False)
    media = StructuredProperty(MediaItem, repeated=True, indexed=False)  # type: List[MediaItem]
    visible = BooleanProperty()
    status = IntegerProperty(choices=POIStatus.all())  # status is only set by server (not by client/dashboard)

    @property
    def id(self):
        return self.key.integer_id()

    @property
    def has_complete_info(self):
        return all((self.title, self.location, self.location.coordinates, self.main_place_type, self.place_types))

    def get_address_line(self, locale):
        country_name = Locale(locale).territories[self.location.country]
        parts = []
        if self.location.street:
            parts.append(self.location.street)
        if self.location.street_number:
            parts.append(self.location.street_number)
        if parts:
            parts[-1] += ','
        parts.append(self.location.postal_code)
        parts.append(self.location.locality + ',')
        parts.append(country_name)
        return ' '.join(parts)

    @classmethod
    def create_key(cls, poi_id):
        # type: (int) -> ndb.Key
        assert isinstance(poi_id, (int, long))
        return ndb.Key(cls, poi_id)

    @classmethod
    def list_by_community(cls, community_id):
        return cls.query().filter(cls.community_id == community_id)
