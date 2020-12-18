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

import base64
import json
import logging
import os

import jinja2
from google.appengine.ext import webapp, db
from google.appengine.ext.webapp import template

from mcfw.properties import azzert
from rogerthat.bizz.user import calculate_secure_url_digest
from rogerthat.dal.app import get_app_by_user
from rogerthat.dal.mobile import get_user_active_mobiles
from rogerthat.models import ActivationLog, App, UserProfile
from rogerthat.rpc import users
from rogerthat.rpc.models import Mobile
from rogerthat.templates.jinja_extensions import TranslateExtension
from rogerthat.utils import now
from rogerthat.utils.app import get_human_user_from_app_user, get_app_id_from_app_user
from rogerthat.utils.crypto import decrypt


class UnsubscribeReminderHandler(webapp.RequestHandler):
    _BASE_DIR = None
    _JINJA_ENVIRONMENT = None

    @staticmethod
    def get_base_dir():
        if not UnsubscribeReminderHandler._BASE_DIR:
            UnsubscribeReminderHandler._BASE_DIR = os.path.dirname(__file__)
        return UnsubscribeReminderHandler._BASE_DIR

    @staticmethod
    def get_jinja_environment():
        if not UnsubscribeReminderHandler._JINJA_ENVIRONMENT:
            UnsubscribeReminderHandler._JINJA_ENVIRONMENT = \
                jinja2.Environment(loader=jinja2.FileSystemLoader([UnsubscribeReminderHandler.get_base_dir()]),
                                   extensions=[TranslateExtension])
        return UnsubscribeReminderHandler._JINJA_ENVIRONMENT

    def return_error(self, reason="Invalid url received."):
        path = os.path.join(self.get_base_dir(), 'error.html')
        self.response.out.write(template.render(path, {"reason": reason, "hide_header": True}))
        return None, None

    def parse_data(self, email, data):
        user = users.User(email)
        data = base64.decodestring(data)
        data = decrypt(user, data)
        data = json.loads(data)
        azzert(data["d"] == calculate_secure_url_digest(data))
        return data, user

    def get_user_info(self):
        email = self.request.get("email", None)
        data = self.request.get("data", None)

        if not email or not data:
            return self.return_error()

        try:
            data_dict, _ = self.parse_data(email, data)
        except:
            logging.warn("Could not decipher url!", exc_info=True)
            return self.return_error()

        app_user = users.User(email)
        return data_dict, app_user

    def get(self):
        data_dict, app_user = self.get_user_info()
        if not data_dict or not app_user:
            return

        app, user_profile = db.get([App.create_key(get_app_id_from_app_user(app_user)),
                                    UserProfile.createKey(app_user)])

        if not user_profile:
            self.redirect("/")
            return

        mobiles = list(get_user_active_mobiles(app_user))
        if mobiles:
            mobile = mobiles[0]
            if mobile.type in Mobile.ANDROID_TYPES:
                page_type = "android"
            elif mobile.type in Mobile.IOS_TYPES:
                page_type = "ios"
            else:
                return self.return_error()
        else:
            mobile = None
            page_type = "web"

        page_type = self.request.get("page_type", page_type)
        language = self.request.get("language", user_profile.language)

        ActivationLog(timestamp=now(), email=app_user.email(), mobile=mobile,
                      description="Visit unsubscribe page %s %s" % (page_type, user_profile.language)).put()

        jinja_template = self.get_jinja_environment().get_template('unsubscribe_reminder_service.html')

        params = {
            'name': data_dict['n'],
            'app_name': get_app_by_user(app_user).name,
            'hide_header': True,
            'data': self.request.get("data"),
            'app_email': app_user.email(),
            'email': get_human_user_from_app_user(app_user).email(),
            'action': data_dict['a'],
            'page_type': page_type,
            'language': language,
            'is_city_app': app.type == App.APP_TYPE_CITY_APP
        }

        self.response.out.write(jinja_template.render(params))


class UnsubscribeDeactivateHandler(UnsubscribeReminderHandler):

    def get(self):
        data_dict, app_user = self.get_user_info()
        if not data_dict or not app_user:
            return

        azzert(data_dict['a'] == "unsubscribe deactivate")

        app, user_profile = db.get([App.create_key(get_app_id_from_app_user(app_user)),
                                    UserProfile.createKey(app_user)])

        if not user_profile:
            self.redirect("/")
            return

        mobiles = list(get_user_active_mobiles(app_user))
        if mobiles:
            mobile = mobiles[0]
            if mobile.type in Mobile.ANDROID_TYPES:
                page_type = "android"
            elif mobile.type in Mobile.IOS_TYPES:
                page_type = "ios"
            else:
                return self.return_error()
        else:
            mobile = None
            page_type = "web"

        page_type = self.request.get("page_type", page_type)
        language = self.request.get("language", user_profile.language)

        ActivationLog(timestamp=now(), email=app_user.email(), mobile=mobile,
                      description="Visit unsubscribe page %s %s" % (page_type, user_profile.language)).put()

        jinja_template = self.get_jinja_environment().get_template('unsubscribe_deactivate.html')

        params = {
            'name': data_dict['n'],
            'app_name': get_app_by_user(app_user).name,
            'hide_header': True,
            'data': self.request.get("data"),
            'app_email': app_user.email(),
            'email': get_human_user_from_app_user(app_user).email(),
            'action': data_dict['a'],
            'page_type': page_type,
            'language': language,
            'is_city_app': app.type == App.APP_TYPE_CITY_APP
        }

        self.response.out.write(jinja_template.render(params))
