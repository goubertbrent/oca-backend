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
from rogerthat.rpc import users
from solutions.common.bizz.reports import list_incidents, get_incident, update_incident


@rest('/common/reports/incidents', 'get', read_only_access=True, silent_result=True)
@returns(dict)
@arguments(status=unicode, cursor=unicode)
def rest_list_incidents(status=None, cursor=None):
    params = {'status': status}
    if cursor:
        params['cursor'] = cursor
    return list_incidents(users.get_current_user(), params)


@rest('/common/reports/incidents/<incident_id:[^/]+>', 'get', read_only_access=True, silent_result=True)
@returns(dict)
@arguments(incident_id=unicode)
def rest_get_incident(incident_id):
    return get_incident(users.get_current_user(), incident_id)


@rest('/common/reports/incidents/<incident_id:[^/]+>', 'put', read_only_access=True, silent_result=True)
@returns(dict)
@arguments(incident_id=unicode, data=dict)
def rest_update_incident(incident_id, data):
    return update_incident(users.get_current_user(), incident_id, data)
