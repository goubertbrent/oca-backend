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

import logging

from google.appengine.ext import ndb, db, deferred
from types import NoneType

from mcfw.cache import cached
from mcfw.rpc import arguments, returns
from rogerthat.bizz.job import run_job
from rogerthat.bizz.system import update_look_and_feel_response
from rogerthat.capi.system import updateLookAndFeel
from rogerthat.consts import DEBUG
from rogerthat.dal.profile import get_user_profile
from rogerthat.exceptions.look_and_feel import LookAndFeelNotFoundException
from rogerthat.models import UserProfile
from rogerthat.models.apps import AppLookAndFeel
from rogerthat.rpc.rpc import logError
from rogerthat.to.app import AppLookAndFeelTO, UpdateLookAndFeelRequestTO, LookAndFeelTO
from rogerthat.to.messaging import BaseMemberTO
from rogerthat.utils.app import create_app_user_by_email


@ndb.non_transactional()
@cached(1, lifetime=0, datastore='get_look_and_feel_by_app_id')
@returns([AppLookAndFeel])
@arguments(app_id=unicode)
def get_look_and_feel_by_app_id(app_id):
    return AppLookAndFeel.get_by_app_id(app_id).fetch()


@returns((AppLookAndFeel, NoneType))
@arguments(user_profile=UserProfile, ignore_role=(int, long))
def get_look_and_feel_for_user(user_profile, ignore_role=None):
    """
    Args:
        user_profile (UserProfile)
        ignore_role (long): used when removing this role, so this role isn't used for getting the new look and feel
         after removing the role
    Returns (AppLookAndFeel)
    """
    look_and_feels = get_look_and_feel_by_app_id(user_profile.app_id)

    for service, roles in user_profile.grants.iteritems():
        for role in roles:
            try:
                role_id = int(role)
                for look_and_feel in look_and_feels:  # type: AppLookAndFeel
                    for role_mapping in look_and_feel.roles:  # type: LookAndFeelServiceRoles
                        if role_id in role_mapping.role_ids \
                                and (not ignore_role or role_id != ignore_role) \
                                and role_mapping.service_email == service:
                            return look_and_feel
            except ValueError:
                pass  # Skip build-in roles (see ROLES constant)
    return None


@returns([AppLookAndFeel])
@arguments(app_id=unicode)
def list_app_look_and_feel(app_id):
    return AppLookAndFeel.get_by_app_id(app_id)


@returns(AppLookAndFeel)
@arguments(look_and_feel=AppLookAndFeelTO)
def put_app_look_and_feel(look_and_feel):
    def trans():
        if look_and_feel.id:
            look_and_feel_model = AppLookAndFeel.get_by_id(look_and_feel.id)
            if not look_and_feel_model:
                raise LookAndFeelNotFoundException(look_and_feel.id)

            look_and_feel_model.app_id = look_and_feel.app_id
            look_and_feel_model.colors = look_and_feel.colors.to_model()
            look_and_feel_model.homescreen = look_and_feel.homescreen.to_model()
            look_and_feel_model.toolbar = look_and_feel.toolbar.to_model()
            look_and_feel_model.roles = [role.to_model() for role in look_and_feel.roles]
        else:
            look_and_feel_model = look_and_feel.to_model()
        look_and_feel_model.put()

        send_look_and_feel_updates(look_and_feel_model)
        return look_and_feel_model

    return db.run_in_transaction(trans)


@returns(AppLookAndFeel)
@arguments(look_and_feel=AppLookAndFeelTO, members=[BaseMemberTO])
def test_app_look_and_feel(look_and_feel, members):
    for m in members:
        app_user = create_app_user_by_email(m.member, m.app_id)
        if look_and_feel:
            if DEBUG:
                logging.debug('Updating TEST look and feel for app user %s' % app_user)
            updateLookAndFeel(update_look_and_feel_response, logError, app_user, request=UpdateLookAndFeelRequestTO(look_and_feel))
        else:
            deferred.defer(update_look_and_feel_for_user, app_user, _countdown=1)


@returns()
@arguments(look_and_feel_id=long)
def delete_app_look_and_feel(look_and_feel_id):
    def trans():
        look_and_feel = AppLookAndFeel.get_by_id(look_and_feel_id)
        if not look_and_feel:
            return

        send_look_and_feel_updates(look_and_feel)
        look_and_feel.delete()
    db.run_in_transaction(trans)


def send_look_and_feel_updates(look_and_feel):
    """
    Args:
        look_and_feel (AppLookAndFeel)
    """
    logging.debug("send_look_and_feel_updates for %s", look_and_feel.id)
    service_roles = []
    for role in look_and_feel.roles:  # type: LookAndFeelServiceRoles
        for role_id in role.role_ids:
            service_roles.append(u'%s:%s' % (role.service_email, role_id))
    run_job(_get_app_users, [look_and_feel.app_id, service_roles], update_look_and_feel_for_user_profile, [])


def _get_app_users(app_id, service_roles):
    return UserProfile.list_by_roles(app_id, service_roles)


def update_look_and_feel_for_user(app_user):
    up = get_user_profile(app_user)
    update_look_and_feel_for_user_profile(up)


def update_look_and_feel_for_user_profile(user_profile):
    """
    Args:
        user_profile (UserProfile)
    """
    new_look_and_feel = get_look_and_feel_for_user(user_profile)
    new_look_and_feel_id = new_look_and_feel.id if new_look_and_feel else None
    if new_look_and_feel_id != user_profile.look_and_feel_id:
        user_profile.look_and_feel_id = new_look_and_feel_id
        user_profile.put()
    send_look_and_feel_update(user_profile.user, new_look_and_feel)


def send_look_and_feel_update(app_user, look_and_feel):
    if DEBUG:
        logging.debug('Updating look and feel for app user %s' % app_user)

    look_and_feel_to = LookAndFeelTO.from_model(look_and_feel) if look_and_feel else None
    updateLookAndFeel(update_look_and_feel_response, logError, app_user,
                      request=UpdateLookAndFeelRequestTO(look_and_feel_to))
