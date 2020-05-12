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

from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.dal.mobile import get_user_active_mobiles
from rogerthat.rpc import users
from rogerthat.to.system import WebMobileTO


@rest("/mobi/rest/devices/mobiles/active", "get")
@returns([WebMobileTO])
@arguments()
def get_active_mobiles():
    user = users.get_current_user()
    return (WebMobileTO.from_model(m) for m in get_user_active_mobiles(user))
