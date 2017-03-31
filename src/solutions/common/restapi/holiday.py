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
# @@license_version:1.3@@

from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from rogerthat.to import ReturnStatusTO, RETURNSTATUS_TO_SUCCESS
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from solutions import translate as common_translate
from solutions.common import SOLUTION_COMMON
from solutions.common.dal import get_solution_settings
from solutions.common.to.holiday import HolidayTO


@rest("/common/settings/holiday/add", "post")
@returns(ReturnStatusTO)
@arguments(holiday=HolidayTO)
def add_holiday(holiday):
    from solutions.common.bizz.holiday import add_holiday as add_holiday_bizz
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    try:
        add_holiday_bizz(service_user, service_identity, holiday)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException, e:
        sln_settings = get_solution_settings(service_user)
        return ReturnStatusTO.create(False, common_translate(sln_settings.main_language, SOLUTION_COMMON, e.message))


@rest("/common/settings/holiday/delete", "post")
@returns(ReturnStatusTO)
@arguments(holiday=HolidayTO)
def delete_holiday(holiday):
    from solutions.common.bizz.holiday import delete_holiday as delete_holiday_bizz
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    try:
        delete_holiday_bizz(service_user, service_identity, holiday)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException, e:
        sln_settings = get_solution_settings(service_user)
        return ReturnStatusTO.create(False, common_translate(sln_settings.main_language, SOLUTION_COMMON, e.message))


@rest("/common/settings/holiday/out_of_office_message", "post")
@returns(ReturnStatusTO)
@arguments(message=unicode)
def save_out_of_office_message(message):
    from solutions.common.bizz.holiday import save_out_of_office_message as save_oof_message
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    try:
        save_oof_message(service_user, service_identity, message)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException, e:
        sln_settings = get_solution_settings(service_user)
        return ReturnStatusTO.create(False, common_translate(sln_settings.main_language, SOLUTION_COMMON, e.message))
