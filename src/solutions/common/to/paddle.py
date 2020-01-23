# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley NV
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
from mcfw.properties import unicode_property, long_property, typed_property
from rogerthat.to import TO
from typing import List


class PaddleMappingTO(TO):
    paddle_id = unicode_property('paddle_id')
    title = unicode_property('title')
    service_email = unicode_property('service_email')


class PaddleSettingsTO(TO):
    base_url = unicode_property('base_url')
    mapping = typed_property('mapping', PaddleMappingTO, True, default=[])  # type: list[PaddleMappingTO]

    @classmethod
    def from_model(cls, settings):
        return cls(base_url=settings.base_url, mapping=[PaddleMappingTO.from_model(m) for m in settings.mapping])


class SimpleServiceTO(TO):
    name = unicode_property('name')
    service_email = unicode_property('service_email')


class PaddleSettingsServicesTO(TO):
    settings = typed_property('settings', PaddleSettingsTO)
    services = typed_property('services', SimpleServiceTO, True)


class PaddleOrganizationalUnit(TO):
    nid = unicode_property('nid')
    title = unicode_property('title')
    last_updated = unicode_property('last_updated')


class PaddleOrganizationalUnitsTO(TO):
    path = unicode_property('path')
    count = long_property('count')
    list = typed_property('list', PaddleOrganizationalUnit, True)  # type: list[PaddleOrganizationalUnit]


class PaddleAddress(TO):
    country = unicode_property('country')
    locality = unicode_property('locality')
    name_line = unicode_property('name_line')
    postal_code = unicode_property('postal_code')
    premise = unicode_property('premise')
    thoroughfare = unicode_property('thoroughfare')

    def is_valid(self):
        return (self.locality and self.postal_code and self.thoroughfare) not in ('', None)


class PaddleNode(TO):
    address = typed_property('address', PaddleAddress)  # type: PaddleAddress
    body = unicode_property('body')
    email = unicode_property('email')
    facebook = unicode_property('facebook')
    tax = unicode_property('tax')
    featured_image = unicode_property('featured_image')
    head_of_unit = unicode_property('head_of_unit')
    last_updated = unicode_property('last_updated')
    linked_in = unicode_property('linked_in')
    nid = unicode_property('nid')
    summary = unicode_property('summary')
    telephone = unicode_property('telephone')
    title = unicode_property('title')
    twitter = unicode_property('twitter')
    vat_number = unicode_property('PaddleRegularOpeningHoursvat_number')
    website = unicode_property('website')


class PaddlePeriod(TO):
    start = unicode_property('start')
    end = unicode_property('end')
    description = unicode_property('description')


class PaddleRegularOpeningHours(TO):
    friday = typed_property('friday', PaddlePeriod, True, default=[])  # type: List[PaddlePeriod]
    monday = typed_property('monday', PaddlePeriod, True, default=[])  # type: List[PaddlePeriod]
    saturday = typed_property('saturday', PaddlePeriod, True, default=[])  # type: List[PaddlePeriod]
    sunday = typed_property('sunday', PaddlePeriod, True, default=[])  # type: List[PaddlePeriod]
    thursday = typed_property('thursday', PaddlePeriod, True, default=[])  # type: List[PaddlePeriod]
    tuesday = typed_property('tuesday', PaddlePeriod, True, default=[])  # type: List[PaddlePeriod]
    wednesday = typed_property('wednesday', PaddlePeriod, True, default=[])  # type: List[PaddlePeriod]


class PaddleExceptionalOpeningHours(TO):
    description = unicode_property('description')
    start = unicode_property('start')
    opening_hours = typed_property('opening_hours', PaddleRegularOpeningHours)  # type: PaddleRegularOpeningHours
    end = unicode_property('end')


class PaddleOpeningHours(TO):
    closing_days = typed_property('closing_days', PaddlePeriod, True)  # type: List[PaddlePeriod]
    exceptional_opening_hours = typed_property('exceptional_opening_hours', PaddleExceptionalOpeningHours,
                                               True, default=[])  # type: List[PaddleExceptionalOpeningHours]
    regular = typed_property('regular', PaddleRegularOpeningHours)  # type: PaddleRegularOpeningHours


class PaddleOrganizationUnitDetails(TO):
    node = typed_property('node', PaddleNode)  # type: PaddleNode
    opening_hours = typed_property('opening_hours', PaddleOpeningHours)  # type: PaddleOpeningHours
    path = unicode_property('path')
