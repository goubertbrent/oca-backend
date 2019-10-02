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

from google.appengine.ext.deferred import deferred

from mcfw.consts import REST_TYPE_TO
from mcfw.exceptions import HttpNotFoundException
from mcfw.restapi import rest
from mcfw.rpc import arguments, returns
from rogerthat.bizz.app import get_app, AppDoesNotExistException
from rogerthat.bizz.authentication import Scopes
from solutions.common.bizz.app import import_location_data
from solutions.common.bizz.participation.proxy import register_app
from solutions.common.to.app import RegisterAppTO


@rest('/bob/api/apps/<app_id:[^/]+>/register', 'post', scopes=Scopes.APPS_CREATOR, type=REST_TYPE_TO)
@returns()
@arguments(app_id=unicode, data=RegisterAppTO)
def rest_import_location_data(app_id, data):
    # type: (unicode, RegisterAppTO) -> None
    try:
        app = get_app(app_id)
    except AppDoesNotExistException:
        raise HttpNotFoundException('app_not_found', data={'app_id': app_id})
    register_app(app_id, data.ios_dev_team)
    if data.official_id:
        deferred.defer(import_location_data, app_id, app.country, data.official_id)
