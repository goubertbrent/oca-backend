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

from mcfw.consts import REST_TYPE_TO
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.bizz.maps.reports import REPORTS_TAG
from rogerthat.to.maps import MapConfigTO
from solutions.common.bizz.maps import get_map_settings, save_map_settings


@rest('/console-api/maps/<app_id:[^/]+>', 'get', read_only_access=True, silent_result=True)
@returns(MapConfigTO)
@arguments(app_id=unicode)
def rest_get_map_settings(app_id):
    return MapConfigTO.from_model(get_map_settings(app_id, REPORTS_TAG))


@rest('/console-api/maps/<app_id:[^/]+>', 'put', read_only_access=True, silent_result=True, type=REST_TYPE_TO)
@returns(MapConfigTO)
@arguments(app_id=unicode, data=MapConfigTO)
def rest_put_map_settings(app_id, data):
    return MapConfigTO.from_model(save_map_settings(app_id, REPORTS_TAG, data))
