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

from __future__ import unicode_literals

from google.appengine.ext import db

import mc_unittest
from test import set_current_user

from rogerthat.dal import parent_key_unsafe
from rogerthat.consts import WEEK
from rogerthat.models import App
from rogerthat.rpc import users
from rogerthat.to.service import UserDetailsTO
from rogerthat.utils import now
from rogerthat.utils.app import create_app_user_by_email

from solutions.common import SOLUTION_COMMON
from solutions.common.bizz import SolutionModule, OrganizationType, common_provision
from solutions.common.bizz.loyalty import add_loyalty_for_user, redeem_lottery_winners
from solutions.common.cron.loyalty import _pick_winner
from solutions.common.models.loyalty import SolutionLoyaltySettings, SolutionLoyaltyLottery
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

    def _create_service(self, email, org_type=OrganizationType.PROFIT, city_wide_lottery=False):
        self.set_datastore_hr_probability(1)

        loyalty_module = SolutionModule.HIDDEN_CITY_WIDE_LOTTER if city_wide_lottery else SolutionModule.LOYALTY
        service = create_flex_service(email,
                                      name="test",
                                      address="test address",
                                      phone_number="",
                                      languages=["en", "nl"],
                                      currency=u"EUR",
                                      modules=list(SolutionModule.STATIC_MODULES) + [
                                      loyalty_module],
                                      broadcast_types=[
                                      'test1', 'test2', 'test3'],
                                      apps=[a.app_id for a in App.all()],
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
