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

from google.appengine.ext import db
import mc_unittest
from rogerthat.bizz.friends import makeFriends
from rogerthat.bizz.profile import create_service_profile, create_user_profile
from rogerthat.bizz.service import set_user_data_object, set_app_data
from rogerthat.dal.service import get_service_identity
from rogerthat.models import UserData
from rogerthat.rpc import users


class Test(mc_unittest.TestCase):

    def setUp(self):
        super(Test, self).setUp(1)
        self.service_user = users.User(u'service@rogerth.at')
        _, service_identity = create_service_profile(self.service_user, u"Rogerthat Service")
        self.service_identity_user = service_identity.user

        self.app_user = users.User(u'john_doe@foo.com')
        create_user_profile(self.app_user, u"John Doe")

        makeFriends(self.app_user, self.service_user, original_invitee=None, servicetag=None, origin=None)

    def test_user_data(self):
        expected_data = {'key1': 1, 'key2': 2}
        set_user_data_object(self.service_identity_user, self.app_user, expected_data)

        user_data = db.get(UserData.createKey(self.app_user, self.service_identity_user))
        self.assertDictEqual(expected_data, user_data.userData.to_json_dict())

        new_data = {'key3': 3}
        set_user_data_object(self.service_identity_user, self.app_user, new_data)

        expected_data.update(new_data)
        user_data = db.get(UserData.createKey(self.app_user, self.service_identity_user))
        self.assertDictEqual(expected_data, user_data.userData.to_json_dict())

        new_data = {'key1': None, 'key2': 'B', 'key3': 'C', 'key4': 'D'}
        set_user_data_object(self.service_identity_user, self.app_user, new_data)

        expected_data.update(new_data)
        del expected_data['key1']
        user_data = db.get(UserData.createKey(self.app_user, self.service_identity_user))
        self.assertDictEqual(expected_data, user_data.userData.to_json_dict())

    def test_app_data(self):
        expected_data = {'key1': 1, 'key2': 2}
        set_app_data(self.service_identity_user, json.dumps(expected_data))

        si = get_service_identity(self.service_identity_user)
        self.assertDictEqual(expected_data, si.serviceData.to_json_dict())

        new_data = {'key3': 3}
        set_app_data(self.service_identity_user, json.dumps(new_data))

        expected_data.update(new_data)
        si = get_service_identity(self.service_identity_user)
        self.assertDictEqual(expected_data, si.serviceData.to_json_dict())

        new_data = {'key1': None, 'key2': 'B', 'key3': 'C', 'key4': 'D'}
        set_app_data(self.service_identity_user, json.dumps(new_data))

        expected_data.update(new_data)
        del expected_data['key1']
        si = get_service_identity(self.service_identity_user)
        self.assertDictEqual(expected_data, si.serviceData.to_json_dict())
