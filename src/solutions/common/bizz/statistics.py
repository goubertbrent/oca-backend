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
from rogerthat.bizz.service import get_and_validate_service_identity_user
from rogerthat.rpc import users
from rogerthat.service.api import app
from rogerthat.to.statistics import AppServiceStatisticsTO
from shop.dal import get_customer, get_available_apps_for_customer


@returns([AppServiceStatisticsTO])
@arguments(service_identity=unicode)
def get_app_statistics(service_identity):
    service_user = users.get_current_user()
    service_identity_user = get_and_validate_service_identity_user(service_user, service_identity)
    customer = get_customer(service_user)
    app_ids = []
    available_apps = get_available_apps_for_customer(customer)
    for available_app in available_apps:
        app_ids.append(available_app.app_id)
    return app.get_app_statistics(app_ids, service_identity_user)
