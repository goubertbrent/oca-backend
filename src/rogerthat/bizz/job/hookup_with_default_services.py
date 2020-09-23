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

from google.appengine.ext import deferred, db, ndb
from typing import Union, Optional, List

from rogerthat.bizz.communities.models import CommunityAutoConnectedService
from rogerthat.bizz.friend_helper import FriendCloudStorageHelper
from rogerthat.bizz.friends import makeFriends, ORIGIN_USER_INVITE
from rogerthat.consts import HIGH_LOAD_WORKER_QUEUE
from rogerthat.dal import parent_key
from rogerthat.dal.profile import get_user_profile
from rogerthat.models import UserInteraction
from rogerthat.rpc import users
from rogerthat.utils.service import add_slash_default
from rogerthat.utils.transactions import run_in_transaction


def schedule(app_user):
    # type: (users.User) -> None
    deferred.defer(run, app_user, _transactional=db.is_in_transaction(), _countdown=2)


def get_user_interaction(app_user):
    # type: (users.User) -> UserInteraction
    return UserInteraction.get_by_key_name(app_user.email(), parent=parent_key(app_user)) \
        or UserInteraction(key_name=app_user.email(), parent=parent_key(app_user))


def run(app_user):
    # type: (users.User) -> None
    from rogerthat.bizz.communities.communities import get_community
    user_profile = get_user_profile(app_user)
    community = get_community(user_profile.community_id)
    logging.debug('Default services for the \'%s\' community are: %s', community.name,
                  community.auto_connected_service_emails)
    run_for_auto_connected_service(app_user, community.auto_connected_services, None)


def run_for_auto_connected_service(app_user_or_key, new_acs, service_helper):
    # type: (Union[users.User, ndb.Key], List[CommunityAutoConnectedService], Optional[FriendCloudStorageHelper]) -> None
    app_user = app_user_or_key if isinstance(app_user_or_key, users.User) else users.User(app_user_or_key.id())

    def trans():
        to_add = []
        user_profile = get_user_profile(app_user)
        if user_profile.isCreatedForService:
            return to_add

        ui = get_user_interaction(app_user)
        for acs in new_acs:
            if acs.service_identity_email not in ui.services:
                service_identity_user = users.User(acs.service_identity_email)
                ui.services.append(acs.service_identity_email)
                to_add.append(add_slash_default(service_identity_user))
        ui.put()
        return to_add

    services_to_add = run_in_transaction(trans, xg=True)
    for service in services_to_add:
        logging.info('Connecting %s with auto-connected service %s', app_user, service)
        deferred.defer(makeFriends, service, app_user, app_user, None,
                       notify_invitee=False, origin=ORIGIN_USER_INVITE, service_helper=service_helper,
                       skip_callbacks=True, _queue=HIGH_LOAD_WORKER_QUEUE)
