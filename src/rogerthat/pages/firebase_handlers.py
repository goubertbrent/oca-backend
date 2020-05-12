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

import json

from rogerthat.bizz.channel import get_uid
from rogerthat.bizz.channel.firebase import create_custom_token
from rogerthat.pages import UserAwareRequestHandler
from rogerthat.rpc import users
from rogerthat.utils.app import get_human_user_from_app_user


class FirebaseTokenHandler(UserAwareRequestHandler):

    def get(self):
        web_user = users.get_current_user()
        if not web_user and not self.set_user():
            self.abort(401)
            return
        human_user = get_human_user_from_app_user(users.get_current_user())
        user_id = get_uid(human_user.email())
        if web_user:
            token = create_custom_token(user_id, {})
        else:
            token = create_custom_token(user_id, {}, mobile=users.get_current_mobile())
        response = {
            'token': token
        }
        self.response.write(json.dumps(response))
