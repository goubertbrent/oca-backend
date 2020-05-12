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
from rogerthat.bizz.authentication import Scopes
from rogerthat.bizz.firebase import create_firebase_project, \
    get_firebase_projects
from rogerthat.to import FileTO


@rest('/restapi/firebase-projects', 'get', scopes=Scopes.BACKEND_EDITOR)
@returns([dict])
@arguments()
def api_get_firebase_projects():
    return get_firebase_projects()


@rest('/restapi/firebase-projects', 'put', scopes=Scopes.BACKEND_EDITOR, silent=True)
@returns(dict)
@arguments(data=FileTO)
def api_create_firebase_project(data):
    return create_firebase_project(data.file)
