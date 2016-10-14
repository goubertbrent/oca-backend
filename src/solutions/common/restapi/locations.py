# -*- coding: utf-8 -*-
# Copyright 2016 Mobicage NV
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
# @@license_version:1.1@@

from rogerthat.bizz.session import set_service_identity
from rogerthat.models import ServiceIdentity
from rogerthat.rpc import users
from rogerthat.utils.channel import send_message_to_session
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from solutions.common.dal import get_solution_settings, get_solution_identity_settings
from solutions.common.to.locations import LocationTO


@rest("/common/locations/load", "get", read_only_access=True)
@returns([LocationTO])
@arguments()
def locations_load():
    service_user = users.get_current_user()
    sln_settings = get_solution_settings(service_user)
    if sln_settings.identities:
        locations = []
        locations.append(LocationTO.create(ServiceIdentity.DEFAULT, sln_settings))
        for service_identity in sln_settings.identities:
            sln_i_settings = get_solution_identity_settings(service_user, service_identity)
            locations.append(LocationTO.create(service_identity, sln_i_settings))
        return locations
    return []


@rest("/common/locations/use", "post", read_only_access=True)
@returns()
@arguments(service_identity=unicode)
def locations_use(service_identity):
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    sln_settings = get_solution_settings(service_user)
    new_service_identity = ServiceIdentity.DEFAULT
    if sln_settings.identities:
        if service_identity in sln_settings.identities:
            new_service_identity = service_identity

    if session_.service_identity != new_service_identity:
        session_ = set_service_identity(session_, new_service_identity)

    send_message_to_session(service_user, session_, u"solutions.common.locations.update", si=new_service_identity)
