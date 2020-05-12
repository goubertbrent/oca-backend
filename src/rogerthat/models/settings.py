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

from babel import Locale
from google.appengine.ext.ndb import TextProperty, GeoPtProperty, StringProperty, GeoPt, StructuredProperty, \
    LocalStructuredProperty, BooleanProperty, Key
from typing import List

from rogerthat.dal import parent_ndb_key
from rogerthat.models import NdbModel
from rogerthat.models.maps import MapServiceMediaItem
from rogerthat.rpc import users


class SyncedName(NdbModel):
    name = TextProperty()
    provider = TextProperty()

    @classmethod
    def from_to(cls, v):
        model = cls()
        model.name = v.name
        model.provider = v.provider
        return model


class SyncedNameValue(SyncedName):
    value = TextProperty()

    @classmethod
    def from_to(cls, v):
        model = super(SyncedNameValue, cls).from_to(v)
        model.value = v.value
        return model

    @classmethod
    def from_value(cls, value):
        model = cls()
        model.value = value
        return model


class ServiceAddress(SyncedName):
    coordinates = GeoPtProperty()  # type: GeoPt
    google_maps_place_id = StringProperty()
    country = TextProperty()  # BE
    locality = TextProperty()  # Nazareth
    postal_code = TextProperty()  # 9810
    street = TextProperty()  # Steenweg Deinze
    street_number = TextProperty()  # 154
    
    value = TextProperty() # todo remove 

    @classmethod
    def from_to(cls, address):
        model = super(ServiceAddress, cls).from_to(address)
        model.coordinates = GeoPt(address.coordinates.lat, address.coordinates.lon)
        model.google_maps_place_id = address.google_maps_place_id
        model.country = address.country
        model.locality = address.locality
        model.postal_code = address.postal_code
        model.street = address.street
        model.street_number = address.street_number
        return model

    def get_address_line(self, locale):
        country_name = Locale(locale).territories[self.country]
        return '%s %s, %s %s, %s' % (self.street, self.street_number, self.postal_code, self.locality, country_name)


class SyncedField(NdbModel):
    key = TextProperty(choices=['addresses', 'description', 'email_addresses', 'name', 'phone_numbers', 'websites'])
    provider = TextProperty()

    @classmethod
    def from_to(cls, v):
        return cls(key=v.key,
                   provider=v.provider)


# Stores service data "temporarily", when publishing other models are populated
class ServiceInfo(NdbModel):
    addresses = StructuredProperty(ServiceAddress, repeated=True)  # type: List[ServiceAddress]
    cover_media = LocalStructuredProperty(MapServiceMediaItem, repeated=True,
                                          indexed=False)  # type: List[MapServiceMediaItem]
    currency = TextProperty()
    description = TextProperty()
    email_addresses = StructuredProperty(SyncedNameValue, repeated=True, indexed=False)  # type: List[SyncedNameValue]
    keywords = TextProperty(repeated=True)  # type: List[str]
    name = TextProperty()
    phone_numbers = StructuredProperty(SyncedNameValue, repeated=True, indexed=False)  # type: List[SyncedNameValue]
    main_place_type = TextProperty()
    place_types = TextProperty(repeated=True)  # type: List[str]
    synced_fields = StructuredProperty(SyncedField, repeated=True, indexed=False)  # type: List[SyncedField]
    timezone = TextProperty()
    visible = BooleanProperty(default=True)
    websites = StructuredProperty(SyncedNameValue, repeated=True, indexed=False)  # type: List[SyncedNameValue]

    @property
    def service_user(self):
        return users.User(self.key.parent().id())

    @property
    def identity(self):
        return self.key.id()

    def main_address(self, locale):
        if not self.addresses:
            return None
        return self.addresses[0].get_address_line(locale)

    @property
    def main_email_address(self):
        return self.email_addresses[0].value if self.email_addresses else None

    @property
    def main_phone_number(self):
        return self.phone_numbers[0].value if self.phone_numbers else None

    @property
    def main_website(self):
        return self.websites[0].value if self.websites else None

    @classmethod
    def create_key(cls, service_user, service_identity):
        return Key(cls, service_identity, parent=parent_ndb_key(service_user))
