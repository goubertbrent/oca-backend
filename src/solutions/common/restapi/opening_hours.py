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
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.models import ServiceIdentity
from rogerthat.rpc import users
from solutions.common.bizz.opening_hours import put_opening_hours, get_opening_hours
from solutions.common.to.opening_hours import OpeningHoursTO


@rest('/common/settings/opening-hours', 'get', silent_result=True)
@returns(OpeningHoursTO)
@arguments()
def rest_get_opening_hours():
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity or ServiceIdentity.DEFAULT
    return OpeningHoursTO.from_model(get_opening_hours(service_user, service_identity))


@rest('/common/settings/opening-hours', 'put', silent_result=True, silent=True)
@returns(OpeningHoursTO)
@arguments(data=OpeningHoursTO)
def rest_put_opening_hours(data):
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity or ServiceIdentity.DEFAULT
    return OpeningHoursTO.from_model(put_opening_hours(service_user, service_identity, data))
