# -*- coding: utf-8 -*-
# Copyright 2020 Green Valley NV
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
from typing import Optional

from mcfw.cache import cached
from mcfw.exceptions import HttpNotFoundException
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.dal.app import get_app_by_id
from rogerthat.models import AppNameMapping
from rogerthat.rpc import users
from solutions.common.models import SolutionBrandingSettings


@rest('/api/web/app/name/<app_name:[^/]+>', 'get')
@cached(0, lifetime=3600)
@returns(dict)
@arguments(app_name=unicode)
def rest_get_app_info(app_name):
    app_mapping = AppNameMapping.create_key(app_name).get()  # type: Optional[AppNameMapping]
    if not app_mapping:
        raise HttpNotFoundException('app_not_found')
    app = get_app_by_id(app_mapping.app_id)
    # TODO: Should not use SolutionBrandingSettings (use the app icon from the app itself)
    branding_settings = SolutionBrandingSettings.get_by_user(users.User(app.main_service))
    return {
        'app_id': app_mapping.app_id,
        'name': app.name,
        'url_name': app_mapping.name,
        'logo_url': branding_settings.avatar_url,
        'cover_url': branding_settings.logo_url,
    }
