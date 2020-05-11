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

import mc_unittest
from rogerthat.bizz.profile import create_user_profile
from rogerthat.rpc import users
from rogerthat_tests import set_current_user


class RPCUserTests(mc_unittest.TestCase):

    def testSetUser(self):
        user1 = users.User(u"test1@mobicage.com")
        create_user_profile(user1, user1.email())
        set_current_user(user1)

        self.assertEqual(users.get_current_user(), user1)

        user2 = users.User(u"test2@mobicage.com")
        create_user_profile(user2, user2.email())
        set_current_user(user2)

        self.assertEqual(users.get_current_user(), user2)

    def testSetUserWith(self):
        user1 = users.User(u"test1@mobicage.com")
        set_current_user(user1)

        user2 = users.User(u"test2@mobicage.com")
        with set_current_user(user2):
            self.assertEqual(users.get_current_user(), user2)

        self.assertEqual(users.get_current_user(), user1)
