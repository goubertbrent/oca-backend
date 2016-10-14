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
import json

from mcfw.restapi import rest
from mcfw.rpc import arguments, returns
from rogerthat.rpc import users
from rogerthat.to.statistics import AppServiceStatisticsTO
from solutions.common.bizz.statistics import get_app_statistics


@rest('/common/statistics/apps', 'get', read_only_access=True)
@returns([AppServiceStatisticsTO])
@arguments()
def rest_get_app_statistics():
    service_identity = users.get_current_session().service_identity
    return get_app_statistics(service_identity)

