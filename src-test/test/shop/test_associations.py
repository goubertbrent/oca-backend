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

import mc_unittest
from rogerthat.models import App
from rogerthat.rpc import users
from shop.bizz import create_or_update_customer, create_contact
from shop.models import RegioManagerTeam
from solutions.common.bizz import OrganizationType, SolutionModule
from solutions.common.restapi.services import rest_put_service
from solutions.flex.bizz import create_flex_service
from test import set_current_user


class AssociationsTestCase(mc_unittest.TestCase):
    def test_association_creation(self):
        self.set_datastore_hr_probability(1)
        apps = [a.app_id for a in App.all()]
        r = create_flex_service(email=u'test-communicatie@example.be',
                                name=u"test",
                                address=u"Antwerpsesteenweg 19\n9080 Lochristi",
                                phone_number=u"+32 9 324 25 64",
                                languages=[u"en", u"nl"],
                                currency=u"€",
                                modules=[SolutionModule.CITY_APP, SolutionModule.BROADCAST, SolutionModule.ASK_QUESTION,
                                         SolutionModule.WHEN_WHERE],
                                broadcast_types=['News', 'test'],
                                apps=apps,
                                allow_redeploy=False,
                                organization_type=OrganizationType.CITY)
        # Create city customer
        shop_user = users.User(u'regiomanager-test@example.com') 
        customer_id = None
        vat = u''
        name = u'Town Lochristi'
        address1 = u'Dorp - West 52'
        address2 = u''
        zip_code = u'9080'
        city = u'Lochristi'
        country = u'BE'
        language = u'nl'
        organization_type = OrganizationType.CITY
        prospect_id = None
        city_customer = create_or_update_customer(shop_user, customer_id, vat, name, address1, address2, zip_code, city,
                                                  country, language, organization_type, prospect_id,
                                                  team_id=RegioManagerTeam.all().get().id)
        city_customer.service_email = city_customer.user_email = r.login
        city_customer.default_app_id = apps[0]
        city_customer.app_ids = apps
        city_customer.put()

        # Create city contact
        first_name = u'Firstname'
        last_name = u'Lastname'
        email_address = u'firstnamelastname@lochristi.be'
        phone_number = u'+3293268806'

        create_contact(city_customer, first_name, last_name, email_address, phone_number)

        name = u'test-Test association'
        address1 = u'Antwerpsesteenweg 19'
        address2 = u''
        zip_code = u'9080'
        city = u'Lochristi'
        user_email = u'test_association_lochristi@test.com'
        telephone = u'+32 9 324 25 64'
        language = u'nl'
        modules = [u'agenda', u'bulk_invite', u'static_content', u'ask_question', u'broadcast']
        broadcast_types = [u'Evenementen', u'Nieuws']
        set_current_user(users.User(r.login), set_google_user=False)
        output = rest_put_service(name, address1, address2, zip_code, city, user_email, telephone, language, modules,
                                 broadcast_types)
        self.assertTrue(output.success, output.errormsg)
        self.assertFalse(output.errormsg)
