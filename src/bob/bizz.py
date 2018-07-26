# -*- coding: utf-8 -*-
# Copyright 2018 Mobicage NV
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
# @@license_version:1.3@@

from google.appengine.ext import db

from mcfw.rpc import arguments
from rogerthat.bizz.app import AppDoesNotExistException
from rogerthat.dal.app import get_app_by_id


@arguments(app_id=unicode, ios_app_id=unicode)
def set_ios_app_id(app_id, ios_app_id):
    def trans():
        app = get_app_by_id(app_id)
        if not app:
            raise AppDoesNotExistException(app_id)
        app.ios_app_id = ios_app_id
        app.put()

    db.run_in_transaction(trans)
