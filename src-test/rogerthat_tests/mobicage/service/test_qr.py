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

import time

import mc_unittest
from rogerthat.bizz.profile import create_service_profile
from rogerthat.bizz.service import InvalidValueException
from rogerthat.rpc import users
from rogerthat.service.api import qr
from rogerthat_tests import set_current_user
from rogerthat.models import ServiceInteractionDef


class QrTest(mc_unittest.TestCase):

    def setUp(self, datastore_hr_probability=0):
        mc_unittest.TestCase.setUp(self, datastore_hr_probability=1)
        self._prepare_svc()

    def _prepare_svc(self, email=None):
        service_user = users.User(email or u'svc_test%s@foo.com' % time.time())
        create_service_profile(service_user, u'Test Name')
        set_current_user(service_user)
        return service_user

    def _qry(self):
        return ServiceInteractionDef.all().filter('deleted', False)

    def test_create(self):
        description = 'description'
        tag = 'tag'
        qr.create(description, tag)
        sid = self._qry().get()
        self.assertEqual(description, sid.description)
        self.assertEqual(tag, sid.tag)

    def test_bulk_create_with_1_description(self):
        description = 'description'
        tags = ['tag1', 'tag2', 'tag3']
        qr.bulk_create(description, tags)
        sids = sorted(self._qry(), key=lambda x: x.tag)

        self.assertEqual(len(tags), len(sids))
        for sid, tag in zip(sids, tags):
            self.assertEqual(description, sid.description)
            self.assertEqual(tag, sid.tag)

    def test_bulk_create_with_multiple_descriptions(self):
        descriptions = ['descr1', 'descr2', 'descr3']
        tags = ['tag1', 'tag2', 'tag3']
        qr.bulk_create(descriptions, tags)
        sids = sorted(self._qry(), key=lambda x: x.tag)

        self.assertEqual(len(tags), len(sids))
        for sid, description, tag in zip(sids, descriptions, tags):
            self.assertEqual(description, sid.description)
            self.assertEqual(tag, sid.tag)

    def test_bulk_create_failure(self):
        self.assertRaises(InvalidValueException, lambda: qr.bulk_create(['description'], ['tag1', 'tag2']))
