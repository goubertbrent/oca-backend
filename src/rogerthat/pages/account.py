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
import logging

from google.appengine.ext import deferred

from rogerthat.bizz.registration import get_headers_for_consent
from rogerthat.bizz.system import mark_mobile_for_delete
from rogerthat.bizz.user import delete_account
from rogerthat.bizz.user.export import export_user_data
from rogerthat.dal.profile import get_user_profile
from rogerthat.models import UserConsentHistory
from rogerthat.pages import UserAwareRequestHandler
from rogerthat.pages.legal import get_current_document_version, DOC_TERMS
from rogerthat.rpc import users
from rogerthat.translations import localize


class AccountLogoutHandler(UserAwareRequestHandler):

    def post(self):
        logging.debug(self.request.POST)
        if not self.set_user():
            self.abort(401)
            return

        mobile = users.get_current_mobile()
        user_profile = get_user_profile(mobile.user)

        deferred.defer(mark_mobile_for_delete, mobile.user, mobile.key())

        reason = localize(user_profile.language, "You have been logged out on your request")
        self.response.headers['Content-Type'] = "application/json"
        self.response.out.write(json.dumps(dict(reason=reason)))


class AccountDeleteHandler(UserAwareRequestHandler):

    def post(self):
        logging.debug(self.request.POST)
        if not self.set_user():
            self.abort(401)
            return

        app_user = users.get_current_user()
        user_profile = get_user_profile(app_user)

        deferred.defer(delete_account, app_user)

        reason = localize(user_profile.language, "Your account has been deleted on your request")
        self.response.headers['Content-Type'] = "application/json"
        self.response.out.write(json.dumps(dict(reason=reason)))


class AccountDataDownloadHandler(UserAwareRequestHandler):

    def post(self):
        logging.debug(self.request.POST)
        if not self.set_user():
            self.abort(401)
            return

        data_export_email = self.request.get("data_export_email", None)

        app_user = users.get_current_user()
        user_profile = get_user_profile(app_user)
        current_data_export_email = export_user_data(app_user, data_export_email)
        if current_data_export_email:
            message = localize(user_profile.language, "user_data_download_duplicate", email=current_data_export_email)
        else:
            message = localize(user_profile.language, "user_data_download_started")

        self.response.headers['Content-Type'] = "application/json"
        self.response.out.write(json.dumps(dict(message=message)))


class AccountConsentHandler(UserAwareRequestHandler):

    def post(self):
        logging.debug(self.request.POST)
        if not self.set_user():
            self.abort(401)
            return

        consent_type = self.request.get("consent_type", None)
        if not consent_type:
            age = self.request.get("age", None)  # We forgot to add consent_type on ios for tos
            if age:
                consent_type = UserConsentHistory.TYPE_TOS
            else:
                self.abort(401)
                return

        app_user = users.get_current_user()
        user_profile = get_user_profile(app_user)

        if consent_type == UserConsentHistory.TYPE_TOS:
            from rogerthat.bizz.registration import save_tos_consent
            version = get_current_document_version(DOC_TERMS)
            age = self.request.get("age", None)
            if not age:
                self.abort(401)
                return
            user_profile.tos_version = version
            user_profile.put()
            deferred.defer(save_tos_consent, app_user, get_headers_for_consent(self.request), version, age)

        elif consent_type == UserConsentHistory.TYPE_PUSH_NOTIFICATIONS:
            from rogerthat.bizz.registration import save_push_notifications_consent
            enabled = self.request.get("enabled", None)
            if not enabled:
                self.abort(401)
                return
            user_profile.consent_push_notifications_shown = True
            user_profile.put()

            deferred.defer(save_push_notifications_consent, app_user, get_headers_for_consent(self.request), enabled)

        else:
            self.abort(401)
            return

        self.response.headers['Content-Type'] = "application/json"
        self.response.out.write(json.dumps(dict()))
