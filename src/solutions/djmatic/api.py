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

from mcfw.rpc import returns, arguments
from rogerthat.dal.service import get_api_keys
from rogerthat.rpc import users
from rogerthat.rpc.service import ServiceApiHandler, service_api
from solution_server_settings import get_solution_server_settings
from solutions.common.to import ProvisionResponseTO
from solutions.djmatic.bizz import create_djmatic_service


class DJMaticApiHandler(ServiceApiHandler):
    def post(self):
        secret = self.request.headers.get("X-DJMatic-Secret")
        if not secret:
            self.response.set_status(401, "Missing secret")
            return

        solution_server_settings = get_solution_server_settings()
        if secret != solution_server_settings.djmatic_secret:
            self.response.set_status(401, "Wrong secret")
            return

        for api_key in get_api_keys(users.User(solution_server_settings.djmatic_service_email)):
            self.request.headers["X-Nuntiuz-API-Key"] = api_key.key().name()
            break

        return ServiceApiHandler.post(self)


@service_api(function="djmatic.provision")
@returns(ProvisionResponseTO)
@arguments(email=unicode, name=unicode, branding_url=unicode, menu_item_color=unicode, secret=unicode,
           player_id=unicode, player_type=int)
def djmatic_provision(email, name, branding_url, menu_item_color, secret, player_id, player_type):
    return create_djmatic_service(email, name, branding_url, menu_item_color, secret, player_id, player_type)
