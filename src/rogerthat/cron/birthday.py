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

import logging
from collections import defaultdict

import webapp2
from google.appengine.ext.deferred import deferred

from rogerthat.bizz.messaging import sendMessage
from rogerthat.consts import MC_DASHBOARD
from rogerthat.models import UserProfile, AppSettings, Message, Branding
from rogerthat.models.apps import DefaultBranding
from rogerthat.rpc.service import BusinessException
from rogerthat.to.messaging import UserMemberTO
from rogerthat.utils import now


class BirthdayMessagesCronHandler(webapp2.RequestHandler):
    def get(self):
        deferred.defer(send_birthday_messages)


def get_all_app_birthday_messages():
    messages = {}
    brandings = {}
    brandings_to_get = []  # type: list of unicode
    default_birthday_branding = DefaultBranding.default_key(DefaultBranding.TYPE_BIRTHDAY_MESSAGE).get()
    for birthday_branding in DefaultBranding.list_by_type(DefaultBranding.TYPE_BIRTHDAY_MESSAGE):
        for app_id in birthday_branding.app_ids:
            brandings[app_id] = birthday_branding.branding
    for app_settings in AppSettings.list_with_birthday_message():  # type: AppSettings
        if not app_settings.birthday_message:
            continue
        if app_settings.app_id not in brandings:
            if not default_birthday_branding:
                logging.error(
                    'No default birthday branding has been set. Skipping sending out birthday messages for %s',
                    app_settings.app_id)
                continue
            logging.info('Using default birthday branding for %s', app_settings.app_id)
            messages[app_settings.app_id] = (app_settings.birthday_message, default_birthday_branding.branding)
        else:
            brandings_to_get.append(brandings[app_settings.app_id])
            messages[app_settings.app_id] = (app_settings.birthday_message, brandings[app_settings.app_id])
    for app_id, branding in zip(messages, Branding.get_by_key_name(brandings_to_get)):
        if not branding:
            raise BusinessException('Birthday branding not found for app %s' % app_id)
    return messages


def send_birthday_messages():
    messages_per_app = get_all_app_birthday_messages()
    receivers_per_app = defaultdict(list)
    for user_profile in UserProfile.list_by_birth_day(now()):
        assert (isinstance(user_profile, UserProfile))
        if user_profile.app_id not in messages_per_app:  # this will be faster than doing multiple queries on app ids
            continue
        receivers_per_app[user_profile.app_id].append(UserMemberTO(user_profile.user, Message.ALERT_FLAG_VIBRATE))
    for app_id, receivers in receivers_per_app.iteritems():
        message, branding_hash = messages_per_app[app_id]
        deferred.defer(sendMessage, MC_DASHBOARD, receivers, Message.FLAG_ALLOW_DISMISS, 0, None, message, [], None,
                       branding_hash, None, is_mfr=False)
