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

from google.appengine.ext import db

from rogerthat.dal import put_and_invalidate_cache
from rogerthat.bizz.job import run_job
from rogerthat.models import App


def job(main_services):
    """Set app main service emails.

    Args:
        main_services (dict): app id to service email mapping
    """
    run_job(_get_all_apps, [], _set_main_service_email, [main_services])


def _get_all_apps():
    return App.all(keys_only=True)


def _set_main_service_email(app_key, main_services):
    app = db.get(app_key)

    if app:
        app_id = app.app_id
        if app_id in [App.APP_ID_ROGERTHAT, App.APP_ID_OSA_LOYALTY]:
            return

        if app_id in main_services:
            app.main_service = main_services[app.app_id]
            put_and_invalidate_cache(app)
