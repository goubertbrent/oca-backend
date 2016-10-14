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

from rogerthat.models import ServiceIdentity
from rogerthat.rpc import users
from rogerthat.utils.service import create_service_identity_user
from mcfw.rpc import returns, arguments


@returns(bool)
@arguments(service_identity=unicode)
def is_default_service_identity(service_identity):
    if not service_identity:
        return True
    if service_identity == ServiceIdentity.DEFAULT:
        return True
    return False

@returns(users.User)
@arguments(service_user=users.User, service_identity=unicode)
def create_service_identity_user_wo_default(service_user, service_identity):
    if is_default_service_identity(service_identity):
        return service_user
    else:
        return create_service_identity_user(service_user, service_identity)
