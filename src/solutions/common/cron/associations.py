# -*- coding: utf-8 -*-
# Copyright 2016 Mobicage NV
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
# @@license_version:1.1@@

import logging

from google.appengine.ext import webapp, db
from google.appengine.ext.deferred import deferred

from mcfw.utils import chunks
from rogerthat.utils import now
from shop.models import Customer
from solutions.common.models import SolutionInboxMessage, SolutionScheduledBroadcast
from solutions.common.models.agenda import Event
from solutions.common.models.associations import AssociationStatistic
from solutions.common.models.static_content import SolutionStaticContent


class CreateNonProfitStatistics(webapp.RequestHandler):
    def get(self):
        deferred.defer(update_statistic)


def update_statistic():
    # Completely rebuilds statistics on run.

    current_date = now()
    broadcast_count_dict = dict()
    for broadcast_key in SolutionScheduledBroadcast.get_keys_last_month():
        service_email = broadcast_key.parent().name()
        if service_email not in broadcast_count_dict:
            broadcast_count_dict[service_email] = 1
        else:
            broadcast_count_dict[service_email] += 1

    future_event_count_dict = dict()

    for future_event_key in Event.get_future_event_keys(current_date):
        service_email = future_event_key.parent().name()
        if not service_email in future_event_count_dict:
            future_event_count_dict[service_email] = 1
        else:
            future_event_count_dict[service_email] += 1

    static_content_count_dict = dict()

    for static_content_key in SolutionStaticContent.get_all_keys():
        service_email = static_content_key.parent().name()
        if not service_email in static_content_count_dict:
            static_content_count_dict[service_email] = 1
        else:
            static_content_count_dict[service_email] += 1

    unanswered_question_count_dict = dict()

    # find the oldest, unanswered question per customer and add it to the statistics
    for unanswered_question in SolutionInboxMessage.get_all_unanswered_questions(5):
        service_email = unanswered_question.service_user.email()
        if unanswered_question.question_asked_timestamp != 0:
            if not service_email in unanswered_question_count_dict:
                unanswered_question_count_dict[service_email] = unanswered_question.question_asked_timestamp
            elif unanswered_question.question_asked_timestamp < unanswered_question_count_dict[service_email]:
                unanswered_question_count_dict[service_email] = unanswered_question.question_asked_timestamp

    # dict with as keys the app id from the city, value the statistics of this city.
    statistics = dict()
    for customer in Customer.get_all_non_profit():
        if len(customer.app_ids) != 0:
            service_email = customer.service_email
            if customer.app_id not in statistics:
                stats = AssociationStatistic(key_name=customer.app_id)
                stats.generated_on = current_date
                statistics[customer.app_id] = stats
            else:
                stats = statistics[customer.app_id]
            if not service_email:
                logging.error(u'Association customer %s(%d) has no service_email!', customer.name, customer.id)
                continue
            stats.customer_emails.append(service_email)

            if service_email in broadcast_count_dict:
                stats.broadcasts_last_month.append(broadcast_count_dict[customer.service_email])
            else:
                stats.broadcasts_last_month.append(0)

            if service_email in future_event_count_dict:
                stats.future_events_count.append(future_event_count_dict[service_email])
            else:
                stats.future_events_count.append(0)

            if service_email in static_content_count_dict:
                stats.static_content_count.append(static_content_count_dict[service_email])
            else:
                stats.static_content_count.append(0)

            if service_email in unanswered_question_count_dict:
                stats.last_unanswered_questions_timestamps.append(unanswered_question_count_dict[service_email])
            else:
                stats.last_unanswered_questions_timestamps.append(0)


    for chunk in chunks(statistics.values(), 200):
        db.put(chunk)
