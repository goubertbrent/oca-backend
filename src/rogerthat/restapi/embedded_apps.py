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

from mcfw.consts import REST_TYPE_TO
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.bizz.embedded_applications import get_embedded_application, delete_embedded_application, \
    get_embedded_applications, create_embedded_application, update_embedded_application
from rogerthat.to.app import CreateEmbeddedApplicationTO, UpdateEmbeddedApplicationTO


@rest('/console-api/embedded-apps', 'get')
@returns([dict])
@arguments(tag=unicode)
def api_get_embedded_applications(tag=None):
    return [a.to_dict() for a in get_embedded_applications(tag)]


@rest('/console-api/embedded-apps', 'post', type=REST_TYPE_TO, silent=True)
@returns(dict)
@arguments(data=CreateEmbeddedApplicationTO)
def api_create_embedded_application(data):
    return create_embedded_application(data).to_dict()


@rest('/console-api/embedded-apps/<name:[^/]+>', 'get')
@returns(dict)
@arguments(name=unicode)
def api_get_embedded_application(name):
    return get_embedded_application(name).to_dict()


@rest('/console-api/embedded-apps/<name:[^/]+>', 'put', type=REST_TYPE_TO, silent=True)
@returns(dict)
@arguments(name=unicode, data=UpdateEmbeddedApplicationTO)
def api_update_embedded_application(name, data):
    return update_embedded_application(name, data).to_dict()


@rest('/console-api/embedded-apps/<name:[^/]+>', 'delete')
@returns()
@arguments(name=unicode)
def api_delete_embedded_application(name):
    delete_embedded_application(name)
