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

import json
import logging
from datetime import datetime

from google.appengine.api import urlfetch
from google.appengine.api.apiproxy_stub_map import UserRPC
from google.appengine.ext import db, ndb
from typing import List, Tuple, Dict

from mcfw.consts import MISSING
from mcfw.exceptions import HttpBadRequestException
from mcfw.utils import Enum
from rogerthat.bizz.opening_hours import OPENING_HOURS_RED_COLOR, OPENING_HOURS_ORANGE_COLOR
from rogerthat.consts import DEBUG
from rogerthat.models import OpeningHours, OpeningPeriod, OpeningHour, OpeningHourException, ServiceIdentity
from rogerthat.models.settings import SyncedNameValue, SyncedField, ServiceInfo
from rogerthat.rpc import users
from solutions.common.dal import get_solution_settings
from solutions.common.models import SolutionSettings
from solutions.common.models.cityapp import PaddleOrganizationalUnits, PaddleSettings
from solutions.common.to.paddle import PaddleOrganizationalUnitsTO, PaddleOrganizationUnitDetails, PaddleAddress, \
    PaddleRegularOpeningHours, PaddlePeriod, PaddleExceptionalOpeningHours


class ServiceInfoSyncProvider(Enum):
    PADDLE = 'paddle'


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


def _get_address_str(address):
    # type: (PaddleAddress) -> str
    lines = [
        address.thoroughfare,
        '%s %s' % (address.postal_code, address.locality)
    ]
    return '\n'.join(lines)


def populate_info_from_paddle(paddle_settings, paddle_data):
    # type: (PaddleSettings, PaddleOrganizationalUnits) -> List[SolutionSettings]
    keys = [ServiceInfo.create_key(users.User(m.service_email), ServiceIdentity.DEFAULT)
            for m in paddle_settings.mapping if m.service_email]
    models = {s.key: s for s in ndb.get_multi(keys)}  # type: dict[str, ndb.Model]
    paddle_mapping = {u.node.nid: u for u in paddle_data.units}  # type: Dict[str, PaddleOrganizationUnitDetails]
    to_put = []
    ndb_puts = []
    if not paddle_settings.synced_fields:
        # TODO make user editable
        paddle_settings.synced_fields = ['addresses', 'email_addresses', 'phone_numbers', 'websites']
        ndb_puts.append(paddle_settings)
    for mapping in paddle_settings.mapping:
        if not mapping.service_email:
            continue
        provider = ServiceInfoSyncProvider.PADDLE
        service_user = users.User(mapping.service_email)
        hours_key = OpeningHours.create_key(service_user, ServiceIdentity.DEFAULT)
        opening_hours = models.get(hours_key) or OpeningHours(key=hours_key, type=OpeningHours.TYPE_TEXTUAL)
        service_info = models.get(ServiceInfo.create_key(service_user, ServiceIdentity.DEFAULT))  # type: ServiceInfo
        original_service_info = service_info.to_dict()
        service_info.synced_fields = [SyncedField(key=field, provider=provider)
                                      for field in paddle_settings.synced_fields]
        paddle_info = paddle_mapping[mapping.paddle_id]
        changed, _ = _update_opening_hours_from_paddle(opening_hours, paddle_info)
        if 'phone_numbers' in paddle_settings.synced_fields:
            service_info.phone_numbers = _sync_paddle_values(service_info.phone_numbers, paddle_info.node.telephone)
        if 'email_addresses' in paddle_settings.synced_fields:
            service_info.email_addresses = _sync_paddle_values(service_info.email_addresses, paddle_info.node.email)
        if 'websites' in paddle_settings.synced_fields:
            service_info.websites = _sync_paddle_values(service_info.websites, paddle_info.node.website)
        if 'name' in paddle_settings.synced_fields:
            service_info.name = paddle_info.node.title
        if 'description' in paddle_settings.synced_fields and paddle_info.node.body:
            service_info.description = paddle_info.node.body
        changed = changed or original_service_info != service_info.to_dict()
        if changed:
            sln_settings = get_solution_settings(service_user)
            sln_settings.updates_pending = True
            to_put.append(sln_settings)
            ndb_puts.append(service_info)
    db.put(to_put)
    ndb.put_multi(ndb_puts)
    return to_put


def _sync_paddle_values(values, paddle_value):
    # type: (List[SynceNameValue], str) -> List[SyncedNameValue]
    value_found = False
    # Take copy so we can remove elements from the original list
    for val in list(values):
        if val.provider == ServiceInfoSyncProvider.PADDLE:
            value_found = True
            if val.value != paddle_value:
                if not paddle_value:
                    values.remove(val)
                else:
                    val.value = paddle_value
    if not value_found and paddle_value:
        value = SyncedNameValue()
        value.value = paddle_value
        value.provider = ServiceInfoSyncProvider.PADDLE
        values.append(value)
    return values


def _update_opening_hours_from_paddle(opening_hours, paddle_data):
    # type: (OpeningHours, PaddleOrganizationUnitDetails) -> Tuple[bool, OpeningHours]
    opening_hours.type = OpeningHours.TYPE_STRUCTURED
    new_periods = _paddle_periods_to_periods(paddle_data.opening_hours.regular, None)
    closing_days = [_paddle_closing_period_to_exception(closing_day)
                    for closing_day in paddle_data.opening_hours.closing_days]
    new_exceptional_opening_hours = [_convert_paddle_exceptional_hour(exception)
                                     for exception in paddle_data.opening_hours.exceptional_opening_hours]
    existing_opening_hours = opening_hours.to_dict()
    opening_hours.periods = new_periods
    opening_hours.exceptional_opening_hours = closing_days + new_exceptional_opening_hours
    opening_hours.sort_dates()
    new_opening_hours = opening_hours.to_dict()
    # python actually implements deep compare by default
    changed = existing_opening_hours != new_opening_hours
    if changed:
        opening_hours.put()
    return changed, opening_hours


def _paddle_periods_to_periods(hours, color):
    # type: (PaddleRegularOpeningHours, str) -> List[OpeningPeriod]
    periods = []
    days = [hours.sunday, hours.monday, hours.tuesday, hours.wednesday, hours.thursday, hours.friday, hours.saturday]

    for day_number, paddle_periods in enumerate(days):
        if paddle_periods is MISSING:
            continue
        for paddle_period in paddle_periods:
            period = OpeningPeriod()
            period.open = OpeningHour()
            period.open.day = day_number
            period.open.time = _paddle_time_to_time(paddle_period.start)
            period.close = OpeningHour()
            period.close.day = day_number
            period.close.time = _paddle_time_to_time(paddle_period.end)
            period.description = paddle_period.description
            period.description_color = color
            periods.append(period)
    return periods


def _paddle_time_to_time(paddle_time):
    return paddle_time.replace(':', '')


def _convert_paddle_exceptional_hour(exceptional_hours):
    # type: (PaddleExceptionalOpeningHours) -> OpeningHourException
    orange_color = OPENING_HOURS_ORANGE_COLOR
    exception = OpeningHourException()
    exception.start_date = _parse_paddle_date(exceptional_hours.start)
    exception.end_date = _parse_paddle_date(exceptional_hours.end) or exception.start_date
    exception.description = exceptional_hours.description
    exception.description_color = orange_color
    exception.periods = _paddle_periods_to_periods(exceptional_hours.opening_hours, orange_color)
    return exception


def _paddle_closing_period_to_exception(paddle_period):
    # type: (PaddlePeriod) -> OpeningHourException
    exception = OpeningHourException()
    exception.start_date = _parse_paddle_date(paddle_period.start)
    exception.end_date = _parse_paddle_date(paddle_period.end) or exception.start_date
    exception.description = paddle_period.description
    exception.description_color = OPENING_HOURS_RED_COLOR
    exception.periods = []
    return exception


def _parse_paddle_date(date):
    # Not actually an iso date, dd--mm-yy
    return datetime.strptime(date, '%d-%m-%Y').date() if date else None
