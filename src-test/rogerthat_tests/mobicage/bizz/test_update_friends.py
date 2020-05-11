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

import cloudstorage

import mc_unittest
from rogerthat.bizz.friend_helper import FriendHelper
from rogerthat.bizz.friends import makeFriends, ORIGIN_USER_INVITE
from rogerthat.bizz.i18n import DummyTranslator
from rogerthat.bizz.job.update_friends import convert_friend
from rogerthat.bizz.profile import create_service_profile, create_user_profile
from rogerthat.bizz.service import create_menu_item, set_app_data
from rogerthat.bizz.service.broadcast import set_broadcast_types
from rogerthat.consts import FRIEND_HELPER_BUCKET
from rogerthat.dal.friend import get_friends_map
from rogerthat.models import ServiceProfile, ServiceIdentity, ServiceInteractionDef, UserProfile
from rogerthat.rpc import users
from rogerthat.to.friends import FriendTO, ServiceMenuItemLinkTO, UpdateFriendRequestTO
from rogerthat.utils.service import add_slash_default


class FriendHelperTestCase(mc_unittest.TestCase):

    def setUp(self, *args, **kwargs):
        super(FriendHelperTestCase, self).setUp(*args, **kwargs)

    def tearDown(self):
        super(FriendHelperTestCase, self).tearDown()
        for f in cloudstorage.listbucket(FRIEND_HELPER_BUCKET):
            cloudstorage.delete(f.filename)


class TestUpdateUser(FriendHelperTestCase):

    def setUp(self):
        super(TestUpdateUser, self).setUp(1)

        self.john = users.User(u'john_doe@foo.com')
        create_user_profile(self.john, u"John Doe")

        self.jane = users.User(u'jane_doe@foo.com')
        create_user_profile(self.jane, u"Jane Doe")

    def test_ds_helper_for_user(self):
        helper = FriendHelper.from_data_store(self.john, FriendTO.TYPE_USER)
        self.assertIsInstance(helper.get_profile_info(), UserProfile)
        self.assertIsNone(helper.get_service_profile())
        self.assertIsNone(helper.get_share_sid())
        self.assertIsNone(helper.get_translator())
        self.assertIsNone(helper.get_service_data())
        self.assertListEqual(helper.list_service_menu_items(), [])

    def test_cs_helper_for_user(self):
        helper = FriendHelper.serialize(self.john, FriendTO.TYPE_USER)
        self.assertIsInstance(helper.get_profile_info(), UserProfile)
        self.assertIsNone(helper.get_service_profile())
        self.assertIsNone(helper.get_share_sid())
        self.assertIsNone(helper.get_translator())
        self.assertIsNone(helper.get_service_data())
        self.assertListEqual(helper.list_service_menu_items(), [])


class TestUpdateService(FriendHelperTestCase):

    def setUp(self):
        super(TestUpdateService, self).setUp(1)
        self.service_user = users.User(u'service@rogerth.at')
        _, service_identity = create_service_profile(self.service_user, u"Rogerthat service")
        self.service_identity_user = service_identity.user

    def _assert_simple_service(self, helper):
        self.assertIsInstance(helper.get_service_profile(), ServiceProfile)
        self.assertIsInstance(helper.get_profile_info(), ServiceIdentity)
        self.assertIsInstance(helper.get_translator(), DummyTranslator)
        self.assertIsNone(helper.get_share_sid(), ServiceInteractionDef)
        self.assertIsNone(helper.get_service_data())
        self.assertListEqual(list(helper.list_service_menu_items()), [])

    def _extend_service(self):
        set_broadcast_types(self.service_user, ['Info', 'Events'])

        link = ServiceMenuItemLinkTO()
        link.url = u'https://www.google.com'
        link.external = False
        link.request_user_link = False
        create_menu_item(self.service_user, 'fa-help', '#ffffff', 'label', 'tag', [0, 1, 0], link=link)
        create_menu_item(self.service_user, 'fa-help', '#ffffff', 'label', 'tag', [0, 2, 0], is_broadcast_settings=True)

        self.data = dict(a=True, b='2', c=3, d=[1, 2, 3, 4])
        set_app_data(add_slash_default(self.service_user), json.dumps(self.data))

    def _assert_complex_service(self, helper):
        menu_items = list(helper.list_service_menu_items())
        self.assertEqual(2, len(menu_items))
        self.assertEqual(1, len(filter(lambda i: i.link, menu_items)))
        self.assertEqual(1, len(filter(lambda i: i.isBroadcastSettings, menu_items)))

        service_data = helper.get_service_data()
        self.assertDictEqual(self.data, service_data)

    def test_ds_helper_for_simple_service(self):
        helper = FriendHelper.from_data_store(self.service_user, FriendTO.TYPE_SERVICE)
        self._assert_simple_service(helper)

    def test_ds_helper_for_complex_service(self):
        self._extend_service()
        helper = FriendHelper.from_data_store(self.service_user, FriendTO.TYPE_SERVICE)
        self._assert_complex_service(helper)

    def test_cs_helper_for_simple_service(self):
        helper = FriendHelper.serialize(self.service_identity_user, FriendTO.TYPE_SERVICE)
        self._assert_simple_service(helper)

    def test_cs_helper_for_complex_service(self):
        self._extend_service()
        helper = FriendHelper.serialize(self.service_identity_user, FriendTO.TYPE_SERVICE)
        self._assert_complex_service(helper)

    def test_friend_to(self):
        self._extend_service()

        app_user = users.User(u'john_doe@foo.com')
        create_user_profile(app_user, u"John Doe")
        makeFriends(app_user, self.service_user, self.service_user, None, ORIGIN_USER_INVITE)

        cs_helper = FriendHelper.serialize(self.service_identity_user, FriendTO.TYPE_SERVICE)
        ds_helper = FriendHelper.from_data_store(self.service_user, FriendTO.TYPE_SERVICE)

        friend_map = get_friends_map(app_user)
        friend_detail = friend_map.friendDetails[self.service_user.email()]
        status = UpdateFriendRequestTO.STATUS_MODIFIED
        ds_friend = convert_friend(ds_helper, app_user, friend_detail, status)
        cs_friend = convert_friend(cs_helper, app_user, friend_detail, status)

        self.assertDictEqual(ds_friend.to_dict(), cs_friend.to_dict())
