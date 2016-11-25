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

from google.appengine.ext import db

from mcfw.cache import cached
from mcfw.rpc import returns, arguments
from rogerthat.dal import parent_key, generator, parent_key_unsafe
from rogerthat.rpc import users
from solutions.common import SOLUTION_COMMON
from solutions.common.models import SolutionSettings, SolutionMainBranding, SolutionLogo, \
    RestaurantMenu, SolutionScheduledBroadcast, SolutionInboxMessage, SolutionEmailSettings, SolutionAvatar, \
    SolutionIdentitySettings
from solutions.common.models.agenda import Event, EventReminder, SolutionCalendar, SolutionCalendarAdmin
from solutions.common.models.group_purchase import SolutionGroupPurchaseSettings
from solutions.common.models.static_content import SolutionStaticContent
from solutions.common.utils import is_default_service_identity, create_service_identity_user_wo_default


@returns(int)
@arguments(service_user=users.User, service_identity=unicode)
def count_unread_solution_inbox_messages(service_user, service_identity):
    service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
    ancestor = parent_key_unsafe(service_identity_user, SOLUTION_COMMON)
    qry = SolutionInboxMessage.all(keys_only=True).ancestor(ancestor).filter('parent_message_key =', None)
    qry.filter('deleted =', False)
    qry.filter('trashed =', False)
    qry.filter('read =', False)
    qry.filter('starred =', False)
    return qry.count(None)

@returns(tuple)
@arguments(service_user=users.User, service_identity=unicode, count=(int, long), name=unicode, cursor=unicode)
def get_solution_inbox_messages(service_user, service_identity, count, name, cursor=None):
    service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
    ancestor = parent_key_unsafe(service_identity_user, SOLUTION_COMMON)
    qry = SolutionInboxMessage.all().with_cursor(cursor).ancestor(ancestor).filter('parent_message_key =', None)
    qry.filter('deleted =', False)
    if name == SolutionInboxMessage.INBOX_NAME_UNREAD:
        qry.filter('trashed =', False)
        qry.filter('read =', False)
        qry.filter('starred =', False)
    elif name == SolutionInboxMessage.INBOX_NAME_STARRED:
        qry.filter('trashed =', False)
        qry.filter('starred =', True)
    elif name == SolutionInboxMessage.INBOX_NAME_READ:
        qry.filter('trashed =', False)
        qry.filter('read =', True)
        qry.filter('starred =', False)
    elif name == SolutionInboxMessage.INBOX_NAME_TRASH:
        qry.filter('trashed =', True)
    else:
        return None
    qry.order('-last_timestamp')
    messages = qry.fetch(count)
    cursor_ = qry.cursor()
    has_more = False
    if len(messages) != 0:
        qry.with_cursor(cursor_)
        if len(qry.fetch(1)) > 0:
            has_more = True

    return unicode(cursor_), messages, has_more

@returns(SolutionSettings)
@arguments(service_user=users.User)
def get_solution_settings(service_user):
    """
    Args:
        service_user (users.User)
    Returns:
        SolutionSettings
    """
    return SolutionSettings.get(SolutionSettings.create_key(service_user))

@returns(SolutionIdentitySettings)
@arguments(service_user=users.User, service_identity=unicode)
def get_solution_identity_settings(service_user, service_identity):
    return SolutionIdentitySettings.get(SolutionIdentitySettings.create_key(service_user, service_identity))

def get_solution_settings_or_identity_settings(sln_settings, service_identity):
    if is_default_service_identity(service_identity):
        return sln_settings
    else:
        return get_solution_identity_settings(sln_settings.service_user, service_identity)

@returns(SolutionMainBranding)
@arguments(service_user=users.User)
def get_solution_main_branding(service_user):
    return SolutionMainBranding.get(SolutionMainBranding.create_key(service_user))

@returns(SolutionLogo)
@arguments(service_user=users.User)
def get_solution_logo(service_user):
    return SolutionLogo.get(SolutionLogo.create_key(service_user))

@returns(SolutionAvatar)
@arguments(service_user=users.User)
def get_solution_avatar(service_user):
    return SolutionAvatar.get(SolutionAvatar.create_key(service_user))


@returns(RestaurantMenu)
@arguments(service_user=users.User, solution=unicode)
def get_restaurant_menu(service_user, solution=None):
    """
    Returns:
        RestaurantMenu
    """
    solution = solution or get_solution_settings(service_user).solution
    return db.get(RestaurantMenu.create_key(service_user, solution))


@returns([SolutionCalendar])
@arguments(service_user=users.User, solution=unicode, filter_broadcast_disabled=bool)
def get_solution_calendars(service_user, solution, filter_broadcast_disabled=False):
    if filter_broadcast_disabled:
        qry = SolutionCalendar.gql("WHERE ANCESTOR IS :ancestor AND deleted=False AND broadcast_enabled=True")
    else:
        qry = SolutionCalendar.gql("WHERE ANCESTOR IS :ancestor AND deleted=False")
    qry.bind(ancestor=parent_key(service_user, solution))
    return generator(qry.run())

@returns([SolutionCalendarAdmin])
@arguments(service_user=users.User, solution=unicode)
def get_admins_of_solution_calendars(service_user, solution):
    deleted_calendar_keys = [c for c in SolutionCalendar.all(keys_only=True).ancestor(parent_key(service_user, solution)).filter("deleted =", True)]

    admins = []
    for admin in SolutionCalendarAdmin.all().ancestor(parent_key(service_user, solution)):
        if admin.calendar_key not in deleted_calendar_keys:
            admins.append(admin)

    return admins

@returns([SolutionCalendar])
@arguments(service_user=users.User, solution=unicode, app_user=users.User, filter_deleted=bool)
def get_solution_calendars_for_user(service_user, solution, app_user, filter_deleted=True):
    calendars = []
    for calendar in db.get([ c.calendar_key for c in SolutionCalendarAdmin.all().ancestor(parent_key(service_user, solution)).filter("app_user =", app_user)]):
        if not(filter_deleted and calendar.deleted):
            calendars.append(calendar)
    return calendars

@returns([long])
@arguments(service_user=users.User, solution=unicode, app_user=users.User, filter_deleted=bool)
def get_solution_calendar_ids_for_user(service_user, solution, app_user, filter_deleted=True):
    calendar_ids = []
    for calendar in get_solution_calendars_for_user(service_user, solution, app_user, filter_deleted):
        calendar_ids.append(calendar.calendar_id)
    return calendar_ids

@returns([Event])
@arguments(service_user=users.User, solution=unicode)
def get_event_list(service_user, solution):
    qry = Event.gql("WHERE ANCESTOR IS :ancestor AND deleted=False")
    qry.bind(ancestor=parent_key_unsafe(service_user, solution))
    return generator(qry.run())

@returns([Event])
@arguments(service_user=users.User, solution=unicode)
def get_public_event_list(service_user, solution):
    qry = Event.gql("WHERE ANCESTOR IS :ancestor AND deleted=False AND source = :source")
    qry.bind(ancestor=parent_key(service_user, solution), source=Event.SOURCE_CMS)
    return generator(qry.run())

@returns(Event)
@arguments(service_user=users.User, solution=unicode, id_=(int, long))
def get_event_by_id(service_user, solution, id_):
    return Event.get_by_id(id_, parent_key(service_user, solution))

@returns(bool)
@arguments(app_user=users.User, event_id=(int, long), event_start_epoch=(int, long), remind_before=(int, long))
def is_reminder_set(app_user, event_id, event_start_epoch, remind_before):
    return len(EventReminder.all().filter("event_id =", event_id).filter("human_user =", app_user).filter("event_start_epoch =", event_start_epoch).filter("remind_before =", remind_before).fetch(1)) > 0


@returns([SolutionStaticContent])
@arguments(service_user=users.User)
def get_static_content_list(service_user):
    return SolutionStaticContent.list_non_deleted(service_user)


@returns([db.Key])
@arguments(service_user=users.User, solution=unicode)
def get_static_content_keys(service_user, solution):
    return [sc_key for sc_key in SolutionStaticContent.all(keys_only=True).ancestor(parent_key(service_user, solution))]

@returns(SolutionGroupPurchaseSettings)
@arguments(service_user=users.User, solution=unicode)
def get_solution_group_purchase_settings(service_user, solution):
    sgps = SolutionGroupPurchaseSettings.get(SolutionGroupPurchaseSettings.create_key(service_user, solution))
    if not sgps:
        sgps = SolutionGroupPurchaseSettings(key=SolutionGroupPurchaseSettings.create_key(service_user, solution), visible=True, branding_hash=None)
        sgps.put()
    return sgps


@returns([SolutionScheduledBroadcast])
@arguments(service_user=users.User)
def get_solution_scheduled_broadcasts(service_user):
    return SolutionScheduledBroadcast.all().ancestor(parent_key(service_user, SOLUTION_COMMON)).filter("deleted =", False).order("broadcast_epoch")

@cached(1)
@returns(SolutionEmailSettings)
@arguments()
def get_solution_email_settings():
    sln_email_settings = SolutionEmailSettings.get_by_key_name("SolutionEmailSettings")
    if not sln_email_settings:
        sln_email_settings = SolutionEmailSettings(key_name="SolutionEmailSettings")
    return sln_email_settings
