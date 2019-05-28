# -*- coding: utf-8 -*-
# Copyright 2019 Mobicage NV
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
# @@license_version:1.4@@
from mcfw.consts import REST_TYPE_TO
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.rpc import users
from solutions.common.bizz.participation.proxy import list_projects, get_project, update_project, get_settings, \
    update_settings, get_project_statistics, create_project


@rest('/common/participation/projects', 'get', read_only_access=True, silent_result=True)
@returns([dict])
@arguments()
def rest_list_projects():
    return list_projects(users.get_current_user())


@rest('/common/participation/projects', 'post', read_only_access=True, silent_result=True, type=REST_TYPE_TO)
@returns(dict)
@arguments(data=dict)
def rest_create_project(data):
    return create_project(users.get_current_user(), data)


@rest('/common/participation/projects/<project_id:[^/]+>', 'get', read_only_access=True, silent_result=True)
@returns(dict)
@arguments(project_id=(int, long))
def rest_get_project(project_id):
    return get_project(users.get_current_user(), project_id)


@rest('/common/participation/projects/<project_id:[^/]+>', 'put', silent_result=True, type=REST_TYPE_TO)
@returns(dict)
@arguments(project_id=(int, long), data=dict)
def rest_update_projects(project_id, data):
    return update_project(users.get_current_user(), project_id, data)


@rest('/common/participation/projects/<project_id:[^/]+>/statistics', 'get', read_only_access=True, silent_result=True)
@returns(dict)
@arguments(project_id=(int, long))
def rest_project_stats(project_id):
    return get_project_statistics(users.get_current_user(), project_id)


@rest('/common/participation/settings', 'get', read_only_access=True, silent_result=True)
@returns(dict)
@arguments()
def rest_get_settings():
    return get_settings(users.get_current_user())


@rest('/common/participation/settings', 'put', silent_result=True, type=REST_TYPE_TO)
@returns(dict)
@arguments(data=dict)
def rest_update_settings(data):
    return update_settings(users.get_current_user(), data)
