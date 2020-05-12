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

# Do not touch the indentation here

from rogerthat.rpc.service import register_service_api_calls
from rogerthat.service.api import app, friends, messaging, qr, system, news, payments
from solutions.common.restapi import yourservicehere


def register_all_service_api_calls():
    register_service_api_calls(yourservicehere)
    register_service_api_calls(app)
    register_service_api_calls(friends)
    register_service_api_calls(messaging)
    register_service_api_calls(qr)
    register_service_api_calls(system)
    register_service_api_calls(news)
    register_service_api_calls(payments)
