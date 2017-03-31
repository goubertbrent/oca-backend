# -*- coding: utf-8 -*-
# Copyright 2017 GIG Technology NV
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

import os
import shutil

from rogerthat.bizz.profile import create_user_profile
from rogerthat.bizz.service import UserWithThisEmailAddressAlreadyExistsException
from rogerthat.dal.profile import get_user_profile
from rogerthat.rpc import users
from rogerthat.rpc.service import ServiceApiException
from rogerthat.utils.app import create_app_user_by_email
import mc_unittest
from solutions.common.bizz import create_solution_service


class TestException(ServiceApiException):

    def __init__(self):
        super(TestException, self).__init__(300, "lekker")

def copytree(src, dst, symlinks=False, ignore=None):
    if not os.path.exists(dst):
        os.makedirs(dst)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            copytree(s, d, symlinks, ignore)
        else:
            if not os.path.exists(d) or os.stat(s).st_mtime - os.stat(d).st_mtime > 1:
                shutil.copy2(s, d)

class Test(mc_unittest.TestCase):

    def testServiceAPIException(self):
        try:
            raise TestException()
        except ServiceApiException, e:
            assert unicode(e) == "lekker"

    def test_create_service_with_existing_user(self):
        self.set_datastore_hr_probability(1)
        rogerthat_service_email = "service-rogerthat@foo.com"
        rogerthat_email = "rogerthat@foo.com"
        rogerthat_user = create_app_user_by_email(rogerthat_email, 'rogerthat')

        be_loc_email = "be.loc@foo.com"
        be_loc_user = create_app_user_by_email(be_loc_email, 'be-loc')

        for u in (rogerthat_user, be_loc_user):
            create_user_profile(u, u.email())

        with self.assertRaises(UserWithThisEmailAddressAlreadyExistsException) as cm:
            create_solution_service(rogerthat_email, 'name', solution='flex')
        self.assertEqual(rogerthat_email, cm.exception.fields['email'])

        _, new_service_sln_settings = create_solution_service(rogerthat_service_email, 'name', solution='flex',
                                                              owner_user_email=rogerthat_email)
        new_service_user = new_service_sln_settings.service_user
        self.assertEqual(rogerthat_service_email, new_service_user.email())
        self.assertTrue(rogerthat_service_email in get_user_profile(users.User(rogerthat_email), cached=False).owningServiceEmails)

        _, new_service_sln_settings = create_solution_service(be_loc_email, 'name', solution='flex')
        new_service_user = new_service_sln_settings.service_user
        self.assertEqual(be_loc_email, new_service_user.email())
