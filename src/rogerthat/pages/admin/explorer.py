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

import os

from rogerthat.consts import DEBUG
from rogerthat.rpc import users
from rogerthat.rpc.users import create_logout_url
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template


class ExplorerPage(webapp.RequestHandler):

    def get(self):
        user = users.get_current_user()
        path = os.path.join(os.path.dirname(__file__), 'explorer.html')
        self.response.out.write(template.render(path, {
            'debug':DEBUG,
            'user':user,
            'session':create_logout_url("/")}))
