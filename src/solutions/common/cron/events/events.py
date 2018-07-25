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

import datetime
import logging

from google.appengine.ext import db, deferred
import webapp2

from babel.dates import format_date, format_time
from rogerthat.bizz.job import run_job
from rogerthat.dal import parent_key
from rogerthat.models import Message
from rogerthat.rpc import users
from rogerthat.service.api import messaging
from rogerthat.translations import DEFAULT_LANGUAGE
from rogerthat.utils import now
from rogerthat.utils.app import get_human_user_from_app_user
from rogerthat.utils.models import delete_all
from solutions.common.bizz.events import update_events_from_google
from solutions.common.bizz.provisioning import populate_identity_and_publish
from solutions.common.dal import get_solution_settings, get_solution_main_branding
from solutions.common.models import SolutionSettings
from solutions.common.models.agenda import EventReminder, Event, SolutionCalendar, SolutionCalendarGoogleSync


class UpdateSolutionEventStartDate(webapp2.RequestHandler):

    def get(self):
        run_job(_get_event_first_start_date_query, [], _update_first_start_date, [])


def _get_event_first_start_date_query():
    qry = db.GqlQuery("SELECT __key__ FROM Event WHERE first_start_date < :epoch")
    qry.bind(epoch=now())
    return qry


def _update_first_start_date(event_key):
    def trans():
        event = Event.get(event_key)
        if not event:  # event can be None if the CLEANUP cron_job is being run
            return
        new_first_start_date = event.get_first_event_date()
        if event.first_start_date != new_first_start_date:
            event.first_start_date = new_first_start_date
            event.put()
    db.run_in_transaction(trans)


class CleanupSolutionEvents(webapp2.RequestHandler):

    def get(self):
        yesterday = (now() - (24 * 60 * 60))
        qry = db.GqlQuery("SELECT __key__ FROM Event WHERE last_start_date < :epoch")
        qry.bind(epoch=yesterday)
        cleanup_size = delete_all(qry)
        logging.info("Cleanup %s timedout CleanupSolutionEvents" % cleanup_size)


class ReminderSolutionEvents(webapp2.RequestHandler):

    def get(self):
        run_job(_get_event_reminder_query, [], _process_event_reminder, [])


def _get_event_reminder_query():
    qry = db.GqlQuery("SELECT __key__ FROM EventReminder WHERE status = :status")
    qry.bind(status=EventReminder.STATUS_PENDING)
    return qry


def _process_event_reminder(reminder_key):
    reminder = EventReminder.get(reminder_key)

    service_user = reminder.service_user
    settings = get_solution_settings(service_user)
    event = Event.get_by_id(reminder.event_id, parent_key(service_user, settings.solution))

    if event and reminder.event_start_epoch in event.start_dates:
        now_ = now()
        if (now_ + reminder.remind_before) > (reminder.event_start_epoch + timezone_offset(settings.timezone)):
            if event.place:
                place = "\n@ " + event.place + "\n"
            else:
                place = ""

            dt = datetime.datetime.fromtimestamp(reminder.event_start_epoch)
            language = settings.main_language or DEFAULT_LANGUAGE
            when = "%s, %s" % (format_date(dt, format='full', locale=language) , format_time(dt, format='short', locale=language))
            reminderMessage = "Reminder:\n\nTitle:\n%s\n\nWhen:\n%s\n%s\nDescription:\n%s" % (event.title, when, place, event.description)
            main_branding = get_solution_main_branding(service_user)

            human_user = get_human_user_from_app_user(reminder.human_user)
            members = list()
            members.append(human_user.email())
            users.set_user(reminder.service_user)
            try:
                messaging.send(parent_key=None,
                            parent_message_key=None,
                            message=reminderMessage,
                            answers=[],
                            flags=Message.FLAG_ALLOW_DISMISS,
                            members=members,
                            branding=main_branding.branding_key,
                            tag=None,
                            service_identity=reminder.service_identity)
            finally:
                users.clear_user()

            reminder.status = EventReminder.STATUS_REMINDED
            reminder.put()
    else:
        reminder.status = EventReminder.STATUS_REMINDED
        reminder.put()


class SolutionSyncGoogleCalendarEvents(webapp2.RequestHandler):

    def get(self):
        run_job(_get_solution_calendars_to_sync_with_google_query, [], _process_solution_calendar_sync_google_events, [])


def _get_solution_calendars_to_sync_with_google_query():
    return db.GqlQuery("SELECT __key__ FROM SolutionCalendar WHERE google_sync_events = true")


def _process_solution_calendar_sync_google_events(sc_key):
    calendar = SolutionCalendar.get(sc_key)
    def trans():
        scgs = SolutionCalendarGoogleSync.get_by_key_name(calendar.service_user.email())
        if not scgs:
            scgs = SolutionCalendarGoogleSync(key_name=calendar.service_user.email())
            scgs.google_calendar_keys = map(str, SolutionCalendar.all(keys_only=True).ancestor(parent_key(calendar.service_user, calendar.solution)).filter("google_sync_events =", True))
            scgs.put()
        deferred.defer(update_events_from_google, calendar.service_user, calendar.calendar_id, _transactional=True)

    xg_on = db.create_transaction_options(xg=True)
    db.run_in_transaction_options(xg_on, trans)


def _get_solution_settings_query():
    return db.GqlQuery("SELECT __key__ from SolutionSettings WHERE put_identity_pending = TRUE")


def _publish_app_data(sln_settings):
    logging.debug('publishing app data for %s' % sln_settings.service_user)
    sln_settings.put_identity_pending = False
    sln_settings.put()
    main_branding = get_solution_main_branding(sln_settings.service_user)
    populate_identity_and_publish(sln_settings, main_branding.branding_key)


def _publish_events_app_data(sln_settings_key):
    sln_settings = SolutionSettings.get(sln_settings_key)
    _publish_app_data(sln_settings)


class SolutionEventsDataPublisher(webapp2.RequestHandler):

    def get(self):
        run_job(_get_solution_settings_query, [], _publish_events_app_data, [])
