# -*- coding: utf-8 -*-
# Copyright 2017 Mobicage NV
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
# @@license_version:1.2@@

from mcfw.restapi import GenericRESTRequestHandler, rest, REST_FLAVOR_NORMAL
from mcfw.rpc import arguments, returns
from createsend.utils import json_to_py

from solutions.common.bizz.campaignmonitor import LIST_CALLBACK_PATH
from solutions.common.bizz.service import new_list_event


@rest(LIST_CALLBACK_PATH, "post", read_only_access=True, authenticated=False, flavor=REST_FLAVOR_NORMAL)
@returns()
@arguments()
def api_list_webhook_callback():
    """A generic handler for campaignmonitor subscriber list web hooks"""
    # FIXME: how to verify this callback is from campaignmonitor?
    list_events = json_to_py(GenericRESTRequestHandler.getCurrentRequest().body)
    new_list_event(list_events.ListID, list_events.Events)
