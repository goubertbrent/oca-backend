# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
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
# @@license_version:1.5@@

import datetime
import logging

import webapp2
from dateutil import relativedelta
from google.appengine.ext import ndb

from rogerthat.bizz.job import run_job
from rogerthat.rpc import users
from solutions.common.bizz.events import update_events_from_google
from solutions.common.bizz.events.events_search import delete_events_from_index
from solutions.common.models.agenda import SolutionCalendar, Event


class CleanupSolutionEvents(webapp2.RequestHandler):

    def get(self):
        yesterday = datetime.datetime.now() - relativedelta.relativedelta(days=1)
        event_keys = Event.list_less_than_end_date(yesterday).fetch(keys_only=True)
        logging.info('Cleaning up %d expired Event models' % len(event_keys))
        delete_events_from_index(event_keys)
        ndb.delete_multi(event_keys)


class SolutionSyncGoogleCalendarEvents(webapp2.RequestHandler):

    def get(self):
        run_job(_get_solution_calendars_to_sync_with_google_query, [], _process_solution_calendar_sync_google_events,
                [])


def _get_solution_calendars_to_sync_with_google_query():
    return SolutionCalendar.list_with_google_sync()


def _process_solution_calendar_sync_google_events(sc_key):
    calendar_id = sc_key.id()
    service_user = users.User(sc_key.parent().id())
    update_events_from_google(service_user, calendar_id)
