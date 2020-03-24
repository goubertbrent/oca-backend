# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
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

from mcfw.consts import REST_TYPE_TO
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.rpc import users
from solutions.common.bizz.settings import get_service_info, update_service_info
from solutions.common.to.settings import ServiceInfoTO


@rest('/common/service-info', 'get', read_only_access=True, silent=True)
@returns(ServiceInfoTO)
@arguments()
def rest_get_service_info():
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    return ServiceInfoTO.from_model(get_service_info(users.get_current_user(), service_identity))


@rest('/common/service-info', 'put', type=REST_TYPE_TO, silent=True, silent_result=True)
@returns(ServiceInfoTO)
@arguments(data=ServiceInfoTO)
def rest_save_service_info(data):
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    return ServiceInfoTO.from_model(update_service_info(users.get_current_user(), service_identity, data))
