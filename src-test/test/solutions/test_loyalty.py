# coding: utf-8
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
from __future__ import unicode_literals

from google.appengine.ext import db

import mc_unittest
from test import set_current_user

from rogerthat.bizz.messaging import MessageLockedException
from rogerthat.consts import WEEK
from rogerthat.dal import parent_key_unsafe
from rogerthat.models import App, ServiceIdentity
from rogerthat.rpc import users
from rogerthat.to.service import UserDetailsTO
from rogerthat.utils import now
from rogerthat.utils.app import create_app_user_by_email
from rogerthat.service.api import system

from solutions.common import SOLUTION_COMMON
from solutions.common.bizz import _get_location, SolutionModule, OrganizationType, common_provision
from solutions.common.bizz.loyalty import _get_app_id_if_using_city_wide_tombola, add_city_postal_code, \
    add_loyalty_for_user, redeem_lottery_winners
from solutions.common.cron.loyalty import _pick_winner, _pick_city_wide_lottery_winner
from solutions.common.dal import get_solution_settings, get_solution_settings_or_identity_settings
from solutions.common.models.loyalty import SolutionCityWideLottery, SolutionLoyaltySettings, SolutionLoyaltyLottery
from solutions.common.utils import create_service_identity_user_wo_default
from solutions.flex.bizz import create_flex_service


class LotteryTest(mc_unittest.TestCase):

    """This should test the lottery flow/logic.
    Needed helpers: create service with certain modules
                    create app users
                    -are these helpers exist?-

    Testing steps:
        create the service with loyalty module and lottery (and type lottery)
               another one with city_lottery enabled
        add some visits, then try to pick a winner

    """
    def setUp(self):
        super(LotteryTest, self).setUp(datastore_hr_probability=1)

    def _create_service(self, email, org_type=OrganizationType.PROFIT, city_wide_lottery=False, **service):
        loyalty_module = SolutionModule.HIDDEN_CITY_WIDE_LOTTERY if city_wide_lottery else SolutionModule.LOYALTY
        service = create_flex_service(email,
                                      name=service.get('name', 'test'),
                                      address=service.get('address', 'test address'),
                                      phone_number=service.get('phone_number', ''),
                                      languages=service.get('languages', ['en', 'nl']),
                                      currency=service.get('currency', u'€'),
                                      modules=[SolutionModule.WHEN_WHERE, SolutionModule.BILLING , loyalty_module],
                                      broadcast_types=service.get('broadcast_types', [
                                      'test1', 'test2', 'test3']),
                                      apps=service.get('apps', [a.app_id for a in App.all()]),
                                      allow_redeploy=False,
                                      organization_type=org_type)

        service_user = users.User(service.login)
        set_current_user(service_user)
        common_provision(service_user)
        return service_user

    def _create_lottery(self, service_user):
        settings = SolutionLoyaltySettings.get_by_user(service_user)
        settings.loyalty_type = SolutionLoyaltySettings.LOYALTY_TYPE_LOTTERY
        settings.put()

        service_identity_user = create_service_identity_user_wo_default(service_user, None)

        _now = now()
        lottery = SolutionLoyaltyLottery(parent=parent_key_unsafe(service_identity_user, SOLUTION_COMMON))
        lottery.timestamp = _now
        lottery.end_timestamp = _now + WEEK
        lottery.schedule_loot_time = 0
        lottery.winnings = 'win a mocked prize!'
        lottery.winner = None
        lottery.winner_info = None
        lottery.winner_timestamp = 0
        lottery.skip_winners = []
        lottery.pending = True
        lottery.redeemed = False
        lottery.claimed = False
        db.put([settings, lottery])
        return lottery

    def _to_user_detial(self, app_user):
        user_detail = UserDetailsTO()
        user_detail.email = app_user.email()
        user_detail.name = app_user.email()
        user_detail.language = 'en'
        user_detail.app_id = 'rogerthat'
        user_detail.avatar_url = 'dummy_avatar_url'
        return user_detail

    def _add_lottery_for_users(self, service_user):
        user1 = create_app_user_by_email('user1@user.foo')
        user2 = create_app_user_by_email('user2@user.foo')
        user3 = create_app_user_by_email('user3@user.foo')
        admin_user = create_app_user_by_email('admin@user.bar')

        add_loyalty_for_user(service_user, None, admin_user, user1, {
            'loyalty_type': SolutionLoyaltySettings.LOYALTY_TYPE_LOTTERY
        }, now(), self._to_user_detial(user1))

        add_loyalty_for_user(service_user, None, admin_user, user2, {
            'loyalty_type': SolutionLoyaltySettings.LOYALTY_TYPE_LOTTERY
        }, now(), self._to_user_detial(user2))

        add_loyalty_for_user(service_user, None, admin_user, user3, {
            'loyalty_type': SolutionLoyaltySettings.LOYALTY_TYPE_LOTTERY
        }, now(), self._to_user_detial(user3))

    def test_lottery(self):
        service_user = self._create_service('test@email.com')
        lottery = self._create_lottery(service_user)
        self._add_lottery_for_users(service_user)
        sim_parent, _ = _pick_winner(service_user, lottery.key())
        lottery = SolutionLoyaltyLottery.get(lottery.key())
        self.assertNotEqual(lottery.winner, None)
        reddem_result = redeem_lottery_winners(service_user, None, lottery.winner, 'THE WINNER!', sim_parent)
        self.assertTrue(reddem_result)

    def _create_city_wide_lottery(self, city_app_id, winners_count=2):
        _now = now()
        lottery = SolutionCityWideLottery(parent=SolutionCityWideLottery.create_parent_key(city_app_id))
        lottery.timestamp = _now
        lottery.end_timestamp = _now + WEEK
        lottery.schedule_loot_time = 0
        lottery.winnings = 'city wide prize!'
        lottery.x_winners = winners_count
        lottery.winners = []
        lottery.winner_info = []
        lottery.skip_winners = []
        lottery.deleted = False
        lottery.pending = True
        return unicode(lottery.put())

    def test_city_wide_lottery(self):
        app_id = u'be-loc'
        service = {
            'name': 'Main city service',
            'address': '9080 Lochristi',
            'apps': [app_id, 'rogerthat']
        }
        city_service_user = self._create_service('city@service.com',
                                                 org_type=OrganizationType.CITY,
                                                 city_wide_lottery=True,
                                                 **service)

        # ensure the city service create postal codes to enable city wide lottery
        add_city_postal_code(app_id, '9080')
        self.assertIsNotNone(_get_app_id_if_using_city_wide_tombola(city_service_user, ServiceIdentity.DEFAULT))
        city_wide_lottery_key = self._create_city_wide_lottery(app_id)

        service_user = self._create_service('test@email.com', address='9080 Lochristi')
        self.assertIsNotNone(_get_app_id_if_using_city_wide_tombola(service_user, ServiceIdentity.DEFAULT))
        self._create_lottery(service_user)
        self._add_lottery_for_users(service_user)

        _pick_city_wide_lottery_winner(city_service_user, city_wide_lottery_key)
        city_wide_lottery = db.get(city_wide_lottery_key)

        self.assertEqual(city_wide_lottery.winners_info, False)
