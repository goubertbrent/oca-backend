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

from rogerthat.models import ServiceIdentity
from rogerthat.rpc import users
from rogerthat.service.api import app

from mcfw.consts import MISSING
from mcfw.rpc import returns, arguments
from rogerthat.bizz.app import get_app
from rogerthat.dal.service import get_service_identity
from rogerthat.to.statistics import AppServiceStatisticsTO
from rogerthat.utils.service import create_service_identity_user
from shop.dal import get_customer, get_available_apps_for_customer
from solutions.common.bizz.cityapp import get_country_apps


@returns([AppServiceStatisticsTO])
@arguments(service_user=users.User, service_identity=unicode, all_apps=bool)
def get_app_statistics(service_user, service_identity=None, all_apps=True):
    customer = get_customer(service_user)
    if all_apps:
        available_apps = get_country_apps(customer.country).values()
    else:
        if not service_identity or service_identity == MISSING:
            service_identity = ServiceIdentity.DEFAULT
        service_identity_user = create_service_identity_user(service_user, service_identity)
        si = get_service_identity(service_identity_user)
        default_app = get_app(si.defaultAppId)

        available_apps = [a.app_id for a in get_available_apps_for_customer(customer, default_app.demo)]
        if not available_apps:
            # Customer does not exist or has no app ids
            available_apps = sorted(si.appIds)

    return app.get_statistics(available_apps, service_identity)
