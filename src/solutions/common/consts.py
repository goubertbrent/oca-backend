# -*- coding: utf-8 -*-
# Copyright 2017 Mobicage NV
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
# @@license_version:1.2@@

OUR_CITY_APP_COLOUR = u'5BC4BF'

UNIT_PIECE = 1
UNIT_LITER = 2
UNIT_KG = 3
UNIT_GRAM = 4
UNIT_HOUR = 5
UNIT_MINUTE = 6
UNIT_DAY = 7
UNIT_PERSON = 8
UNIT_SESSION = 9
UNIT_PLATTER = 10
UNIT_WEEK = 11
UNIT_MONTH = 12
# values are the translation keys
UNITS = {
    UNIT_PIECE: 'piece',
    UNIT_LITER: 'liter',
    UNIT_KG: 'kilogram',
    UNIT_GRAM: 'gram',
    UNIT_HOUR: 'hour',
    UNIT_MINUTE: 'minute',
    UNIT_DAY: 'day',
    UNIT_WEEK: 'week',
    UNIT_MONTH: 'month',
    UNIT_PERSON: 'person',
    UNIT_SESSION: 'session',
    UNIT_PLATTER: 'platter'
}

# values are translation keys except for the official symbols (liter, kg, gram, ..)
UNIT_SYMBOLS = {
    UNIT_PIECE: 'piece_short',
    UNIT_LITER: 'l',
    UNIT_KG: 'kg',
    UNIT_GRAM: 'g',
    UNIT_HOUR: 'h',
    UNIT_MINUTE: 'min',
    UNIT_DAY: 'day_short',
    UNIT_WEEK: 'week_short',
    UNIT_MONTH: 'month_short',
    UNIT_PERSON: 'person_short',
    UNIT_SESSION: 'session',
    UNIT_PLATTER: 'platter'
}

ORDER_TYPE_SIMPLE = 1
ORDER_TYPE_ADVANCED = 2

SECONDS_IN_MINUTE = 60
SECONDS_IN_HOUR = 3600
SECONDS_IN_DAY = 86400
SECONDS_IN_WEEK = 604800
