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

from google.appengine.ext import db

from mcfw.properties import azzert
from mcfw.rpc import returns, arguments
from rogerthat.bizz.friends import create_add_to_services_button, ORIGIN_SERVICE_INVITE
from rogerthat.bizz.job import run_job
from rogerthat.bizz.service import fake_friend_connection
from rogerthat.bizz.messaging import sendMessage
from rogerthat.consts import MC_RESERVED_TAG_PREFIX
from rogerthat.dal.friend import get_friends_map_key_by_user
from rogerthat.dal.profile import get_profile_key
from rogerthat.dal.service import get_service_identity
from rogerthat.models import UserProfile, FriendServiceIdentityConnection, ServiceIdentity, Message
from rogerthat.rpc import users
from rogerthat.to.messaging import UserMemberTO
from rogerthat.utils import bizz_check
from rogerthat.utils.app import create_app_user_by_email
from rogerthat.utils.service import get_service_user_from_service_identity_user
from rogerthat.utils.transactions import run_in_transaction

APP_BROADCAST_TAG = u"%s.app_broadcast" % MC_RESERVED_TAG_PREFIX


def _validate_app_broadcast(service_identity_user, app_ids, message):
    si = get_service_identity(service_identity_user)
    azzert(si)
    for app_id in app_ids:
        azzert(app_id in si.appIds)

    bizz_check(message and message.strip(), 'Message should not be empty')
    return si


def _get_tag(identifier):
    return u'%s %s' % (APP_BROADCAST_TAG, identifier)


@returns(unicode)
@arguments(service_identity_user=users.User, app_ids=[unicode], message=unicode, identifier=unicode)
def send_app_broadcast(service_identity_user, app_ids, message, identifier):
    si = _validate_app_broadcast(service_identity_user, app_ids, message)
    tag = _get_tag(identifier)
    for app_id in app_ids:
        run_job(_get_app_users, [app_id],
                _send_app_broadcast_to_user, [si.user, message, tag])
    return tag


@returns(unicode)
@arguments(service_identity_user=users.User, app_ids=[unicode], message=unicode, identifier=unicode, tester=unicode)
def test_send_app_broadcast(service_identity_user, app_ids, message, identifier, tester):
    si = _validate_app_broadcast(service_identity_user, app_ids, message)
    tag = _get_tag(identifier)
    app_users = []
    user_profile_keys = []
    for app_id in app_ids:
        app_user = create_app_user_by_email(tester, app_id)
        user_profile_key = get_profile_key(app_user)
        app_users.append(app_user)
        user_profile_keys.append(user_profile_key)
    user_profiles = db.get(user_profile_keys)
    for user_profile, app_user in zip(user_profiles, app_users):
        bizz_check(user_profile and isinstance(user_profile, UserProfile), 'User %s not found' % app_user.email())

    for user_profile in user_profiles:
        _send_app_broadcast_to_user(user_profile, si.user, message, tag, is_test=True)
    return tag


def _get_app_users(app_id):
    return UserProfile.all().filter('app_id', app_id)


@returns()
@arguments(user_profile=UserProfile, service_identity_user=users.User, message=unicode, tag=unicode, is_test=bool)
def _send_app_broadcast_to_user(user_profile, service_identity_user, message, tag, is_test=False):
    app_user = users.User(user_profile.key().name())
    if user_profile.isCreatedForService:
        logging.debug('%s is created for service(s) %s', app_user, user_profile.owningServiceEmails)
        return

    service_user = get_service_user_from_service_identity_user(service_identity_user)
    fsic_key = FriendServiceIdentityConnection.createKey(app_user, service_identity_user)
    friend_map_key = get_friends_map_key_by_user(app_user)

    fsic, friend_map, si, service_profile = \
        db.get([fsic_key,
                friend_map_key,
                ServiceIdentity.keyFromUser(service_identity_user),
                get_profile_key(service_user)])

    azzert(si and service_profile)

    if fsic and not fsic.deleted:
        # they are friends
        alert_flags = Message.ALERT_FLAG_VIBRATE
        answers = []
        step_id = u'Connected'
    elif friend_map:
        # Fake a deleted connection between service and human user to be able to show the service's avatar on the phone
        fake_friend_connection(friend_map_key, si)

        alert_flags = Message.ALERT_FLAG_SILENT
        answers = create_add_to_services_button(service_profile.defaultLanguage)
        step_id = u'Not connected'
    else:
        logging.warn(u'No FSIC nor FriendMap found for %s', app_user)
        return

    member = UserMemberTO(app_user, alert_flags)
    flags = Message.FLAG_ALLOW_DISMISS | Message.FLAG_AUTO_LOCK
    timeout = 0
    parent_key = None
    sender_answer = None
    branding = si.descriptionBranding

    if is_test:
        step_id = None

    m = sendMessage(service_identity_user, [member], flags, timeout, parent_key, message, answers, sender_answer,
                    branding, tag, check_friends=False, allow_reserved_tag=True, step_id=step_id)
    m.invitor = service_identity_user
    m.invitee = app_user
    m.origin = ORIGIN_SERVICE_INVITE
    m.servicetag = APP_BROADCAST_TAG
    m.put()
