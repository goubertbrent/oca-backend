# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
# NOTICE: THIS FILE HAS BEEN MODIFIED BY GREEN VALLEY BELGIUM NV IN ACCORDANCE WITH THE APACHE LICENSE VERSION 2.0
# Copyright 2018 GIG Technology NV
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
# @@license_version:1.6@@

import os

from rogerthat.consts import DEBUG
from rogerthat.models import DoNotSendMeMoreInvites
from rogerthat.rpc import users
from rogerthat.rpc.users import create_logout_url
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template


class UnsubscribeHandler(webapp.RequestHandler):
    
    def get(self):
        user = users.get_current_user()
        DoNotSendMeMoreInvites.get_or_insert(key_name=user.email())
        path = os.path.join(os.path.dirname(__file__), 'unsubscribe.html')
        self.response.out.write(template.render(path, {
            'debug':DEBUG,                                           
            'user':user,
            'session':create_logout_url("/")}))
