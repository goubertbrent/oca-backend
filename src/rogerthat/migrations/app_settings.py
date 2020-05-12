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

from rogerthat.models import App, AppSettings

from rogerthat.dal.app import get_app_settings


def migrate():
    for app in App.all():
        settings_key = AppSettings.create_key(app.app_id)
        new_settings = AppSettings(key=settings_key,
                                   background_fetch_timestamps=[21600] if app.type == App.APP_TYPE_CITY_APP else [])
        settings = AppSettings.get(settings_key) or new_settings
        settings.put()
        get_app_settings.invalidate_cache(app.app_id)  # @UndefinedVariable
