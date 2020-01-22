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
from __future__ import unicode_literals

from datetime import datetime
import json
import logging

from babel.dates import get_day_names
from google.appengine.api import urlfetch
from google.appengine.api.apiproxy_stub_map import UserRPC
from google.appengine.ext import db, deferred

from mcfw.consts import MISSING
from mcfw.exceptions import HttpBadRequestException
from rogerthat.bizz.opening_hours import save_textual_opening_hours
from rogerthat.consts import DEBUG
from rogerthat.rpc import users
from solutions import translate, SOLUTION_COMMON
from solutions.common.models import SolutionSettings
from solutions.common.models.cityapp import PaddleOrganizationalUnits, PaddleSettings
from solutions.common.to.paddle import PaddleOrganizationalUnitsTO, PaddleOrganizationUnitDetails, PaddleOpeningHours, \
    PaddleAddress


def get_organizational_units(base_url):
    # type: (str) -> UserRPC
    url = '%s/organizational_units' % base_url
    rpc_item = urlfetch.create_rpc(20)
    return urlfetch.make_fetch_call(rpc_item, url)


def _get_result(rpc_item):
    result = rpc_item.get_result()  # type: urlfetch._URLFetchResult
    if result.status_code != 200:
        logging.debug('%d: %s', result.status_code, result.content)
        raise Exception('Error while fetching data from paddle')
    if DEBUG:
        logging.debug(result.content)
    return json.loads(result.content)


def _rpc_to_organization_units(rpc_item):
    # type: (UserRPC) -> PaddleOrganizationalUnitsTO
    return PaddleOrganizationalUnitsTO.from_dict(_get_result(rpc_item))


def _rpc_to_organization_unit_details(rpc_item):
    # type: (UserRPC) -> PaddleOrganizationUnitDetails
    return PaddleOrganizationUnitDetails.from_dict(_get_result(rpc_item))


def get_organizational_unit_details(base_url, organizational_unit_id):
    # type: (str, str) -> UserRPC
    url = '%s/organizational_units/%s' % (base_url, organizational_unit_id)
    rpc_item = urlfetch.create_rpc(15)
    return urlfetch.make_fetch_call(rpc_item, url)


def get_paddle_info(paddle_settings):
    # type: (PaddleSettings) -> PaddleOrganizationalUnits
    try:
        organizational_units = _rpc_to_organization_units(get_organizational_units(paddle_settings.base_url))
    except urlfetch.InvalidURLError:
        raise HttpBadRequestException('invalid_url')
    rpcs = [get_organizational_unit_details(paddle_settings.base_url, organizational_unit.nid)
            for organizational_unit in organizational_units.list]
    model = PaddleOrganizationalUnits(key=PaddleOrganizationalUnits.create_key(paddle_settings.service_user))
    for organizational_unit, rpc in zip(organizational_units.list, rpcs):
        organizational_unit_details = _rpc_to_organization_unit_details(rpc)
        model.units.append(organizational_unit_details)
    return model


def _get_period_text(periods):
    lines = []
    for period in periods:
        if period.end:
            line = '%s - %s' % (period.start, period.end)
        else:
            line = period.start
        if period.description:
            line += ' ' + period.description
        lines.append(line)
    return '\n'.join(lines)


def _get_opening_hours_text(day_names, opening_hours):
    # type: (str, PaddleRegularOpeningHours) -> object
    lines = []
    days = [opening_hours.monday, opening_hours.tuesday, opening_hours.wednesday,
            opening_hours.thursday, opening_hours.friday, opening_hours.saturday,
            opening_hours.sunday]
    for i, periods in enumerate(days):
        if periods and periods is not MISSING:
            lines.append(day_names[i])
            lines.append(_get_period_text(periods))
            lines.append('')
    return '\n'.join(lines).strip()


def _opening_hours_to_str(language, opening_hours):
    # type: (str, PaddleOpeningHours) -> str
    day_names = get_day_names(locale=language)
    lines = []
    regular = _get_opening_hours_text(day_names, opening_hours.regular)
    if regular:
        lines.append(regular)

    if opening_hours.closing_days:
        now = datetime.now()
        closing_days_in_future = []
        for day in opening_hours.closing_days:
            start_date = datetime.strptime(day.start, '%d-%m-%Y')
            if start_date > now:
                closing_days_in_future.append(day)
        if closing_days_in_future:
            lines.append('')
            lines.append(translate(language, SOLUTION_COMMON, 'closing_days'))
            lines.append(_get_period_text(closing_days_in_future))
    exceptional = opening_hours.exceptional_opening_hours
    if exceptional and exceptional.opening_hours is not MISSING:
        lines.append('')
        description = exceptional.description if exceptional.description else translate(language, SOLUTION_COMMON,
                                                                                        'deviating_opening_hours')
        if exceptional.end:
            lines.append('%s: %s - %s' % (description, exceptional.start, exceptional.end))
        else:
            lines.append('%s: %s' % (description, exceptional.start))
        lines.append(_get_opening_hours_text(day_names, exceptional.opening_hours))
    return '\n'.join(lines).strip()


def _get_address_str(address):
    # type: (PaddleAddress) -> str
    lines = [
        address.thoroughfare,
        '%s %s' % (address.postal_code, address.locality)
    ]
    return '\n'.join(lines)


def populate_info_from_paddle(paddle_settings, paddle_data):
    # type: (PaddleSettings, PaddleOrganizationalUnits) -> list[SolutionSettings]
    settings_keys = [SolutionSettings.create_key(users.User(m.service_email))
                     for m in paddle_settings.mapping if m.service_email]
    settings_mapping = {s.service_user.email(): s for s in db.get(settings_keys)}  # type: dict[str, SolutionSettings]
    paddle_mapping = {u.node.nid: u for u in paddle_data.units}  # type: dict[str, PaddleOrganizationUnitDetails]
    to_put = []
    for mapping in paddle_settings.mapping:
        if not mapping.service_email:
            continue
        sln_settings = settings_mapping[mapping.service_email]
        paddle_info = paddle_mapping[mapping.paddle_id]
        changed = False
        if paddle_info.node.telephone and sln_settings.phone_number != paddle_info.node.telephone:
            changed = True
            sln_settings.phone_number = paddle_info.node.telephone
        if paddle_info.node.email and paddle_info.node.email != sln_settings.qualified_identifier:
            changed = True
            sln_settings.qualified_identifier = paddle_info.node.email
        if paddle_info.opening_hours:
            hours = _opening_hours_to_str(sln_settings.main_language, paddle_info.opening_hours)
            changed = changed or hours != sln_settings.opening_hours
            sln_settings.opening_hours = hours
            deferred.defer(save_textual_opening_hours, mapping.service_email, sln_settings.opening_hours)
        if paddle_info.node.address and paddle_info.node.address.is_valid():
            new_address = _get_address_str(paddle_info.node.address)
            changed = changed or sln_settings.address != new_address
            sln_settings.address = new_address
        if changed:
            sln_settings.updates_pending = True
            to_put.append(sln_settings)
    db.put(to_put)
    return to_put
