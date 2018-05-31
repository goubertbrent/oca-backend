# -*- coding: utf-8 -*-
# Copyright 2017 Mobicage NV
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
# @@license_version:1.2@@

import webapp2

import mc_unittest
import random
from rogerthat.dal.profile import get_service_profile
from rogerthat.models import App
from rogerthat.pages.legal import get_current_document_version, \
    DOC_TERMS_SERVICE
from rogerthat.rpc import users
from solutions.common.bizz import SolutionModule, OrganizationType, common_provision
from solutions.common.bizz.menu import _put_default_menu
from solutions.common.dal import get_solution_settings
from solutions.common.models.order import SolutionOrderWeekdayTimeframe, SolutionOrderSettings
from solutions.flex.bizz import create_flex_service
from solutions.flex.handlers import FlexHomeHandler
from test import set_current_user


class FlexTestCase(mc_unittest.TestCase):

    def test_static_flex_service(self):
        self._test_static_flex_service()

    def test_static_flex_service_TOS(self):
        self._test_static_flex_service(False)

    def _test_static_flex_service(self, set_tos=True):
        self.set_datastore_hr_probability(1)

        print 'Test service creation with static modules'
        email = u'test1.flex.foo.com'
        r = create_flex_service(email,
                                name="test",
                                address="Antwerpsesteenweg 19\n9080 Lochristi",
                                phone_number="+32 9 324 25 64",
                                languages=["en", "nl"],
                                currency=u"€",
                                modules=list(SolutionModule.STATIC_MODULES),
                                broadcast_types=['test1', 'test2', 'test3'],
                                apps=[a.app_id for a in App.all()],
                                allow_redeploy=False,
                                organization_type=random.choice([x for x in OrganizationType.all() if x > 0]))

        service_user = users.User(r.login)
        set_current_user(service_user)

        print 'Test provisioning of static modules'
        common_provision(service_user)

        if set_tos:
            sp = get_service_profile(service_user)
            sp.tos_version = get_current_document_version(DOC_TERMS_SERVICE)
            sp.put()

        print 'Test rendering the home page'
        FlexHomeHandler({}, webapp2.Response()).get()

    def test_dynamic_flex_service_ES(self):
        self._test_dynamic_flex_service('es')

    def test_dynamic_flex_service_ES_TOS(self):
        self._test_dynamic_flex_service('es', False)

    def test_dynamic_flex_service_EN(self):
        self._test_dynamic_flex_service('en')

    def test_dynamic_flex_service_EN_TOS(self):
        self._test_dynamic_flex_service('en', False)

    def test_dynamic_flex_service_FR(self):
        self._test_dynamic_flex_service('fr')

    def test_dynamic_flex_service_FR_TOS(self):
        self._test_dynamic_flex_service('fr', False)

    def test_dynamic_flex_service_NL(self):
        self._test_dynamic_flex_service('nl')

    def test_dynamic_flex_service_NL_TOS(self):
        self._test_dynamic_flex_service('nl', False)

    def _test_dynamic_flex_service(self, language, set_tos=True):
        self.set_datastore_hr_probability(1)

        print 'Test %s service creation with all modules' % language
        email = u'test2.flex@foo.com'
        r = create_flex_service(email,
                                name="test",
                                address="Antwerpsesteenweg 19\n9080 Lochristi",
                                phone_number="+32 9 324 25 64",
                                languages=[language],
                                currency=u"€",
                                modules=SolutionModule.visible_modules(),
                                broadcast_types=['test1', 'test2', 'test3'],
                                apps=[a.app_id for a in App.all()],
                                allow_redeploy=False,
                                organization_type=random.choice([x for x in OrganizationType.all() if x > 0]))

        service_user = users.User(r.login)
        set_current_user(service_user)

        print 'Setting order type to advanced'
        _put_default_menu(service_user)

        sln_settings = get_solution_settings(service_user)
        sln_order_settings = SolutionOrderSettings(key=SolutionOrderSettings.create_key(service_user))
        sln_order_settings.text_1 = 'text_1'
        sln_order_settings.order_type = SolutionOrderSettings.TYPE_ADVANCED
        sln_order_settings.leap_time = 1
        sln_order_settings.leap_time_type = 86400
        sln_order_settings.put()
        SolutionOrderWeekdayTimeframe.create_default_timeframes_if_nessecary(service_user, sln_settings.solution)

        print 'Test provisioning of all modules'
        common_provision(service_user)

        if set_tos:
            sp = get_service_profile(service_user)
            sp.tos_version = get_current_document_version(DOC_TERMS_SERVICE)
            sp.put()

        print 'Test rendering the home page'
        FlexHomeHandler({}, webapp2.Response()).get()

        print 'Test deletion of all modules'
        solution_settings = get_solution_settings(service_user)
        solution_settings.modules = []
        solution_settings.put()
        common_provision(service_user)

        print 'Test rendering the home page'
        FlexHomeHandler({}, webapp2.Response()).get()
