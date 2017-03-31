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
# @@license_version:1.2@@

from types import NoneType

from mcfw.rpc import returns, arguments
from rogerthat.dal import generator, parent_key_unsafe
from rogerthat.rpc import users
from solutions.common import SOLUTION_COMMON
from solutions.common.models.loyalty import SolutionLoyaltySlide, SolutionLoyaltyVisitRevenueDiscount, \
    SolutionLoyaltyVisitLottery, SolutionLoyaltyVisitStamps, SolutionLoyaltyIdentitySettings, \
    SolutionCityWideLotteryVisit
from solutions.common.utils import create_service_identity_user_wo_default, is_default_service_identity


def get_solution_loyalty_settings_or_identity_settings(sln_l_settings, service_identity):
    if is_default_service_identity(service_identity):
        return sln_l_settings
    else:
        return SolutionLoyaltyIdentitySettings.get_by_user(sln_l_settings.service_user, service_identity)

@returns([SolutionLoyaltySlide])
@arguments(service_user=users.User, service_identity=unicode)
def get_solution_loyalty_slides(service_user, service_identity):
    service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
    qry = SolutionLoyaltySlide.gql("WHERE ANCESTOR IS :ancestor AND deleted=False ORDER BY timestamp DESC")
    qry.bind(ancestor=parent_key_unsafe(service_identity_user, SOLUTION_COMMON))
    return generator(qry.run())

@returns([SolutionLoyaltyVisitRevenueDiscount])
@arguments(service_user=users.User, service_identity=unicode, app_user=users.User, max_visits=(int, long, NoneType))
def get_solution_loyalty_visits_for_revenue_discount(service_user, service_identity, app_user, max_visits=None):
    service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
    qry = SolutionLoyaltyVisitRevenueDiscount.all() \
        .ancestor(parent_key_unsafe(service_identity_user, SOLUTION_COMMON)) \
        .filter('redeemed =', False) \
        .filter('app_user =', app_user)

    if max_visits:
        qry.order('timestamp')
        return qry.fetch(max_visits)
    else:
        qry.order('-timestamp')
        return generator(qry.run())

@returns([SolutionLoyaltyVisitLottery])
@arguments(service_user=users.User, service_identity=unicode, app_user=users.User)
def get_solution_loyalty_visits_for_lottery(service_user, service_identity, app_user):
    service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
    qry = SolutionLoyaltyVisitLottery.all().ancestor(parent_key_unsafe(service_identity_user, SOLUTION_COMMON)).filter('redeemed =', False).filter('app_user =', app_user)
    return generator(qry.run())


@returns([SolutionLoyaltyVisitStamps])
@arguments(service_user=users.User, service_identity=unicode, app_user=users.User, max_stamps=(int, long, NoneType), return_qry=bool)
def get_solution_loyalty_visits_for_stamps(service_user, service_identity, app_user, max_stamps=None, return_qry=False):
    service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
    qry = SolutionLoyaltyVisitStamps.all() \
        .ancestor(parent_key_unsafe(service_identity_user, SOLUTION_COMMON)) \
        .filter('redeemed =', False) \
        .filter('app_user =', app_user)

    if max_stamps:
        qry.order('timestamp')
        if return_qry:
            return qry
        return qry.fetch(max_stamps)
    else:
        return generator(qry.run())

@returns([SolutionCityWideLotteryVisit])
@arguments(app_id=unicode, app_user=users.User, max_stamps=(int, long, NoneType), return_qry=bool)
def get_solution_city_wide_lottery_loyalty_visits_for_user(app_id, app_user, max_stamps=None, return_qry=False):
    parent_key = SolutionCityWideLotteryVisit.create_city_parent_key(app_id)
    qry = SolutionCityWideLotteryVisit.all() \
        .ancestor(parent_key) \
        .filter('redeemed =', False) \
        .filter('app_user =', app_user)

    if max_stamps:
        qry.order('timestamp')
        if return_qry:
            return qry
        return qry.fetch(max_stamps)
    else:
        return generator(qry.run())
