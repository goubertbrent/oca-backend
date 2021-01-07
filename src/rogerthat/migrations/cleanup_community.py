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

from google.appengine.ext import db

from rogerthat.bizz.job import run_job
from rogerthat.models import App
from rogerthat.models.common import NdbModel


def cleanup_app():
    run_job(_query_app, [], _cleanup_app, [])

def _query_app():
    return App.all(keys_only=True)

def _cleanup_app(app_key):
    app = db.get(app_key)
    updated = False
    for attr in ('auto_connected_services', 'embedded_apps'):
        if hasattr(app, attr):
            delattr(app, attr)
            updated = True
    if updated:
        app.put()


class CityAppProfile(NdbModel):
    pass

def cleanup_city_app_profile():
    from rogerthat.migrations.delete_all_models_by_kind import job
    job(CityAppProfile)
