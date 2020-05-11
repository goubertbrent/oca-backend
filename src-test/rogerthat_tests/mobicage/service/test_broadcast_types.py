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

import json

import mc_unittest
from rogerthat.api.friends import breakFriendship, getFriend
from rogerthat.api.services import updateUserData
from rogerthat.bizz.friends import makeFriends
from rogerthat.bizz.profile import create_user_profile
from rogerthat.bizz.service import convert_user_to_service, DISABLED_BROADCAST_TYPES_USER_DATA_KEY
from rogerthat.dal.service import get_friend_serviceidentity_connection, \
    get_friend_service_identity_connections_of_service_identity_query, \
    get_friend_service_identity_connections_of_app_user_query
from rogerthat.rpc import users
from rogerthat.to.friends import BreakFriendshipRequestTO, GetFriendRequestTO, FriendTO
from rogerthat.to.service import UpdateUserDataRequestTO
from rogerthat.utils.service import add_slash_default
from rogerthat_tests import set_current_user


TYPE1 = u'type1'
TYPE2 = u'type2'
TYPE3 = u'type3'


class BroadcastTypesCheck(mc_unittest.TestCase):

    def _setup(self=0):
        self.app_user = users.User(u'app_user@mobicage.com')
        self.service_user = users.User(u'service_user@mobicage.com')
        self.si_user = add_slash_default(self.service_user)

        create_user_profile(self.app_user, self.app_user.email())
        create_user_profile(self.service_user, self.service_user.email())
        self.service_profile = convert_user_to_service(self.service_user)
        self.service_profile.broadcastTypes = [TYPE1, TYPE2, TYPE3]
        self.service_profile.put()

    def _make_friends(self):
        makeFriends(self.app_user, self.service_user, self.service_user, None, None)

    def _break_friendship(self):
        with set_current_user(self.app_user):
            request = BreakFriendshipRequestTO()
            request.friend = self.service_user.email()
            breakFriendship(request)

    def _set_disabled_broadcast_types(self, disabled_broadcast_types):
        with set_current_user(self.app_user):
            user_data = {DISABLED_BROADCAST_TYPES_USER_DATA_KEY: disabled_broadcast_types}
            request = UpdateUserDataRequestTO()
            request.app_data = None
            request.service = self.service_user.email()
            request.user_data = json.dumps(user_data).decode('utf-8')
            updateUserData(request)

    def _get_friend(self):
        with set_current_user(self.app_user):
            request = GetFriendRequestTO()
            request.avatar_size = 50
            request.email = self.service_user.email()
            response = getFriend(request)
            return response

    def _assert_disabled_broadcast_types(self, disabled_broadcast_types):
        fsic = get_friend_serviceidentity_connection(self.app_user, self.si_user)
        self.assertSetEqual(set(disabled_broadcast_types), set(fsic.disabled_broadcast_types))
        enabled_broadcast_types = set(self.service_profile.broadcastTypes) - set(disabled_broadcast_types)
        self.assertSetEqual(enabled_broadcast_types, set(fsic.enabled_broadcast_types))
        return fsic

    def test_deleted_fsics(self):
        self.set_datastore_hr_probability(1)
        self._setup()

        self.assertIsNone(get_friend_serviceidentity_connection(self.app_user, self.si_user))

        self._set_disabled_broadcast_types([TYPE1, TYPE2])
        fsic = self._assert_disabled_broadcast_types([TYPE1, TYPE2])
        self.assertTrue(fsic.deleted)
        self.assertEqual(0, get_friend_service_identity_connections_of_service_identity_query(self.si_user).count())
        self.assertEqual(0, get_friend_service_identity_connections_of_app_user_query(self.app_user).count())

        self._make_friends()
        fsic = self._assert_disabled_broadcast_types([TYPE1, TYPE2])
        self.assertFalse(fsic.deleted)
        self.assertEqual(1, get_friend_service_identity_connections_of_service_identity_query(self.si_user).count())
        self.assertEqual(1, get_friend_service_identity_connections_of_app_user_query(self.app_user).count())

        self._break_friendship()
        fsic = self._assert_disabled_broadcast_types([TYPE1, TYPE2])
        self.assertTrue(fsic.deleted)
        self.assertEqual(0, get_friend_service_identity_connections_of_service_identity_query(self.si_user).count())
        self.assertEqual(0, get_friend_service_identity_connections_of_app_user_query(self.app_user).count())

    def test_disabling_types_of_unconnected_service(self):
        self.set_datastore_hr_probability(1)
        self._setup()

        response = self._get_friend()
        self.assertIsNone(response.friend)

        self._set_disabled_broadcast_types([TYPE1])
        self._assert_disabled_broadcast_types([TYPE1])

        response = self._get_friend()
        self.assertEqual(FriendTO.FRIEND_EXISTENCE_DELETED, response.friend.existence)

        self._set_disabled_broadcast_types([TYPE1, TYPE2])
        self._assert_disabled_broadcast_types([TYPE1, TYPE2])

        self._make_friends()
        self._assert_disabled_broadcast_types([TYPE1, TYPE2])

        response = self._get_friend()
        self.assertEqual(FriendTO.FRIEND_EXISTENCE_ACTIVE, response.friend.existence)

        self._set_disabled_broadcast_types([])
        self._assert_disabled_broadcast_types([])

    def test_disabling_types_of_connected_service(self):
        self.set_datastore_hr_probability(1)
        self._setup()

        self._make_friends()
        self._assert_disabled_broadcast_types([])

        self._set_disabled_broadcast_types([TYPE1])
        self._assert_disabled_broadcast_types([TYPE1])

        self._break_friendship()
        self._assert_disabled_broadcast_types([TYPE1])

        response = self._get_friend()
        self.assertEqual(FriendTO.FRIEND_EXISTENCE_DELETED, response.friend.existence)

        self._set_disabled_broadcast_types([TYPE1, TYPE2])
        self._assert_disabled_broadcast_types([TYPE1, TYPE2])

        self._make_friends()
        self._assert_disabled_broadcast_types([TYPE1, TYPE2])

        self._set_disabled_broadcast_types([])
        self._assert_disabled_broadcast_types([])
