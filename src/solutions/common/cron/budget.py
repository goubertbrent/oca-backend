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

import logging

from google.appengine.ext import ndb, webapp

from rogerthat.bizz.job import run_job
from rogerthat.consts import DAY
from rogerthat.exceptions.news import NewsNotFoundException
from rogerthat.rpc import users
from rogerthat.service.api import news
from rogerthat.utils import today
from solutions import SOLUTION_COMMON, translate as common_translate
from solutions.common.bizz.budget import update_budget, BUDGET_RATE
from solutions.common.bizz.service import new_inbox_message, send_inbox_message_update
from solutions.common.dal import get_solution_settings
from solutions.common.models.budget import BudgetTransaction
from solutions.common.models.news import SolutionNewsItem


class BudgetCheckHandler(webapp.RequestHandler):

    def get(self):
        check_regional_news_budget()


def unpaid_regional_news_query(day_date):
    return SolutionNewsItem.query(
        SolutionNewsItem.paid == False,
        SolutionNewsItem.publish_time <= day_date - 14 * DAY)


def update_regional_news_budget(sln_news_item_key):
    news_id = sln_news_item_key.id()
    sln_news_item = sln_news_item_key.get()
    service_user = sln_news_item.service_user
    service_identity = sln_news_item.service_identity

    with users.set_user(service_user):
        try:
            news_item = news.get(news_id, service_identity, include_statistics=True)
        except NewsNotFoundException:
            logging.warning('News item with id %d is not found', news_id)
            return

    total_reach = 0
    for app_stats in news_item.statistics:
        if app_stats.app_id not in sln_news_item.app_ids:
            continue
        total_reach += app_stats.reached.total

    sln_settings = get_solution_settings(service_user)

    def send_inbox_message():
        message = common_translate(
            sln_settings.main_language, SOLUTION_COMMON, 'consumed_n_regional_news_views_message',
            title=news_item.title, id=news_item.id, n=total_reach)
        inbox_message = new_inbox_message(sln_settings, message, service_identity=service_identity)
        send_inbox_message_update(sln_settings, inbox_message, service_identity)

    @ndb.transactional(xg=True)
    def set_item_paid():
        sln_news_item = sln_news_item_key.get()
        if total_reach:
            memo = common_translate(
                sln_settings.main_language, SOLUTION_COMMON, 'consumed_n_regional_news_views', n=total_reach)
            deducted_amount = -long(round(total_reach / BUDGET_RATE))
            update_budget(service_user, deducted_amount, service_identity,
                          BudgetTransaction.TYPE_NEWS, sln_news_item_key, memo)
        sln_news_item.paid = True
        sln_news_item.put()

    set_item_paid()
    if total_reach:
        send_inbox_message()


def check_regional_news_budget():
    _today = today()
    run_job(unpaid_regional_news_query, [_today],
            update_regional_news_budget, [])
