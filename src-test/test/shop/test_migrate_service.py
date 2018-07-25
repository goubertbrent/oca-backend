# -*- coding: utf-8 -*-
# Copyright 2018 Mobicage NV
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
# @@license_version:1.3@@

from rogerthat.rpc import users
from rogerthat.utils import now
from google.appengine.ext import db
import mc_unittest
from shop.jobs.migrate_service import MigrateServiceJob, _create_new_key


from_service_email = u'from@foo.com'
to_service_email = u'to@foo.com'

job = MigrateServiceJob(parent=db.Key.from_path(MigrateServiceJob.kind(), MigrateServiceJob.kind()),
                        executor_user=users.User('bart@example.com'),
                        from_service_user=users.User(from_service_email),
                        to_service_user=users.User(to_service_email),
                        phase=0,
                        solution=None,
                        customer_key=None,
                        fsic_keys=[],
                        service_enabled=False,
                        start_timestamp=now())

class TestMigrateService(mc_unittest.TestCase):


    def test_create_new_key_with_normal_key_name(self):
        old_key = db.Key.from_path('kind1', 'test123')
        self.assertEqual(old_key, _create_new_key(job, old_key))


    def test_create_new_key_with_constant_key_name_with_service_user_parent(self):
        old_key = db.Key.from_path('kind1', 'test123',
                                    parent=db.Key.from_path('kind2', from_service_email))
        expected_key = db.Key.from_path('kind1', 'test123',
                                        parent=db.Key.from_path('kind2', to_service_email))
        self.assertEqual(expected_key, _create_new_key(job, old_key))


    def test_create_new_key_with_service_user_with_constant_parent(self):
        old_key = db.Key.from_path('kind1', from_service_email,
                                    parent=db.Key.from_path('kind2', 'test123'))
        expected_key = db.Key.from_path('kind1', to_service_email,
                                    parent=db.Key.from_path('kind2', 'test123'))
        self.assertEqual(expected_key, _create_new_key(job, old_key))


    def test_create_new_key_with_service_user_without_parent(self):
        old_key = db.Key.from_path('kind1', from_service_email)
        expected_key = db.Key.from_path('kind1', to_service_email)
        self.assertEqual(expected_key, _create_new_key(job, old_key))


    def test_create_new_key_with_si_user_without_parent(self):
        old_key = db.Key.from_path('kind1', '%s/+default+' % from_service_email)
        expected_key = db.Key.from_path('kind1', '%s/+default+' % to_service_email)
        self.assertEqual(expected_key, _create_new_key(job, old_key))


    def test_create_new_key_with_service_user_with_service_user_parent(self):
        old_key = db.Key.from_path('kind1', from_service_email,
                                   parent=db.Key.from_path('kind2', from_service_email))
        expected_key = db.Key.from_path('kind1', to_service_email,
                                        parent=db.Key.from_path('kind2', to_service_email))
        self.assertEqual(expected_key, _create_new_key(job, old_key))


    def test_create_new_key_with_si_user_with_service_user_parent(self):
        old_key = db.Key.from_path('kind1', '%s/+default+' % from_service_email,
                                   parent=db.Key.from_path('kind2', from_service_email))
        expected_key = db.Key.from_path('kind1', '%s/+default+' % to_service_email,
                                        parent=db.Key.from_path('kind2', to_service_email))
        self.assertEqual(expected_key, _create_new_key(job, old_key))


    def test_create_new_key_with_service_user_with_si_user_parent(self):
        old_key = db.Key.from_path('kind1', from_service_email,
                                   parent=db.Key.from_path('kind2', from_service_email))
        expected_key = db.Key.from_path('kind1', to_service_email,
                                        parent=db.Key.from_path('kind2', to_service_email))
        self.assertEqual(expected_key, _create_new_key(job, old_key))


    def test_create_new_key_with_si_user_with_si_user_parent(self):
        old_key = db.Key.from_path('kind1', '%s/+default+' % from_service_email,
                                   parent=db.Key.from_path('kind2', '%s/+default+' % from_service_email))
        expected_key = db.Key.from_path('kind1', '%s/+default+' % to_service_email,
                                        parent=db.Key.from_path('kind2', '%s/+default+' % to_service_email))
        self.assertEqual(expected_key, _create_new_key(job, old_key))


    def test_create_new_key_with_2_parents(self):
        old_key = db.Key.from_path('EventGuest', 'blabla',
                                   parent=db.Key.from_path('Event', 123,
                                                           parent=db.Key.from_path('flex', from_service_email)))
        expected_key = db.Key.from_path('EventGuest', 'blabla',
                                        parent=db.Key.from_path('Event', 123,
                                                                parent=db.Key.from_path('flex', to_service_email)))
        self.assertEqual(expected_key, _create_new_key(job, old_key))
