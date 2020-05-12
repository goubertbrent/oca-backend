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

from mcfw.rpc import returns, arguments
from rogerthat.rpc import users
from rogerthat.service.api import app
from rogerthat.to.statistics import AppServiceStatisticsTO
from shop.dal import get_customer
from solutions.common.bizz.cityapp import get_country_apps


@returns([AppServiceStatisticsTO])
@arguments(service_user=users.User, service_identity=unicode)
def get_app_statistics(service_user, service_identity=None):
    customer = get_customer(service_user)
    if customer:
        available_apps = get_country_apps(customer.country).values()
    else:
        return []
    return app.get_statistics(available_apps, service_identity)
