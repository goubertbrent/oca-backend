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

import oca_unittest
from rogerthat.rpc import users
from shop.bizz import create_or_update_customer, create_contact
from solutions.common.bizz import OrganizationType, SolutionModule
from solutions.common.restapi.services import rest_put_service
from solutions.flex.bizz import create_flex_service
from test import set_current_user


class AssociationsTestCase(oca_unittest.TestCase):

    def test_association_creation(self):
        self.set_datastore_hr_probability(1)
        community = self.communities[2]
        r = create_flex_service(email=u'test-communicatie@example.be',
                                name=u"test",
                                phone_number=u"+32 9 324 25 64",
                                languages=[u"en", u"nl"],
                                currency=u"EUR",
                                modules=[SolutionModule.CITY_APP, SolutionModule.NEWS, SolutionModule.ASK_QUESTION,
                                         SolutionModule.WHEN_WHERE],
                                allow_redeploy=False,
                                organization_type=OrganizationType.CITY,
                                community_id=community.id)
        # Create city customer
        vat = u''
        name = u'Town Lochristi'
        address1 = u'Dorp - West 52'
        address2 = u''
        zip_code = u'9080'
        city = u'Lochristi'
        country = u'BE'
        language = u'nl'
        organization_type = OrganizationType.CITY
        city_customer = create_or_update_customer(None, vat, name, address1, address2, zip_code, city,
                                                  country, language, organization_type,
                                                  community_id=community.id)
        city_customer.service_email = city_customer.user_email = r.login
        city_customer.put()

        community.main_service = city_customer.service_email
        community.put()

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
        set_current_user(users.User(r.login), set_google_user=False)
        output = rest_put_service(name, address1, address2, zip_code, city, user_email, telephone, language,
                                  None, organization_type, modules=modules)
        self.assertTrue(output.success, output.errormsg)
        self.assertFalse(output.errormsg)
