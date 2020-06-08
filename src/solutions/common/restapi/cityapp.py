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

import logging

from mcfw.consts import MISSING
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from rogerthat.service.api import app
from rogerthat.to import ReturnStatusTO, RETURNSTATUS_TO_SUCCESS
from rogerthat.to.app import AppSettingsTO
from solutions import translate
from solutions.common.bizz.cityapp import get_uitdatabank_events
from solutions.common.dal import get_solution_settings
from solutions.common.dal.cityapp import get_cityapp_profile, \
    get_uitdatabank_settings
from solutions.common.to.cityapp import CityAppProfileTO, UitdatabankSettingsTO, \
    UitdatabankCheckTO


@rest("/common/cityapp/settings/load", "get", read_only_access=True)
@returns(CityAppProfileTO)
@arguments()
def load_cityapp_settings():
    service_user = users.get_current_user()
    settings = get_cityapp_profile(service_user)
    return CityAppProfileTO.from_model(settings)


@rest('/common/settings/app', 'get', read_only_access=True)
@returns(AppSettingsTO)
@arguments()
def rest_get_app_settings():
    return app.get_settings()


@rest('/common/settings/app', 'post')
@returns(AppSettingsTO)
@arguments(settings=AppSettingsTO)
def rest_save_app_settings(settings):
    """
    Args:
        settings (AppSettingsTO)
    """
    settings.oauth = MISSING
    settings.background_fetch_timestamps = MISSING
    settings.wifi_only_downloads = MISSING
    return app.put_settings(settings)


@rest ("/common/cityapp/settings/save", "post")
@returns(ReturnStatusTO)
@arguments(gather_events=bool)
def save_cityapp_settings(gather_events):
    from solutions.common.bizz.cityapp import save_cityapp_settings as save_cityapp_settings_bizz
    try:
        service_user = users.get_current_user()
        save_cityapp_settings_bizz(service_user, gather_events)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@rest("/common/cityapp/uitdatabank/settings", "get", read_only_access=True)
@returns(UitdatabankSettingsTO)
@arguments()
def load_uitdatabank_settings():
    service_user = users.get_current_user()
    settings = get_uitdatabank_settings(service_user)
    return UitdatabankSettingsTO.from_model(settings)


@rest("/common/cityapp/uitdatabank/settings", "post", read_only_access=True)
@returns(ReturnStatusTO)
@arguments(version=unicode, params=dict)
def save_uitdatabank_settings(version, params):
    from solutions.common.bizz.cityapp import save_uitdatabank_settings as save_uitdatabank_settings_bizz
    try:
        service_user = users.get_current_user()
        save_uitdatabank_settings_bizz(service_user, version, params)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@rest("/common/cityapp/uitdatabank/check", "get", read_only_access=True)
@returns(UitdatabankCheckTO)
@arguments()
def uitdatabank_check_cityapp_settings():
    service_user = users.get_current_user()

    settings = get_uitdatabank_settings(service_user)
    sln_settings = get_solution_settings(service_user)
    try:
        success, count, result = get_uitdatabank_events(settings, 1, 50)
        if not success:
            try:
                result = translate(sln_settings.main_language, result)
            except ValueError:
                pass
    except Exception:
        logging.debug('Failed to check uitdatabank.be version: %s params: %s', settings.version, settings.params, exc_info=1)
        success, result = False, translate(sln_settings.main_language, 'error-occured-unknown-try-again')

    if success:
        if not settings.enabled:
            settings.enabled = True
            settings.put()
        return UitdatabankCheckTO.create(True, count=count)
    if settings.enabled:
        settings.enabled = False
        settings.put()
    return UitdatabankCheckTO.create(False, result)
