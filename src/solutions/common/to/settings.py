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

from typing import List

from mcfw.properties import typed_property, unicode_property, bool_property, unicode_list_property
from rogerthat.models.settings import ServiceInfo
from rogerthat.to import TO
from rogerthat.to.news import BaseMediaTO
from solutions.common.to import LatLonTO


class SyncedNameValueTO(TO):
    name = unicode_property('name', default=None)
    value = unicode_property('value')
    provider = unicode_property('provider', default=None)


class ServiceAddressTO(SyncedNameValueTO):
    coordinates = typed_property('coordinates', LatLonTO)
    google_maps_place_id = unicode_property('google_maps_place_id')


class MapServiceMediaItemTO(TO):
    role_ids = unicode_list_property('role_ids')
    item = typed_property('item', BaseMediaTO)  # type: BaseMediaTO


class SyncedFieldTO(TO):
    key = unicode_property('key')
    provider = unicode_property('provider')


class ServiceInfoTO(TO):
    addresses = typed_property('addresses', ServiceAddressTO, True)  # type: List[ServiceAddressTO]
    cover_media = typed_property('cover_media', MapServiceMediaItemTO, True)  # type: List[MapServiceMediaItemTO]
    currency = unicode_property('currency')
    description = unicode_property('description')
    email_addresses = typed_property('email_addresses', SyncedNameValueTO, True)  # type: List[SyncedNameValueTO]
    keywords = unicode_list_property('keywords')  # type: List[str]
    name = unicode_property('name')
    phone_numbers = typed_property('phone_numbers', SyncedNameValueTO, True)  # type: List[SyncedNameValueTO]
    main_place_type = unicode_property('main_place_type')  # type: str
    place_types = unicode_list_property('place_types', default=[])  # type: List[str]
    synced_fields = typed_property('synced_fields', SyncedFieldTO, True)  # type: List[SyncedFieldTO]
    timezone = unicode_property('timezone')
    visible = bool_property('visible')
    websites = typed_property('websites', SyncedNameValueTO, True)  # type: List[SyncedNameValueTO]

    @classmethod
    def from_model(cls, m):
        # type: (ServiceInfo) -> ServiceInfoTO
        # to = super(ServiceInfoTO, cls).from_model(m)
        to = cls()
        to.addresses = [ServiceAddressTO.from_model(address) for address in m.addresses]
        to.cover_media = [MapServiceMediaItemTO.from_model(media_item) for media_item in m.cover_media]
        to.currency = m.currency
        to.description = m.description
        to.email_addresses = [SyncedNameValueTO.from_model(value) for value in m.email_addresses]
        to.keywords = m.keywords
        to.name = m.name
        to.phone_numbers = [SyncedNameValueTO.from_model(value) for value in m.phone_numbers]
        to.main_place_type = m.main_place_type
        to.place_types = m.place_types
        to.synced_fields = [SyncedFieldTO.from_model(field) for field in m.synced_fields]
        to.timezone = m.timezone
        to.visible = m.visible
        to.websites = [SyncedNameValueTO.from_model(value) for value in m.websites]
        return to
