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

from collections import defaultdict
import datetime
import json
import logging
import time

from babel.dates import format_date, format_time
from google.appengine.ext import db, deferred
from mcfw.rpc import serialize_complex_value
from rogerthat.bizz.job import run_job
from rogerthat.dal import parent_key, put_and_invalidate_cache
from rogerthat.models import Message, ServiceIdentity
from rogerthat.models.properties.keyvalue import KVStore
from rogerthat.rpc import users
from rogerthat.service.api import messaging
from rogerthat.translations import DEFAULT_LANGUAGE
from rogerthat.utils import now, get_epoch_from_datetime
from rogerthat.utils.app import get_human_user_from_app_user
from rogerthat.utils.models import delete_all
from rogerthat.utils.transactions import on_trans_committed, run_in_xg_transaction
from shop.constants import MAPS_QUEUE
from shop.models import Customer
from solutions.common.bizz import timezone_offset, OrganizationType, SolutionModule
from solutions.common.bizz.cityapp import get_uitdatabank_events, get_uitdatabank_events_detail
from solutions.common.bizz.events import update_events_from_google
from solutions.common.bizz.provisioning import populate_identity_and_publish
from solutions.common.dal import get_solution_settings, get_solution_main_branding
from solutions.common.models import SolutionSettings
from solutions.common.models.agenda import EventReminder, Event, SolutionCalendar, SolutionCalendarGoogleSync
from solutions.common.models.cityapp import CityAppProfile
from solutions.common.to import EventItemTO
import webapp2


try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


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


class CityAppSolutionGatherEvents(webapp2.RequestHandler):

    def get(self):
        run_job(_get_cityapps_query, [], _gather_events, [])


def _get_cityapps_query():
    return db.GqlQuery("SELECT __key__ FROM CityAppProfile")


def _gather_events(cap_key):

    def trans():
        si_key = ServiceIdentity.keyFromService(users.User(cap_key.parent().name()), ServiceIdentity.DEFAULT)
        cap, si = db.get([cap_key, si_key])
        if cap.gather_events:
            cap.gather_events.clear()
        else:
            cap.gather_events = KVStore(cap_key)
        stream = StringIO()
        json.dump([], stream)
        cap.gather_events[unicode(OrganizationType.NON_PROFIT)] = stream
        cap.gather_events[unicode(OrganizationType.PROFIT)] = stream
        cap.put()
        if cap.gather_events_enabled:
            on_trans_committed(run_job, _get_all_customers, [OrganizationType.NON_PROFIT, si.app_id],
                               _gather_events_for_customer, [cap_key, OrganizationType.NON_PROFIT])
            on_trans_committed(run_job, _get_all_customers, [OrganizationType.PROFIT, si.app_id],
                               _gather_events_for_customer, [cap_key, OrganizationType.PROFIT])
    run_in_xg_transaction(trans)


def _get_all_customers(organization_type, app_id):
    return Customer.all(keys_only=True).filter('organization_type =', organization_type).filter('app_ids =', app_id)


def _gather_events_for_customer(customer_key, cap_key, organization_type):
    customer = Customer.get(customer_key)
    if not customer.service_email:
        logging.debug('This customer has no service yet: %s', db.to_dict(customer))
        return
    sln_settings = get_solution_settings(customer.service_user)
    if SolutionModule.AGENDA not in sln_settings.modules:
        return
    sc = SolutionCalendar.get_by_id(sln_settings.default_calendar, parent_key(customer.service_user, sln_settings.solution))
    if not sc:
        return

    event_items = []
    for event in sc.events:
        event_item = EventItemTO.fromEventItemObject(event)
        event_item.calendar_id = organization_type
        event_items.append(event_item)

    if event_items:
        new_events = serialize_complex_value(event_items, EventItemTO, True)
        gather_events_key = u"%s" % organization_type
        def trans():
            cap = CityAppProfile.get(cap_key)
            stream = cap.gather_events.get(gather_events_key)
            if stream:
                json_list = json.load(stream)
            else:
                json_list = list()
            json_list.extend(new_events)
            stream = StringIO()
            json.dump(json_list, stream)
            cap.gather_events[gather_events_key] = stream
            cap.put()

        db.run_in_transaction(trans)


class CityAppSolutionEventsUitdatabank(webapp2.RequestHandler):

    def get(self):
        run_job(_get_cityapp_uitdatabank_enabled_query, [], _process_cityapp_uitdatabank_events, [1],
                worker_queue=MAPS_QUEUE)


def _get_cityapp_uitdatabank_enabled_query():
    return db.GqlQuery("SELECT __key__ FROM CityAppProfile WHERE uitdatabank_enabled = true")


def _process_cityapp_uitdatabank_events(cap_key, page):
    try:
        uitdatabank_actors = defaultdict(list)
        for sln_settings in SolutionSettings.all().filter("uitdatabank_actor_id !=", None):
            uitdatabank_actors[sln_settings.uitdatabank_actor_id].append(sln_settings)

        pagelength = 50
        cap = CityAppProfile.get(cap_key)
        if page == 1:
            run_time = now()
            services_to_update = set()
        else:
            run_time = cap.run_time
            services_to_update = set(cap.services_to_update)

        logging.info("process_cityapp_uitdatabank_events for %s page %s", cap.service_user, page)
        success, result = get_uitdatabank_events(cap, page, pagelength, cap.uitdatabank_last_query or None)
        if not success:
            logging.exception(result, _suppress=False)
            return

        sln_settings = get_solution_settings(cap.service_user)
        to_put = list()
        should_update_service = page != 1

        result_count = 0
        updated_events_count = 0
        for r in result:
            result_count += 1
            updated_events = _populate_uit_events(sln_settings, cap.uitdatabank_key, r['cdbid'], uitdatabank_actors)
            if updated_events:
                services_to_update.update((event.service_user for event in updated_events))
                updated_events_count += 1
                should_update_service = True
                to_put.extend(updated_events)

        def trans_update_cap():
            cap = db.get(cap_key)
            cap.run_time = run_time
            cap.services_to_update = list(services_to_update)
            cap.put()
            return cap
        cap = db.run_in_transaction(trans_update_cap)

        logging.debug("Added/updated %s events", updated_events_count)
        put_and_invalidate_cache(*to_put)
        if result_count != 0:
            deferred.defer(_process_cityapp_uitdatabank_events, cap_key, page + 1)
        else:
            def trans_set_last_query():
                cap = db.get(cap_key)
                cap.uitdatabank_last_query = cap.run_time
                cap.put()
                return cap
            cap = db.run_in_transaction(trans_set_last_query)

            if should_update_service:
                for service_user in cap.services_to_update:
                    sln_main_branding = get_solution_main_branding(service_user)
                    deferred.defer(populate_identity_and_publish,
                                   sln_settings if service_user == sln_settings.service_user else get_solution_settings(service_user),
                                   sln_main_branding.branding_key)
    except Exception, e:
        logging.exception(str(e), _suppress=False)


def _populate_uit_events(sln_settings, uitdatabank_key, external_id, uitdatabank_actors):
    logging.debug("process event with id: %s", external_id)
    detail_success, detail_result = get_uitdatabank_events_detail(uitdatabank_key, external_id)
    if not detail_success:
        logging.warn("Failed to get detail for cdbid: %s\n%s" % (external_id, detail_result))
        return None

    event_parent_key = parent_key(sln_settings.service_user, sln_settings.solution)
    event = Event.all().ancestor(event_parent_key).filter("source =", Event.SOURCE_UITDATABANK_BE).filter("external_id =", external_id).get()
    if not event:
        event = Event(parent=event_parent_key,
                      source=Event.SOURCE_UITDATABANK_BE,
                      external_id=external_id)

    event.calendar_id = sln_settings.default_calendar
    events = [event]

    uitdatabank_created_by = detail_result.get("createdby", None)
    logging.debug("uitdatabank_created_by: %s", uitdatabank_created_by)
    uitdatabank_lastupdated_by = detail_result.get("lastupdatedby", None)
    logging.debug("uitdatabank_lastupdated_by: %s", uitdatabank_lastupdated_by)

    if uitdatabank_created_by or uitdatabank_lastupdated_by:
        if uitdatabank_created_by and uitdatabank_created_by not in uitdatabank_actors:
            uitdatabank_actors[uitdatabank_created_by] = []
        if uitdatabank_lastupdated_by and uitdatabank_lastupdated_by not in uitdatabank_actors:
            uitdatabank_actors[uitdatabank_lastupdated_by] = []

        origanizer_settings = []
        if uitdatabank_created_by:
            origanizer_settings.extend(uitdatabank_actors[uitdatabank_created_by])
        if uitdatabank_lastupdated_by and uitdatabank_created_by != uitdatabank_lastupdated_by:
            origanizer_settings.extend(uitdatabank_actors[uitdatabank_lastupdated_by])

        logging.debug("len(origanizer_settings): %s", len(origanizer_settings))
        for organizer_sln_settings in origanizer_settings:
            organizer_event_parent_key = parent_key(organizer_sln_settings.service_user, organizer_sln_settings.solution)
            organizer_event = Event.all().ancestor(organizer_event_parent_key).filter("source =", Event.SOURCE_UITDATABANK_BE).filter("external_id =", external_id).get()
            if not organizer_event:
                organizer_event = Event(parent=organizer_event_parent_key,
                                    source=Event.SOURCE_UITDATABANK_BE,
                                    external_id=external_id)

            organizer_event.calendar_id = organizer_sln_settings.default_calendar
            events.append(organizer_event)

    r_event_detail = detail_result["eventdetails"]["eventdetail"]
    if not r_event_detail:
        logging.warn('Missing eventdetail')
        return None

    if isinstance(r_event_detail, list):
        for x in r_event_detail:
            if x['lang'] == sln_settings.main_language:
                r_event_detail = x
                break
        else:
            r_event_detail = r_event_detail[0]

    event_title = r_event_detail["title"]
    event_description = r_event_detail.get("shortdescription", r_event_detail.get("longdescription", u""))
    location = detail_result["location"]["address"]["physical"]
    if location.get("street", None):
        event_place = "%s %s, %s %s" % (location["street"], location.get("housenr", ""), location["zipcode"], location["city"])
    else:
        event_place = "%s %s" % (location["zipcode"], location["city"])

    r_organizer = detail_result.get('organiser')
    for k in ('actor', 'actordetails', 'actordetail', 'title'):
        if not r_organizer:
            break
        r_organizer = r_organizer.get(k)
    event_organizer = r_organizer

    r_timestamps = detail_result["calendar"].get("timestamps")
    if not r_timestamps:
        logging.debug("skipping event because we could not determine starttime")
        return None

    event_last_start_date = 0
    event_start_dates = list()
    event_end_dates = list()

    r_timestamp = r_timestamps["timestamp"]
    if isinstance(r_timestamp, dict):
        logging.debug("dict timestamp: %s", r_timestamp)
        r_timestart = r_timestamp.get("timestart", None)
        if not r_timestart:
            logging.info("Skipping event because it had no starttime")
            return None

        start_date = datetime.datetime.strptime("%s %s" % (r_timestamp["date"], r_timestart), "%Y-%m-%d %H:%M:%S")
        event_last_start_date = get_epoch_from_datetime(start_date)
        event_start_dates = [event_last_start_date]
        if r_timestamp.get("timeend", None):
            end_date = time.strptime(r_timestamp["timeend"], '%H:%M:%S')
            event_end_dates = [int(datetime.timedelta(hours=end_date.tm_hour, minutes=end_date.tm_min, seconds=end_date.tm_sec).total_seconds())]
        else:
            event_end_dates = [0]
    elif isinstance(r_timestamp, list):
        logging.debug("list timestamp: %s", r_timestamp)
        for r_ts in r_timestamp:
            if r_ts.get("timestart", None):
                start_date = datetime.datetime.strptime("%s %s" % (r_ts["date"], r_ts["timestart"]), "%Y-%m-%d %H:%M:%S")
                event_start_dates.append(get_epoch_from_datetime(start_date))
                if r_ts.get("timeend", None):
                    end_date = time.strptime(r_ts["timeend"], '%H:%M:%S')
                    event_end_dates.append(int(datetime.timedelta(hours=end_date.tm_hour, minutes=end_date.tm_min, seconds=end_date.tm_sec).total_seconds()))
                else:
                    event_end_dates.append(0)

        if event_start_dates:
            event_last_start_date = max(event_start_dates)
        else:
            logging.info("Skipping event because it had no starttime")
            return None
    else:
        logging.warn("could not guess timestamp %s", r_timestamp)
        return None

    for event in events:
        event.title = event_title
        event.description = event_description
        event.place = event_place
        event.organize = event_organizer
        event.last_start_date = event_last_start_date
        event.start_dates = event_start_dates
        event.end_dates = event_end_dates
        event.first_start_date = event.get_first_event_date()
    return events


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
