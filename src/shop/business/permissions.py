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

from google.appengine.api import users as gusers

from mcfw.rpc import returns, arguments
from rogerthat.rpc import users
from solution_server_settings import get_solution_server_settings


@returns(bool)
@arguments(user=users.User)
def is_admin(user):
    solutions_server_settings = get_solution_server_settings()
    return user in [gusers.User(email) for email in solutions_server_settings.shop_bizz_admin_emails]
