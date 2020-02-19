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
import logging
from datetime import datetime

import cloudstorage
from dateutil.relativedelta import relativedelta
from google.appengine.ext import ndb, db

from mcfw.utils import chunks
from rogerthat.bizz.branding import get_branding_cloudstorage_path
from rogerthat.bizz.job import run_job
from rogerthat.consts import MIGRATION_QUEUE
from rogerthat.models import Branding, MessageFlowDesign, MessageFlowDesignBackup, ServiceInteractionDef, ServiceRole
from rogerthat.rpc import users
from rogerthat.service.api.system import delete_role, get_menu, delete_menu_item
from rogerthat.utils.cloud_tasks import create_task, schedule_tasks
from solutions.common.bizz import timezone_offset
from solutions.common.bizz.events import upload_event_image, index_events
from solutions.common.dal import get_solution_settings
from solutions.common.models import SolutionSettings
from solutions.common.models.agenda import Event, EventCalendarType, EventPeriod, EventDate
from solutions.common.models.cityapp import UitdatabankSettings


def migrate_1(dry_run=True):
    # Deletes all uit and google calendar events (will be synced later)
    # Moves event images to cloudstorage and updates event periods
    to_delete = []
    to_update = []
    settings_to_update = UitdatabankSettings.query()  # type: list[UitdatabankSettings]
    for event in Event.query():
        if event.source in (Event.SOURCE_UITDATABANK_BE, Event.SOURCE_GOOGLE_CALENDAR):
            to_delete.append(event.key)
        else:
            to_update.append(event)
    if dry_run:
        return 'Events to update: %s\nEvents to delete: %s\nSettings to update: %s' % (
            len(to_update), len(to_delete), settings_to_update.count())
    ndb.delete_multi(to_delete)
    for setting in settings_to_update:
        setting.cron_sync_time = None
        setting.cron_run_time = None
    ndb.put_multi(settings_to_update)
    schedule_tasks([create_task(_migrate_event, model.key) for model in to_update], MIGRATION_QUEUE)


def migrate_2(dry_run=True):
    # Cleanup unused/deleted models
    guests = ndb.Query(kind='EventGuest').fetch(None, keys_only=True)
    reminders = ndb.Query(kind='EventReminder').fetch(None, keys_only=True)
    calendar_admins = ndb.Query(kind='SolutionCalendarAdmin').fetch(None, keys_only=True)

    if not dry_run:
        ndb.delete_multi(guests)
        ndb.delete_multi(reminders)
        ndb.delete_multi(calendar_admins)
    return '%sGuests: %s\nReminders:%s\nCalendar admins: %s' % ('' if dry_run else 'Deleted ',
                                                                len(guests),
                                                                len(reminders),
                                                                len(calendar_admins))


def migrate_3(dry_run=True):
    # Clean up all old brandings to save some storage space
    branding_keys = _get_brandings()
    if dry_run:
        return 'Brandings to delete: %s' % branding_keys.count(None)
    run_job(_get_brandings, [], _delete_branding, [])


def migrate_4():
    run_job(_get_all_sln_settings, [], _cleanup_menu, [])


def migrate_5(dry_run=True):
    # Delete message flow designs and qr codes related to agenda
    to_delete = []
    tasks = []
    for key in MessageFlowDesign.all(keys_only=True).filter('name', 'events_connect_via_scan'):
        to_delete.append(key)
        tasks.append(create_task(delete_design_backups, key))
    for model in ServiceInteractionDef.all():  # type: ServiceInteractionDef
        if model.tag.startswith('agenda.connect_via_scan'):
            to_delete.append(model.key())
    result = {}
    if dry_run:
        for key in to_delete:
            if key.kind() not in result:
                result[key.kind()] = 1
            else:
                result[key.kind()] += 1
        return result
    else:
        for keys in chunks(to_delete, db.datastore_rpc.BaseConnection.MAX_DELETE_KEYS):
            db.delete(keys)
        schedule_tasks(tasks, MIGRATION_QUEUE)


def migrate_6():
    run_job(_list_agenda_roles, [], _delete_role, [])


def _get_all_sln_settings():
    return SolutionSettings.all(keys_only=True)


def _cleanup_menu(key):
    service_user = users.User(key.name())
    with users.set_user(service_user):
        menu = get_menu()
        for item in menu.items:
            if item.tag == 'agenda.new_event':
                delete_menu_item(item.coords)


def _list_agenda_roles():
    return ServiceRole.all(keys_only=True).filter('name', 'agenda.new_event')


def _delete_role(key):
    role = db.get(key)  # type: ServiceRole
    with users.set_user(role.service_user):
        delete_role(role.role_id, cleanup_members=True)


def delete_design_backups(mfd_key):
    keys = MessageFlowDesignBackup.all(keys_only=True).ancestor(mfd_key).fetch(None)
    if keys:
        logging.info('Deleted %s mfd backups', len(keys))
        db.delete(keys)


def _get_brandings():
    return Branding.all(keys_only=True).filter('description', 'Events App')


def _delete_branding(branding_key):
    branding = db.get(branding_key)  # type: Branding
    gcs_path = get_branding_cloudstorage_path(branding.hash, branding.user)
    try:
        cloudstorage.delete(gcs_path)
    except cloudstorage.NotFoundError:
        pass
    db.delete(branding_key)


def _migrate_event(event_key):
    event = event_key.get()  # type: Event
    sln_settings = get_solution_settings(event.service_user)
    offset = timezone_offset(sln_settings.timezone)
    if event.picture:
        upload_event_image(event.picture, event)
        event.picture = None
        event.picture_version = None
    if event.start_dates:
        if len(event.start_dates) == 1:
            event.calendar_type = EventCalendarType.SINGLE
            event.start_date = datetime.utcfromtimestamp(event.start_dates[0] + offset)
            event.start_date = datetime.utcfromtimestamp(event.start_dates[0] + offset)
            end_date = event.start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            event.end_date = end_date + relativedelta(seconds=event.end_dates[0] + offset)
        else:
            event.calendar_type = EventCalendarType.MULTIPLE
            event.periods = []
            for start_timestamp, end_seconds in zip(event.start_dates, event.end_dates):
                start_date = datetime.utcfromtimestamp(start_timestamp + offset)
                end_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                event.periods.append(EventPeriod(
                    start=EventDate(datetime=start_date),
                    end=EventDate(datetime=end_date + relativedelta(seconds=end_seconds + offset)),
                ))
                event.start_date = event.periods[0].start.datetime
                event.end_date = event.periods[-1].end.datetime
        event.put()
        index_events([event])
