# -*- coding: utf-8 -*-
# Copyright 2021 Green Valley NV
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
import logging
import requests
from requests import RequestException
from typing import Optional, Tuple

from mcfw.exceptions import HttpBadRequestException
from rogerthat.rpc import users
from solutions.common.bizz import broadcast_updates_pending
from solutions.common.dal import get_solution_settings
from solutions.common.integrations.timeblockr.models import TimeblockrSettings
from solutions.common.integrations.timeblockr.timeblockr import get_locations


def get_timeblockr_settings(service_user):
    # type: (users.User) -> Optional[TimeblockrSettings]
    key = TimeblockrSettings.create_key(service_user)
    return key.get() or TimeblockrSettings(key=key)


def save_timeblockr_settings(service_user, url, api_key):
    settings = TimeblockrSettings(key=TimeblockrSettings.create_key(service_user))
    settings.url = url
    settings.api_key = api_key
    was_enabled = settings.enabled
    settings.enabled = is_valid_timeblockr_settings(settings)
    settings.put()
    if was_enabled != settings.enabled:
        sln_settings = get_solution_settings(service_user)
        sln_settings.updates_pending = True
        sln_settings.put()
        broadcast_updates_pending(sln_settings)
    if not settings.enabled:
        raise HttpBadRequestException('Invalid settings or server temporarily unreachable')
    else:
        return settings


def is_valid_timeblockr_settings(settings):
    # type: (TimeblockrSettings) -> bool
    try:
        get_locations(settings)
        return True
    except Exception as e:
        logging.debug(e, exc_info=True)
        return False
