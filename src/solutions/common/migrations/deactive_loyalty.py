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
from datetime import datetime
import logging
import time

from google.appengine.ext import db, deferred

from dateutil.relativedelta import relativedelta
from rogerthat.bizz.communities.communities import get_community
from rogerthat.bizz.job import run_job
from rogerthat.consts import FAST_QUEUE
from rogerthat.dal import parent_key_unsafe
from shop.dal import get_customer
from solutions.common import SOLUTION_COMMON
from solutions.common.bizz import SolutionModule, common_provision
from solutions.common.models import SolutionSettings
from solutions.common.models.loyalty import SolutionLoyaltyVisitLottery,\
    SolutionLoyaltyVisitRevenueDiscount, SolutionLoyaltyVisitStamps,\
    SolutionCityWideLotteryVisit, SolutionLoyaltySettings


def cleanup_loyalty_modules(dry_run=True):
    date = datetime.now() - relativedelta(years=2)
    timestamp = int(time.mktime(date.timetuple()))
    run_job(_get_loyalty_solution_settings, [], _do_cleanup, [timestamp, dry_run])


def _get_loyalty_solution_settings():
    return SolutionSettings.all().filter("modules =", SolutionModule.LOYALTY)


def _do_cleanup(sln_settings, timestamp, dry_run=True):
    logging.debug("service_user:%s", sln_settings.service_user)
    if sln_settings.service_disabled:
        logging.debug("ignoring service disabled")
        return
    if SolutionModule.CITY_APP in sln_settings.modules:
        logging.debug("ignoring for city app")
        return
    
    should_delete = False
    loyalty_settings = SolutionLoyaltySettings.get_by_user(sln_settings.service_user)
    if not loyalty_settings:
        should_delete = True
        logging.debug("Deleting loyalty_settings not found")
        
    if not should_delete:
        customer = get_customer(sln_settings.service_user)
        if not has_activity(sln_settings.service_user, customer, timestamp):
            should_delete = True
            logging.debug("Deleting no activity found")
    
    if not should_delete:
        logging.debug("keep loyalty")
        return
    
    logging.debug("deleting loyalty")
    if dry_run:
        return
    
    if should_delete:
        sln_settings.modules.remove(SolutionModule.LOYALTY)
        sln_settings.put()
        deferred.defer(common_provision, sln_settings.service_user, _countdown=5, _queue=FAST_QUEUE)


def has_activity(service_user, customer, timestamp):
    parent_key = parent_key_unsafe(service_user, SOLUTION_COMMON)

    count_lottery = SolutionLoyaltyVisitLottery.all().ancestor(parent_key).filter('timestamp > ', timestamp).count(None)
    logging.info("SolutionLoyaltyVisitLottery:%s", count_lottery)
    count_revenue = SolutionLoyaltyVisitRevenueDiscount.all().ancestor(parent_key).filter('timestamp > ', timestamp).count(None)
    logging.info("SolutionLoyaltyVisitRevenueDiscount:%s", count_revenue)
    count_stamps = SolutionLoyaltyVisitStamps.all().ancestor(parent_key).filter('timestamp > ', timestamp).count(None)
    logging.info("SolutionLoyaltyVisitStamps:%s", count_stamps)

    city_app_id = None
    if customer.app_id:
        city_app_id = customer.app_id
    elif customer.community_id:
        community = get_community(customer.community_id)
        city_app_id = community.default_app
    if city_app_id:
        city_ancestor_key = SolutionCityWideLotteryVisit.create_city_parent_key(city_app_id)
        service_ancestor_key = db.Key.from_path(SOLUTION_COMMON, service_user.email(), parent=city_ancestor_key)
        count_city = SolutionCityWideLotteryVisit.all().ancestor(service_ancestor_key).filter('timestamp > ', timestamp).count(None)
        logging.info("SolutionCityWideLotteryVisit:%s", count_city)
    else:
        count_city = 0
    
    if count_lottery > 0 or count_revenue > 0 or count_stamps > 0 or count_city > 0:
        return True
    return False