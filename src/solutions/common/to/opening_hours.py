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

from mcfw.properties import unicode_property, typed_property, long_property
from rogerthat.to import TO


class OpeningHourTO(TO):
    day = long_property('day')
    time = unicode_property('time')


class OpeningPeriodTO(TO):
    open = typed_property('open', OpeningHourTO)  # type: OpeningHourTO
    close = typed_property('close', OpeningHourTO)  # type: OpeningHourTO
    description = unicode_property('description', default=None)
    description_color = unicode_property('description_color', default=None)


class OpeningHourExceptionTO(TO):
    start_date = unicode_property('start_date')
    end_date = unicode_property('end_date')
    description = unicode_property('description')
    description_color = unicode_property('description_color', default=None)
    periods = typed_property('periods', OpeningPeriodTO, True, default=[])  # type: List[OpeningPeriodTO]


class OpeningHoursTO(TO):
    id = unicode_property('id')
    type = unicode_property('type')
    text = unicode_property('text')
    title = unicode_property('title')
    periods = typed_property('periods', OpeningPeriodTO, True, default=[])  # type: List[OpeningPeriodTO]
    exceptional_opening_hours = typed_property('exceptional_opening_hours', OpeningHourExceptionTO,
                                               True, default=[])  # type: List[OpeningHourExceptionTO]
