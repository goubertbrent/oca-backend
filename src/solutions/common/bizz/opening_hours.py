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

from __future__ import unicode_literals

from datetime import datetime

from babel.dates import format_date, get_day_names, format_time
from typing import List

from mcfw.exceptions import HttpBadRequestException
from rogerthat.bizz.opening_hours import is_always_open, is_always_closed
from rogerthat.models import OpeningHours, OpeningPeriod, OpeningHourException
from rogerthat.rpc import users
from solutions import translate
from solutions.common.bizz import broadcast_updates_pending
from solutions.common.dal import get_solution_settings
from solutions.common.to.opening_hours import OpeningHoursTO


DAY_MAPPING = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']


class HoursOverlapException(HttpBadRequestException):
    def __init__(self, message):
        super(HoursOverlapException, self).__init__('oca.error', {'message': message})


def get_opening_hours(service_user, service_identity):
    # type: (users.User, str) -> OpeningHours
    key = OpeningHours.create_key(service_user, service_identity)
    return key.get() or OpeningHours(key=key, type=OpeningHours.TYPE_TEXTUAL, text='')


def put_opening_hours(service_user, service_identity, data):
    # type: (users.User, str, OpeningHoursTO) -> OpeningHours
    opening_hours = get_opening_hours(service_user, service_identity)
    opening_hours.type = data.type
    opening_hours.text = data.text and data.text.strip()
    opening_hours.title = data.title
    opening_hours.periods = [OpeningPeriod.from_to(period) for period in data.periods]
    opening_hours.exceptional_opening_hours = [OpeningHourException.from_to(exception)
                                               for exception in data.exceptional_opening_hours]
    opening_hours.put()

    sln_settings = get_solution_settings(service_user)
    if not sln_settings.updates_pending:
        sln_settings.updates_pending = True
        sln_settings.put()
    broadcast_updates_pending(sln_settings)
    return opening_hours


def _get_day_int(day_str):
    # type: (str) -> int
    return DAY_MAPPING.index(day_str)


def _get_day_str(day_int):
    # type: (int) -> str
    return DAY_MAPPING[day_int]


def _get_open_hour_text(period, locale):
    # type: (OpeningPeriod, str) -> str
    if period.is_open_24_hours:
        return translate(locale, 'oca.open_24_hours')
    open_time = format_time(period.open.datetime, 'short', locale=locale)
    close_time = format_time(period.close.datetime, 'short', locale=locale)
    line = '%s — %s' % (open_time, close_time)
    if period.description:
        line += ' %s' % period.description
    return line


def _get_opening_periods_lines(opening_periods, day_names, locale):
    # type: (List[OpeningPeriod], List[str], str) -> List[str]
    lines = []
    previous_day_name = None
    for period in opening_periods:
        day_name = day_names[period.open.day]
        # Assumes these are sorted by day
        if previous_day_name != day_name:
            if lines:
                lines.append('')
            lines.append(day_name)
        lines.append(_get_open_hour_text(period, locale))
        previous_day_name = day_name
    return lines


def opening_hours_to_text(opening_hours, locale, current_datetime):
    # type: (OpeningHours, str, datetime) -> str
    if not opening_hours:
        return None
    if opening_hours.type in (OpeningHours.TYPE_TEXTUAL, OpeningHours.TYPE_NOT_RELEVANT,):
        return opening_hours.text
    day_names = get_day_names(locale=locale).values()  # Starts on monday
    day_names.insert(0, day_names.pop())  # Starts on sunday
    if is_always_open(opening_hours.periods):
        return translate(locale, 'always_open')
    if is_always_closed(opening_hours.periods):
        return translate(locale, 'always_closed')
    lines = _get_opening_periods_lines(opening_hours.periods, day_names, locale)
    if opening_hours.exceptional_opening_hours:
        lines.append('')
        lines.append(translate(locale, 'deviating_opening_hours'))
        lines.append('')
    current_date = current_datetime.date()
    for exception in opening_hours.exceptional_opening_hours:
        if exception.end_date < current_date:
            continue
        start_date = format_date(exception.start_date, 'short', locale)
        if exception.start_date == exception.end_date:
            day_str = start_date
        else:
            end_date = format_date(exception.end_date, 'short', locale)
            day_str = '%s — %s' % (start_date, end_date)
        if not exception.periods:
            closed = translate(locale, 'oca.closed')
            if exception.description:
                description = '%s — %s' % (exception.description, closed)
            else:
                description = closed
        else:
            description = exception.description
        lines.append('%s %s' % (day_str, description))
        if exception.periods:
            lines.extend(_get_opening_periods_lines(exception.periods, day_names, locale))
    return '\n'.join(lines)
