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
from rogerthat.bizz.communities.communities import get_community
from rogerthat.bizz.service import validate_app_admin
from rogerthat.dal.profile import get_service_profile
from rogerthat.rpc import users
from rogerthat.rpc.users import get_current_session
from solutions.common.bizz.maps import get_map_settings, save_map_settings
from solutions.common.to.reports import MapConfigTO


@rest('/common/maps/<map_tag:[^/]+>', 'get', read_only_access=True, silent_result=True)
@returns(MapConfigTO)
@arguments(map_tag=unicode)
def rest_get_map_settings(map_tag):
    app_id = _check_permissions()
    return MapConfigTO.from_model(get_map_settings(app_id, map_tag))


@rest('/common/maps/<map_tag:[^/]+>', 'put', read_only_access=True, silent_result=True, type=REST_TYPE_TO)
@returns(MapConfigTO)
@arguments(map_tag=unicode, data=MapConfigTO)
def rest_put_map_settings(map_tag, data):
    app_id = _check_permissions()
    is_shop_user = get_current_session().shop
    return MapConfigTO.from_model(save_map_settings(app_id, map_tag, data, is_shop_user))


def _check_permissions():
    service_user = users.get_current_user()
    community = get_community(get_service_profile(service_user).community_id)
    validate_app_admin(service_user, [community.default_app])
    return community.default_app
