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

import random

from test import set_current_user

import oca_unittest
from rogerthat.dal.profile import get_service_profile
from rogerthat.models import App, ServiceProfile
from rogerthat.rpc import users
from solutions.common.bizz import SolutionModule, OrganizationType, common_provision
from solutions.common.dal import get_solution_settings
from solutions.flex.bizz import create_flex_service


class BroadcastTestCase(oca_unittest.TestCase):

    def setUp(self, datastore_hr_probability=0):
        super(BroadcastTestCase, self).setUp(datastore_hr_probability)

    def test_broadcast_types_static_modules(self):
        self._create_with_modules(list(SolutionModule.STATIC_MODULES))

    def test_broadcast_types_broadcast(self):
        self._create_with_modules([SolutionModule.BROADCAST])

    def test_broadcast_types_visible(self):
        self._create_with_modules(SolutionModule.visible_modules())

    def _create_with_modules(self, modules):
        self.set_datastore_hr_probability(1)

        email = u'test2.flex@foo.com'
        print 'create_flex_service start'
        r = create_flex_service(email,
                                name="test",
                                phone_number="+32 9 324 25 64",
                                languages=["en", "nl"],
                                currency=u"EUR",
                                modules=modules,
                                broadcast_types=['test1', 'test2', 'test3'],
                                apps=[a.app_id for a in App.all()],
                                allow_redeploy=False,
                                organization_type=random.choice([x for x in OrganizationType.all() if x > 0]))
        print 'create_flex_service end'
        service_user = users.User(r.login)
        set_current_user(service_user)

        sln_settings = get_solution_settings(service_user)
        self.assertEqual(sln_settings.broadcast_types, ['test1', 'test2', 'test3'])
        service_profile = get_service_profile(service_user)
        self.assertEqual(service_profile.broadcastTypes, [])

        print 'common_provision start'
        common_provision(service_user)
        print 'common_provision end'
        sp = ServiceProfile.get(service_profile.key())
        if SolutionModule.BROADCAST in modules:
            self.assertEqual(sp.broadcastTypes, ['test1', 'test2', 'test3'])
            sln_settings.broadcast_types.append('test4')
            sln_settings.put()

            print 'common_provision_extra start'
            common_provision(service_user)
            print 'common_provision_extra end'
            sp = ServiceProfile.get(service_profile.key())
            self.assertEqual(sp.broadcastTypes, ['test1', 'test2', 'test3', 'test4'])
        else:
            self.assertEqual(sp.broadcastTypes, [])  # no broadcast module
