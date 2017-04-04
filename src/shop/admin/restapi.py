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

from rogerthat.models import RogerthatBackendErrors
from rogerthat.rpc import users
from rogerthat.to import ReturnStatusTO, RETURNSTATUS_TO_SUCCESS
from rogerthat.utils.channel import send_message
from google.appengine.ext import db
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from shop.admin.bizz import analyze_status
from shop.admin.dal import get_monitored_services_in_trouble_qry
from shop.admin.to import MonitoringStatusTO
from rogerthat.settings import get_server_settings


@rest("/admin/rest/monitoring/get_status", "get", silent_result=True)
@returns(MonitoringStatusTO)
@arguments()
def get_status():
    return MonitoringStatusTO.create(analyze_status())


@rest("/admin/rest/monitoring/reset", "get")
@returns(ReturnStatusTO)
@arguments()
def reset():
    db.delete(RogerthatBackendErrors.get_key())
    db.delete(list(get_monitored_services_in_trouble_qry()))
    server_settings = get_server_settings()
    send_to = server_settings.supportWorkers
    send_to.append(server_settings.dashboardEmail)
    send_message(map(users.User, send_to), 'shop.monitoring.reset', skip_dashboard_user=False)
    return RETURNSTATUS_TO_SUCCESS
