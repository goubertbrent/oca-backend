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

import mc_unittest
from rogerthat.bizz.payment import create_payment_provider, get_and_update_payment_database_info
from rogerthat.dal.payment import get_payment_user_key, get_payment_user
from rogerthat.models.payment import PaymentUser, PaymentUserProvider, \
    PaymentUserAsset
from rogerthat.rpc import users
from rogerthat.to.payment import PaymentProviderTO


class Test(mc_unittest.TestCase):

    def setUp(self, *args):
        super(Test, self).setUp(*args)
        self.create_payment_provider()
        self.app_user = users.User(u"test@example.com")
        self.create_user()

    def create_payment_provider(self):
        data = PaymentProviderTO(id=u"payconiq",
                                 name=u"Payconiq test",
                                 logo=None,
                                 version=1,
                                 description=u"Test descripion is markdown",
                                 oauth_settings=None,
                                 background_color=None,
                                 text_color=None,
                                 button_color=None,
                                 black_white_logo=None,
                                 asset_types=[],
                                 currencies=[u'EUR'],
                                 settings={'a': 1},
                                 embedded_application=None,
                                 app_ids=[])
        create_payment_provider(data)

    def create_user(self):
        payment_user_key = get_payment_user_key(self.app_user)
        payment_user = PaymentUser(key=payment_user_key)
        payment_user.providers = []
        payment_user.assets = []
        payment_user.put()

    def create_user_with_assets(self):
        payment_user_key = get_payment_user_key(self.app_user)
        payment_user = PaymentUser(key=payment_user_key)
        payment_user.providers = []
        payment_user.assets = []

        payment_user.providers.append(PaymentUserProvider(provider_id=u'test', token=None))
        payment_user.assets.append(PaymentUserAsset(
            provider_id=u'test', asset_id=u'create_test', currency=u'CURRENCY', type=u'account', required_action=None))

        payment_user.put()

    def testSyncPaymentDatabase(self):
        self.set_datastore_hr_probability(1)

        get_and_update_payment_database_info(self.app_user)

        payment_user = get_payment_user(self.app_user)
        self.assertEqual(1, len(payment_user.assets))

    def testSyncPaymentDatabaseCreate(self):
        self.set_datastore_hr_probability(1)
        self.create_user_with_assets()

        get_and_update_payment_database_info(self.app_user)

        payment_user = get_payment_user(self.app_user)
        self.assertEqual(1, len(payment_user.assets))
