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

import os

from google.appengine.api import search
from google.appengine.ext import db

import mc_unittest
from rogerthat.bizz.profile import create_service_profile, create_user_profile, update_password_hash, \
    get_profile_for_facebook_user, create_user_index_document, USER_INDEX
from rogerthat.models import UserProfile
from rogerthat.rpc import users
from rogerthat.translations import DEFAULT_LANGUAGE
from rogerthat.utils import now


class Test(mc_unittest.TestCase):

    def setUp(self, *args):
        super(Test, self).setUp(*args)
        self.facebook_access_token = os.environ.get('ROGERTHAT_FB_USER_ACCESS_TOKEN')

    def testGetProfileForFacebookUser(self):
        if self.facebook_access_token:
            profile = get_profile_for_facebook_user(self.facebook_access_token, app_user=None)
            self.assertIsInstance(profile, UserProfile)
            assert profile.language == DEFAULT_LANGUAGE

    def testServiceProfile(self):
        self.set_datastore_hr_probability(1)

        service_profile, service_identity = create_service_profile(users.User(u's1@foo.com'), 's1', is_trial=True)
        service_profile = db.get(service_profile.key())
        assert service_profile.avatarId > 1
        assert service_profile.passwordHash is None

        service_identity = db.get(service_identity.key())
        assert service_identity.name == 's1'

        now_ = now()
        update_password_hash(service_profile, u"passwordHash", now_)
        service_profile = db.get(service_profile.key())
        assert service_profile.passwordHash == "passwordHash"
        assert service_profile.lastUsedMgmtTimestamp == now_

    def testUserProfile(self):
        user_profile = create_user_profile(users.User(u'u1@foo.com'), 'u1', language='es')
        user_profile = db.get(user_profile.key())
        assert user_profile.avatarId > 1
        assert user_profile.passwordHash is None
        assert user_profile.language == 'es'
        assert user_profile.name == 'u1'

        now_ = now()
        update_password_hash(user_profile, u"passwordHash", now_)
        user_profile = db.get(user_profile.key())
        assert user_profile.passwordHash == "passwordHash"
        assert user_profile.lastUsedMgmtTimestamp == now_

    def testEmailWithWhitespaces(self):
        app_user = users.User(u'email with spaces@domain.com:my_app_id')
        app_user_email = app_user.email()

        fields = [
            search.TextField(name='email', value=app_user_email),
            search.TextField(name='name', value='My Name'),
            search.TextField(name='app_id', value='my_app_id')
        ]

        user_index = search.Index(USER_INDEX)
        with self.assertRaises(ValueError):
            doc = search.Document(doc_id=app_user_email, fields=fields)
            user_index.put(doc)

        result = create_user_index_document(user_index, app_user.email(), fields)
        doc_id = result.id
        self.assertTrue(doc_id.startswith('base64:'))
        self.assertIsNotNone(user_index.get(doc_id))
