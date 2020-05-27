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

import datetime
from collections import defaultdict

import pytz
from babel.dates import format_date, format_time
from dateutil.relativedelta import relativedelta
from typing import List, Tuple

from rogerthat.models import OpeningHours, OpeningHour
from rogerthat.to.maps import WeekDayTextTO, MapItemLineTextPartTO
from rogerthat.translations import localize

MIDNIGHT = datetime.time(hour=0, minute=0)
_NAMES = {}


def is_always_open(periods):
    return len(periods) == 7 and all(period.is_open_24_hours for period in periods)


def is_always_closed(periods):
    return len(periods) == 0


def get_opening_hours_info(opening_hours, timezone, lang, now=None):
    # type: (OpeningHours, str, str, datetime) -> Tuple[bool, str, str, List[WeekDayTextTO]]
    if not now:
        now = datetime.datetime.utcnow()
    now_ = now + pytz.timezone(timezone).utcoffset(now)
    exceptions = opening_hours.exceptional_opening_hours
    now_open, open_until, extra_description = get_open_until_with_exceptions(opening_hours.periods, exceptions, now_,
                                                                             lang)
    weekday_text = get_weekday_text(opening_hours.periods, exceptions, lang, now_.date())
    return now_open, open_until, extra_description, weekday_text


def get_open_until(periods, now, lang):
    if len(periods) == 0:
        return False, localize(lang, 'always_closed'), None

    all_periods = []
    for item in periods.values():
        all_periods.extend(item['periods'])
    if is_always_open(all_periods):
        return True, localize(lang, 'open_24_hours'), None

    weekday = _get_weekday(now)
    now_time = datetime.time(now.hour, now.minute)
    for day in xrange(0, 6):
        next_weekday = (weekday + day) % 7
        data = periods.get(next_weekday)
        if not data:
            continue
        for period in data['periods']:
            if period.open and period.close:
                if period.open.day == weekday:
                    if now_time >= period.open.datetime:
                        if period.close.day != weekday:
                            day_name = _get_weekday_names(lang)[period.close.day]
                            hour_str = _format_opening_hour(period and period.close, lang)
                            open_until_str = localize(lang, 'open_until', time='%s %s' % (day_name, hour_str))
                            return True, open_until_str, next_weekday
                        elif now_time < period.close.datetime:
                            return True, _format_open_until(period, lang), next_weekday
                elif period.close.day == weekday:
                    # open.day != weekday, only needed to check the time
                    if now_time < period.close.datetime:
                        return True, _format_open_until(period, lang), next_weekday
            elif period.open:
                # close is NULL
                if period.open.day == weekday and now_time >= period.open.datetime:
                    return True, _format_open_until(None, lang), next_weekday
            elif period.close:
                # open is NULL
                if period.close.day == weekday and now_time < period.close.datetime:
                    return True, _format_open_until(period, lang), next_weekday

    # Closed, check if this store will open today
    for day in xrange(0, 6):
        next_weekday = (weekday + day) % 7
        data = periods.get(next_weekday)
        if not data:
            continue
        for period in data['periods']:
            if period.open and period.open.day == weekday and now_time <= period.open.datetime:
                hour_str = _format_opening_hour(period.open, lang)
                return False, localize(lang, 'opens_on_time', time='%s' % hour_str), next_weekday

    for i in xrange(1, 7):
        next_weekday = (weekday + i) % 7
        data = periods.get(next_weekday)
        if not data:
            continue
        for period in data['periods']:
            if not period.open:
                continue
            period_day = now + relativedelta(days=i)
            day_str = format_date(period_day, format='EEEE', locale=lang)
            hour_str = _format_opening_hour(period.open, lang)
            return False, localize(lang, 'opens_on_day_and_time', day=day_str, time='%s' % hour_str), next_weekday

    return False, localize(lang, 'closed'), None


def get_open_until_with_exceptions(periods, exceptions, now, lang):
    exception_periods = defaultdict(list)
    weekday_exceptions = dict()
    now_date = now.date()
    for i in xrange(7):
        current_day = now_date + relativedelta(days=i)
        for exception in exceptions:
            if exception.start_date <= current_day <= exception.end_date:
                data = get_weekday_periods_day(exception.periods, current_day)
                exception_periods.update(data)
                weekday = _get_weekday(current_day)
                weekday_exceptions[weekday] = exception
                break
        else:
            exception_periods.update(get_weekday_periods_day(periods, current_day))

    now_open, open_until, weekday = get_open_until(exception_periods, now, lang)
    exception_message = None
    if weekday is None:
        if len(weekday_exceptions) > 0:
            exception_message = weekday_exceptions.values()[0].description
    elif weekday in weekday_exceptions:
        exception_message = weekday_exceptions[weekday].description
    else:
        now_weekday = _get_weekday(now_date)
        for day in xrange(0, 6):
            next_weekday = (now_weekday + day) % 7
            if next_weekday > weekday:
                break
            if next_weekday in weekday_exceptions:
                exception_message = weekday_exceptions[next_weekday].description
                break
    return now_open, open_until, exception_message


def _format_open_until(period, lang):
    return localize(lang, 'open_until', time=_format_opening_hour(period and period.close, lang))


def _get_weekday(datetime):
    return (datetime.weekday() + 1) % 7


def _get_weekday_names(lang):
    # type: (unicode) -> dict
    if lang in _NAMES:
        return _NAMES[lang]
    day_names = {}
    today = datetime.datetime.today()
    for days in xrange(7):
        date = today + datetime.timedelta(days=days)
        weekday = _get_weekday(date)
        day_names[weekday] = format_date(date, 'EEEE', locale=lang)
    _NAMES[lang] = day_names
    return day_names


def _format_opening_hour(opening_hour, lang):
    # type: (OpeningHour, unicode) -> unicode
    return format_time(opening_hour and opening_hour.datetime or MIDNIGHT, 'short', locale=lang)


def get_weekday_text(periods, exceptions, lang, now):
    from rogerthat.bizz.maps.services import get_openinghours_color, OPENING_HOURS_ORANGE_COLOR
    lines_per_day = defaultdict(list)
    weekday_exceptions = dict()
    for i in xrange(7):
        current_day = now + relativedelta(days=i)
        for exception in exceptions:
            if exception.start_date <= current_day <= exception.end_date:
                data = get_weekday_text_day(exception.periods, lang, current_day)
                if exception.description:
                    if not data:
                        weekday = _get_weekday(current_day)
                        weekday_exceptions[weekday] = exception
                    for p in data:
                        period = data[p]
                        if not period.get('has_description', False):
                            period['lines'].append(MapItemLineTextPartTO(text=exception.description,
                                                                         color=get_openinghours_color(exception.description_color or OPENING_HOURS_ORANGE_COLOR)))

                for day in data:
                    current_data = lines_per_day.get(day) or []
                    if current_data:
                        current_data.extend(data[day]['lines'])
                    else:
                        current_data = data[day]['lines']
                    lines_per_day[day] = current_data
                break
        else:
            data = get_weekday_text_day(periods, lang, current_day)
            for day in data:
                current_data = lines_per_day.get(day) or []
                if current_data:
                    current_data.extend(data[day]['lines'])
                else:
                    current_data = data[day]['lines']
                lines_per_day[day] = current_data

    day_names = _get_weekday_names(lang)
    days = [1, 2, 3, 4, 5, 6, 0]  # Monday, Tuesday, ..., Sunday
    result = []
    for day in days:
        lines = lines_per_day.get(day)
        if not lines:
            lines = [MapItemLineTextPartTO(text=localize(lang, 'closed'))]
            if day in weekday_exceptions:
                lines.append(MapItemLineTextPartTO(text=weekday_exceptions[day].description,
                                                   color=get_openinghours_color(weekday_exceptions[day].description_color or OPENING_HOURS_ORANGE_COLOR)))
            result.append(WeekDayTextTO(day=day_names[day],
                                        lines=lines))
            continue
        result.append(WeekDayTextTO(day=day_names[day],
                                    lines=lines))
    return result


def get_weekday_text_day(periods, lang, day):
    from rogerthat.bizz.maps.services import get_openinghours_color, OPENING_HOURS_ORANGE_COLOR
    weekday = _get_weekday(day)
    if not periods:
        return {weekday: {'lines': [MapItemLineTextPartTO(text=localize(lang, 'closed'))]}}
    if is_always_open(periods):
        return {weekday: {'lines': [MapItemLineTextPartTO(text=localize(lang, 'open_24_hours')),
                                    MapItemLineTextPartTO(text=periods[0].description,
                                                          color=get_openinghours_color(periods[0].description_color or OPENING_HOURS_ORANGE_COLOR))],
                          'has_description': True}}

    periods_weekday = {}
    for period in sorted(periods, key=lambda p: (p.open and p.open.day, p.open and p.open.time)):
        period_weekday = period.open.day if period.open else period.close.day
        if period_weekday != weekday:
            continue

        if period.is_open_24_hours:
            periods_weekday[weekday] = {}
            periods_weekday[weekday]['lines'] = [MapItemLineTextPartTO(text=localize(lang, 'open_24_hours'))]
            periods_weekday[weekday]['has_description'] = False
            if period.description:
                periods_weekday[weekday]['lines'].append(MapItemLineTextPartTO(
                    text=period.description,
                    color=get_openinghours_color(period.description_color or OPENING_HOURS_ORANGE_COLOR)
                ))
                periods_weekday[weekday]['has_description'] = True
            continue

        if weekday not in periods_weekday:
            periods_weekday[weekday] = {'lines': [],
                                        'has_description': False}

        line = MapItemLineTextPartTO(text='%s - %s' % (_format_opening_hour(period.open, lang),
                                                       _format_opening_hour(period.close, lang)))
        periods_weekday[weekday]['lines'].append(line)

        if period.description:
            line = MapItemLineTextPartTO(text=period.description,
                                         color=get_openinghours_color(
                                             period.description_color or OPENING_HOURS_ORANGE_COLOR))
            periods_weekday[weekday]['lines'].append(line)
            periods_weekday[weekday]['has_description'] = True

    return periods_weekday


def get_weekday_periods_day(periods, day):
    weekday = _get_weekday(day)
    if not periods:
        return {}
    if is_always_open(periods):
        return {weekday: {'periods': periods}}

    periods_weekday = {}
    for period in sorted(periods, key=lambda p: (p.open and p.open.day, p.open and p.open.time)):
        period_weekday = period.open.day if period.open else period.close.day
        if period_weekday != weekday:
            continue

        if period.is_open_24_hours:
            periods_weekday[weekday] = {'periods': [period]}
            continue

        if weekday not in periods_weekday:
            periods_weekday[weekday] = {'periods': []}

        periods_weekday[weekday]['periods'].append(period)

    return periods_weekday
