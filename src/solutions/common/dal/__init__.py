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

from google.appengine.ext import db
from typing import List, Dict

from mcfw.cache import cached
from mcfw.rpc import returns, arguments
from rogerthat.dal import parent_key, parent_key_unsafe
from rogerthat.dal.profile import get_profile_infos
from rogerthat.rpc import users
from rogerthat.service.api import friends
from rogerthat.utils.app import get_human_user_from_app_user
from solutions import SOLUTION_FLEX
from solutions.common import SOLUTION_COMMON
from solutions.common.models import SolutionSettings, SolutionMainBranding, RestaurantMenu, SolutionInboxMessage, \
    SolutionEmailSettings, SolutionIdentitySettings, SolutionNewsPublisher
from solutions.common.models.agenda import SolutionCalendar, Event
from solutions.common.models.group_purchase import SolutionGroupPurchaseSettings
from solutions.common.models.static_content import SolutionStaticContent
from solutions.common.to import SolutionUserKeyLabelTO, SolutionCalendarTO
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
    # type: (users.User) -> SolutionSettings
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


@returns(RestaurantMenu)
@arguments(service_user=users.User, solution=unicode)
def get_restaurant_menu(service_user, solution=None):
    """
    Returns:
        RestaurantMenu
    """
    solution = solution or get_solution_settings(service_user).solution
    return db.get(RestaurantMenu.create_key(service_user, solution))


@returns([SolutionNewsPublisher])
@arguments(service_user=users.User, solution=unicode)
def get_solution_news_publishers(service_user, solution):
    parent = parent_key(service_user, solution)
    news_publishers = SolutionNewsPublisher.all().ancestor(parent)
    return list(news_publishers)


@returns(SolutionNewsPublisher)
@arguments(app_user=users.User, service_user=users.User, solution=unicode)
def get_news_publisher_from_app_user(app_user, service_user, solution):
    key = SolutionNewsPublisher.createKey(app_user, service_user, solution)
    publisher = db.get(key)
    return publisher


def get_solution_calendars(service_user, solution):
    # type: (users.User, str) -> List[SolutionCalendar]
    return SolutionCalendar.list(service_user, solution)


def get_calendar_items(sln_settings, calendars):
    # type: (SolutionSettings, List[SolutionCalendar]) -> List[SolutionCalendarTO]
    return [SolutionCalendarTO.fromSolutionCalendar(sln_settings, calendar) for calendar in calendars]


@returns([Event])
@arguments(service_user=users.User)
def get_public_event_list(service_user):
    return Event.list_visible_by_source(service_user, SOLUTION_FLEX, Event.SOURCE_CMS)


@returns(Event)
@arguments(service_user=users.User, solution=unicode, id_=(int, long))
def get_event_by_id(service_user, solution, id_):
    # type: (users.User, str, int) -> Event
    return Event.create_key(id_, service_user, solution).get()


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
        sgps = SolutionGroupPurchaseSettings(
            key=SolutionGroupPurchaseSettings.create_key(service_user, solution), visible=True, branding_hash=None)
        sgps.put()
    return sgps


@cached(1)
@returns(SolutionEmailSettings)
@arguments()
def get_solution_email_settings():
    sln_email_settings = SolutionEmailSettings.get_by_key_name("SolutionEmailSettings")
    if not sln_email_settings:
        sln_email_settings = SolutionEmailSettings(key_name="SolutionEmailSettings")
    return sln_email_settings


def is_existing_friend(email, app_id, service_identity):
    # type: (str, str, str) -> bool
    status = friends.get_status(email, service_identity, app_id)
    return status.is_friend and not status.deactivated
