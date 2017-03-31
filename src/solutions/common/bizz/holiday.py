# -*- coding: utf-8 -*-
# Copyright 2017 GIG Technology NV
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

from types import NoneType

from rogerthat.dal import put_and_invalidate_cache
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from google.appengine.ext import db
from mcfw.rpc import returns, arguments
from solutions.common.bizz import broadcast_updates_pending
from solutions.common.dal import get_solution_settings, get_solution_identity_settings, \
    get_solution_settings_or_identity_settings
from solutions.common.to.holiday import HolidayTO
from solutions.common.utils import is_default_service_identity

class InvalidHolidayException(BusinessException):
    pass

@returns(NoneType)
@arguments(service_user=users.User, service_identity=unicode, holiday=HolidayTO)
def add_holiday(service_user, service_identity, holiday):
    if holiday.start > holiday.end:
        raise InvalidHolidayException('The specified period ends before it starts.')

    def trans():
        sln_settings = get_solution_settings(service_user)
        sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, service_identity)
        i = 0
        while i < len(sln_i_settings.holidays) / 2:
            if holiday.start < sln_i_settings.holidays[2 * i]:
                break
            i += 1
        sln_i_settings.holidays.insert(2 * i, holiday.start)
        sln_i_settings.holidays.insert(2 * i + 1, holiday.end)

        sln_settings.updates_pending = True
        put_and_invalidate_cache(sln_settings, sln_i_settings)
        return sln_settings

    xg_on = db.create_transaction_options(xg=True)
    sln_settings = db.run_in_transaction_options(xg_on, trans)
    broadcast_updates_pending(sln_settings)


@returns(NoneType)
@arguments(service_user=users.User, service_identity=unicode, holiday=HolidayTO)
def delete_holiday(service_user, service_identity, holiday):
    def trans():
        sln_settings = get_solution_settings(service_user)
        sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, service_identity)
        for i in range(len(sln_i_settings.holidays) / 2):
            if sln_i_settings.holidays[2 * i] == holiday.start:
                del sln_i_settings.holidays[2 * i:2 * i + 2]
                break
        else:
            raise InvalidHolidayException('holiday-not-found')

        sln_settings.updates_pending = True
        put_and_invalidate_cache(sln_settings, sln_i_settings)
        return sln_settings

    xg_on = db.create_transaction_options(xg=True)
    sln_settings = db.run_in_transaction_options(xg_on, trans)
    broadcast_updates_pending(sln_settings)


@returns(NoneType)
@arguments(service_user=users.User, service_identity=unicode, message=unicode)
def save_out_of_office_message(service_user, service_identity, message):
    def trans():
        sln_settings = get_solution_settings(service_user)
        sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, service_identity)
        sln_i_settings.holiday_out_of_office_message = db.Text(message)
        sln_settings.updates_pending = True
        put_and_invalidate_cache(sln_settings, sln_i_settings)
        return sln_settings

    xg_on = db.create_transaction_options(xg=True)
    sln_settings = db.run_in_transaction_options(xg_on, trans)
    broadcast_updates_pending(sln_settings)


@returns(bool)
@arguments(service_user=users.User, service_identity=unicode, date=long)
def is_in_holiday(service_user, service_identity, date):
    if is_default_service_identity(service_identity):
        sln_i_settings = get_solution_settings(service_user)
    else:
        sln_i_settings = get_solution_identity_settings(service_user, service_identity)
    return sln_i_settings.is_in_holiday_for_date(date)
