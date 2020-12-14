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

from __future__ import unicode_literals

import base64
import logging
import re
from collections import defaultdict
from datetime import datetime
from types import NoneType

import cloudstorage
from babel import Locale
from babel.numbers import format_currency
from dateutil.relativedelta import relativedelta
from google.appengine.api import urlfetch
from google.appengine.api.taskqueue import taskqueue
from google.appengine.ext import db, deferred, ndb

from mcfw.consts import MISSING, REST_TYPE_TO
from mcfw.exceptions import HttpBadRequestException, HttpForbiddenException
from mcfw.properties import azzert, get_members
from mcfw.restapi import rest, GenericRESTRequestHandler
from mcfw.rpc import returns, arguments, serialize_complex_value
from rogerthat.bizz.forms import FormNotFoundException
from rogerthat.bizz.gcs import get_serving_url
from rogerthat.bizz.maps.services.places import get_place_types
from rogerthat.bizz.rtemail import EMAIL_REGEX
from rogerthat.bizz.service import AvatarImageNotSquareException, InvalidValueException
from rogerthat.consts import DEBUG, SCHEDULED_QUEUE
from rogerthat.dal import parent_key, put_and_invalidate_cache, parent_key_unsafe, put_in_chunks, parent_ndb_key
from rogerthat.dal.profile import get_user_profile, get_profile_key, get_service_profile
from rogerthat.models import ServiceIdentity
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from rogerthat.rpc.users import get_current_session
from rogerthat.service.api import system
from rogerthat.settings import get_server_settings
from rogerthat.to import ReturnStatusTO, RETURNSTATUS_TO_SUCCESS
from rogerthat.to.friends import FriendListResultTO
from rogerthat.to.messaging import AttachmentTO, BaseMemberTO
from rogerthat.to.service import UserDetailsTO
from rogerthat.translations import DEFAULT_LANGUAGE
from rogerthat.utils.app import get_human_user_from_app_user, sanitize_app_user, \
    get_app_id_from_app_user, get_app_user_tuple
from rogerthat.utils.channel import send_message
from rogerthat.utils.service import create_service_identity_user, remove_slash_default
from shop.bizz import add_service_admin, get_service_admins
from shop.dal import get_customer, get_customer_signups
from shop.exceptions import InvalidEmailFormatException
from shop.models import Customer, CustomerSignup
from solutions import translate as common_translate
from solutions.common.bizz import get_next_free_spots_in_service_menu, common_provision, timezone_offset, \
    broadcast_updates_pending, SolutionModule, delete_file_blob, create_file_blob, \
    create_news_publisher, delete_news_publisher, enable_or_disable_solution_module, \
    validate_enable_or_disable_solution_module, OrganizationType, get_organization_type, validate_before_provision, \
    auto_publish
from solutions.common.bizz.branding_settings import save_branding_settings
from solutions.common.bizz.events import update_events_from_google, get_google_authenticate_url, get_google_calendars
from solutions.common.bizz.group_purchase import save_group_purchase, delete_group_purchase, broadcast_group_purchase, \
    new_group_purchase_subscription
from solutions.common.bizz.images import upload_file, list_files
from solutions.common.bizz.inbox import send_statistics_export_email, send_inbox_info_messages_to_services
from solutions.common.bizz.loyalty import update_user_data_admins
from solutions.common.bizz.menu import _put_default_menu, get_menu_item_qr_url
from solutions.common.bizz.messaging import validate_broadcast_url, send_reply, delete_all_trash
from solutions.common.bizz.paddle import get_paddle_info, populate_info_from_paddle
from solutions.common.bizz.repair import send_message_for_repair_order, delete_repair_order
from solutions.common.bizz.sandwich import ready_sandwich_order, delete_sandwich_order, reply_sandwich_order
from solutions.common.bizz.service import new_inbox_message, send_inbox_message_update, set_customer_signup_status
from solutions.common.bizz.settings import save_settings, set_logo, set_avatar, save_rss_urls, get_service_info
from solutions.common.bizz.static_content import put_static_content as bizz_put_static_content, delete_static_content
from solutions.common.consts import TRANSLATION_MAPPING, OCA_FILES_BUCKET, AUTO_PUBLISH_MINUTES
from solutions.common.dal import get_solution_settings, get_static_content_list, get_solution_group_purchase_settings, \
    get_solution_calendars, get_solution_inbox_messages, \
    get_solution_identity_settings, get_solution_settings_or_identity_settings, \
    get_solution_news_publishers, is_existing_friend
from solutions.common.dal.appointment import get_solution_appointment_settings
from solutions.common.dal.repair import get_solution_repair_orders, get_solution_repair_settings
from solutions.common.integrations.jcc.jcc_appointments import get_jcc_settings, save_jcc_settings
from solutions.common.integrations.qmatic.qmatic import get_qmatic_settings, save_qmatic_settings
from solutions.common.localizer import translations
from solutions.common.models import SolutionBrandingSettings, SolutionSettings, SolutionInboxMessage, \
    SolutionRssScraperSettings
from solutions.common.models.agenda import SolutionCalendar
from solutions.common.models.appointment import SolutionAppointmentWeekdayTimeframe, SolutionAppointmentSettings
from solutions.common.models.cityapp import PaddleSettings, PaddleMapping, PaddleOrganizationalUnits
from solutions.common.models.forms import OcaForm
from solutions.common.models.group_purchase import SolutionGroupPurchase
from solutions.common.models.repair import SolutionRepairSettings
from solutions.common.models.sandwich import SandwichType, SandwichTopping, SandwichOption, SandwichSettings, \
    SandwichOrder
from solutions.common.models.static_content import SolutionStaticContent
from solutions.common.to import ServiceMenuFreeSpotsTO, SolutionStaticContentTO, SolutionSettingsTO, \
    MenuTO, EventItemTO, PublicEventItemTO, SolutionAppointmentWeekdayTimeframeTO, BrandingSettingsTO, \
    SolutionRepairOrderTO, SandwichSettingsTO, SandwichOrderTO, SolutionGroupPurchaseTO, \
    SolutionGroupPurchaseSettingsTO, SolutionCalendarTO, SolutionInboxForwarder, SolutionInboxesTO, \
    SolutionInboxMessageTO, SolutionAppointmentSettingsTO, \
    SolutionRepairSettingsTO, UrlReturnStatusTO, ImageReturnStatusTO, SolutionUserKeyLabelTO, \
    SolutionCalendarWebTO, BrandingSettingsAndMenuItemsTO, ServiceMenuItemWithCoordinatesTO, \
    ServiceMenuItemWithCoordinatesListTO, SolutionGoogleCalendarStatusTO, PictureReturnStatusTO, \
    AppUserRolesTO, CustomerSignupTO, SolutionRssSettingsTO, UploadedImageTO, CreateEventItemTO
from solutions.common.to.forms import GcsFileTO
from solutions.common.to.paddle import PaddleSettingsTO, PaddleSettingsServicesTO, SimpleServiceTO
from solutions.common.to.statistics import StatisticsResultTO
from solutions.common.utils import is_default_service_identity, create_service_identity_user_wo_default


@rest("/solutions/common/public/menu/load", "get", authenticated=False)
@returns(dict)
@arguments(service_user_email=unicode)
def public_load_menu(service_user_email):
    from solutions.common.dal import get_restaurant_menu

    if service_user_email in (None, MISSING):
        logging.debug("Could not load public menu (service_user_email None|MISSING)")
        return None

    service_user = users.User(service_user_email)
    sln_settings = get_solution_settings(service_user)
    if not sln_settings:
        logging.debug("Could not load public menu for: %s (SolutionSettings==None)", service_user_email)
        return None

    menu = get_restaurant_menu(service_user, sln_settings.solution)
    if not menu:
        logging.debug("Could not load public menu for: %s (Menu==None)", service_user_email)
        return None

    menu = serialize_complex_value(MenuTO.fromMenuObject(menu), MenuTO, False)
    # convert prices from long to unicode
    for category in menu['categories']:
        for item in category['items']:
            item['price'] = format_currency((item['price'] or 0) / 100.0, sln_settings.currency, '#,##0.00',
                                            locale=sln_settings.main_language)
    return menu


@rest("/solutions/common/public/events/load", "get", authenticated=False)
@returns([PublicEventItemTO])
@arguments(service_user_email=unicode)
def public_load_events(service_user_email):
    from solutions.common.dal import get_public_event_list

    if service_user_email and service_user_email != MISSING:
        service_user = users.User(service_user_email)
        return [PublicEventItemTO.fromPublicEventItemObject(e) for e in get_public_event_list(service_user)]
    else:
        logging.debug("Could not load public events (service_user_email None|MISSING)")
    return None


@rest("/solutions/common/public/group_purchase/picture", "get", authenticated=False, silent_result=True)
@returns(PictureReturnStatusTO)
@arguments(service_user_email=unicode, group_purchase_id=long, picture_version=long, service_identity=unicode)
def public_group_purchase_picture(service_user_email, group_purchase_id, picture_version=0, service_identity=None):
    service_user = users.User(service_user_email)
    settings = get_solution_settings(service_user)
    service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
    sgp = SolutionGroupPurchase.get_by_id(group_purchase_id,
                                          parent_key_unsafe(service_identity_user, settings.solution))
    if not sgp or not sgp.picture:
        return PictureReturnStatusTO.create(False, None)

    response = GenericRESTRequestHandler.getCurrentResponse()
    response.headers['Cache-Control'] = "public, max-age=31536000"  # Cache forever (1 year)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return PictureReturnStatusTO.create(picture=unicode(sgp.picture))


@rest("/common/service_menu/get_free_spots", "get", read_only_access=True)
@returns(ServiceMenuFreeSpotsTO)
@arguments(count=int)
def get_free_spots(count=10):
    service_user = users.get_current_user()
    sm = system.get_menu()
    all_taken_coords = [item.coords for item in sm.items]
    static_content_items = SolutionStaticContent.list_changed(service_user)
    for sc in static_content_items:
        if sc.deleted or not sc.visible:
            try:
                all_taken_coords.remove(sc.coords)
            except ValueError:
                pass
        else:  # not deleted and visible
            all_taken_coords.append(sc.coords)
    spots = get_next_free_spots_in_service_menu(all_taken_coords, count)
    return ServiceMenuFreeSpotsTO.fromList(spots)


@rest("/common/static_content/load", "get", read_only_access=True, silent_result=True)
@returns([SolutionStaticContentTO])
@arguments()
def get_static_content():
    service_user = users.get_current_user()
    static_contents = sorted(get_static_content_list(service_user), key=lambda m: tuple(reversed(m.coords)))
    return [SolutionStaticContentTO.fromModel(sc) for sc in static_contents]


@rest("/common/static_content/put", "post")
@returns(ReturnStatusTO)
@arguments(static_content=SolutionStaticContentTO)
def put_static_content(static_content):
    service_user = users.get_current_user()
    try:
        bizz_put_static_content(service_user, static_content)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@rest("/common/static_content/delete", "post")
@returns(ReturnStatusTO)
@arguments(static_content_id=(int, long, NoneType))
def rest_delete_static_content(static_content_id=None):
    service_user = users.get_current_user()
    try:
        delete_static_content(service_user, static_content_id)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@rest("/common/inbox/load/all", "get", read_only_access=True)
@returns([SolutionInboxesTO])
@arguments()
def inbox_load_all():
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    sln_settings = get_solution_settings(service_user)
    service_info = get_service_info(service_user, service_identity)

    unread_cursor, unread_messages, unread_has_more = get_solution_inbox_messages(service_user,
                                                                                  service_identity,
                                                                                  10,
                                                                                  SolutionInboxMessage.INBOX_NAME_UNREAD)
    starred_cursor, starred_messages, starred_has_more = get_solution_inbox_messages(service_user,
                                                                                     service_identity,
                                                                                     10,
                                                                                     SolutionInboxMessage.INBOX_NAME_STARRED)
    read_cursor, read_messages, read_has_more = get_solution_inbox_messages(service_user,
                                                                            service_identity,
                                                                            10,
                                                                            SolutionInboxMessage.INBOX_NAME_READ)
    trash_cursor, trash_messages, trash_has_more = get_solution_inbox_messages(service_user,
                                                                               service_identity,
                                                                               10,
                                                                               SolutionInboxMessage.INBOX_NAME_TRASH)

    inboxes = [(SolutionInboxMessage.INBOX_NAME_UNREAD, unread_cursor, unread_messages, unread_has_more),
               (SolutionInboxMessage.INBOX_NAME_STARRED, starred_cursor, starred_messages, starred_has_more),
               (SolutionInboxMessage.INBOX_NAME_READ, read_cursor, read_messages, read_has_more),
               (SolutionInboxMessage.INBOX_NAME_TRASH, trash_cursor, trash_messages, trash_has_more)]

    return [SolutionInboxesTO.fromModel(name, cursor, messages, has_more, sln_settings, service_info, True) for
            name, cursor, messages, has_more in inboxes]


@rest("/common/inbox/load/more", "get", read_only_access=True)
@returns(SolutionInboxesTO)
@arguments(name=unicode, count=(int, long), cursor=unicode)
def inbox_load_more(name, count, cursor):
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    sln_settings = get_solution_settings(service_user)
    service_info = get_service_info(service_user, service_identity)
    cursor_, messages, has_more = get_solution_inbox_messages(service_user, service_identity, count, name, cursor)
    return SolutionInboxesTO.fromModel(name, cursor_, messages, has_more, sln_settings, service_info, True)


@rest("/common/inbox/load/detail", "get", read_only_access=True)
@returns([SolutionInboxMessageTO])
@arguments(key=unicode)
def inbox_load_detail(key):
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    sln_settings = get_solution_settings(service_user)
    sim = SolutionInboxMessage.get(key)
    messages = [sim]
    messages.extend(sim.get_child_messages())
    service_info = get_service_info(service_user, service_identity)
    return [SolutionInboxMessageTO.fromModel(message, sln_settings, service_info, False) for message in messages]


@rest("/common/inbox/message/update/reply", "post")
@returns(ReturnStatusTO)
@arguments(key=unicode, message=unicode)
def inbox_message_update_reply(key, message):
    service_user = users.get_current_user()
    try:
        send_reply(service_user, key, message)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@rest("/common/inbox/message/forward", "post")
@returns(ReturnStatusTO)
@arguments(key=unicode, to_email=unicode)
def inbox_message_forward(key, to_email):
    """Only city service to community service"""
    try:
        sim = SolutionInboxMessage.get(key)
        to_service_user = users.User(to_email)
        to_sln_settings = get_solution_settings(to_service_user)
        new_sim = new_inbox_message(to_sln_settings, sim.message,
                                    user_details=sim.sender.to_user_details(),
                                    category=sim.category,
                                    category_key=sim.category_key,
                                    reply_enabled=sim.reply_enabled,
                                    send_to_forwarders=True)
        send_inbox_message_update(to_sln_settings, new_sim)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as ex:
        return ReturnStatusTO.create(False, ex.message)


@rest("/common/inbox/message/update/starred", "post")
@returns(ReturnStatusTO)
@arguments(key=unicode, starred=bool)
def inbox_message_update_starred(key, starred):
    inbox_message = SolutionInboxMessage.get(key)
    inbox_message.starred = starred
    inbox_message.put()
    return _after_inbox_message_updated(inbox_message)


@rest("/common/inbox/message/update/read", "post")
@returns(ReturnStatusTO)
@arguments(key=unicode, read=bool)
def inbox_message_update_read(key, read):
    inbox_message = SolutionInboxMessage.get(key)
    inbox_message.read = read
    inbox_message.put()
    return _after_inbox_message_updated(inbox_message)


def _after_inbox_message_updated(inbox_message):
    # type: (SolutionInboxMessage) -> ReturnStatusTO
    try:
        service_user = users.get_current_user()
        service_identity = users.get_current_session().service_identity
        sln_settings = get_solution_settings(service_user)
        service_info = get_service_info(service_user, service_identity)
        send_message(service_user, u"solutions.common.messaging.update",
                     service_identity=service_identity,
                     message=SolutionInboxMessageTO.fromModel(inbox_message, sln_settings, service_info,
                                                              True).to_dict())
        deferred.defer(update_user_data_admins, service_user, service_identity)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@rest("/common/inbox/message/update/trashed", "post")
@returns(ReturnStatusTO)
@arguments(key=unicode, trashed=bool)
def inbox_message_update_trashed(key, trashed):
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    sln_settings = get_solution_settings(service_user)
    service_info = get_service_info(service_user, service_identity)
    try:
        sim = SolutionInboxMessage.get(key)
        if trashed and sim.trashed:
            sim.deleted = True
        sim.trashed = trashed
        sim.put()
        send_message(service_user, u"solutions.common.messaging.update",
                     service_identity=service_identity,
                     message=SolutionInboxMessageTO.fromModel(sim, sln_settings, service_info, True).to_dict())
        if not sim.deleted:
            deferred.defer(update_user_data_admins, service_user, service_identity)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@rest("/common/inbox/message/update/deleted", "post")
@returns(ReturnStatusTO)
@arguments()
def inbox_message_update_deleted():
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    try:
        delete_all_trash(service_user, service_identity)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@rest("/common/inbox/messages/export", "get")
@returns(ReturnStatusTO)
@arguments(email=unicode)
def export_inbox_messages(email=''):
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    sln_settings = get_solution_settings(service_user)
    try:
        send_statistics_export_email(service_user, service_identity, email, sln_settings)
        return RETURNSTATUS_TO_SUCCESS
    except InvalidEmailFormatException as ex:
        error_msg = common_translate(sln_settings.main_language, 'invalid_email_format',
                                     email=ex.email)
        return ReturnStatusTO.create(False, error_msg)


@rest('/common/inbox/services', 'post')
@returns()
@arguments(organization_types=[int], message=unicode)
def api_send_message_to_services(organization_types=None, message=None):
    service_user = users.get_current_user()
    sln_settings = get_solution_settings(service_user)

    def _validation_err(translation_key):
        field = common_translate(sln_settings.main_language, translation_key)
        raise HttpBadRequestException(
            '%s: %s' % (field, common_translate(sln_settings.main_language, 'this_field_is_required')))

    if SolutionModule.CITY_APP not in sln_settings.modules:
        raise HttpForbiddenException()

    if not organization_types:
        _validation_err('organization_type')
    message = (message or '').strip()
    if not message:
        _validation_err('message')
    services = []
    service_profile = get_service_profile(service_user)
    for customer in Customer.list_by_community_id(service_profile.community_id):
        if customer.organization_type in organization_types:
            # Don't send message to self
            if customer.service_email and customer.service_email != service_user.email():
                services.append(customer.service_user)
    send_inbox_info_messages_to_services(services, service_user, message, SolutionInboxMessage.CATEGORY_CITY_MESSAGE)


@rest('/common/news/rss', 'get', read_only_access=True)
@returns(SolutionRssSettingsTO)
@arguments()
def rest_get_news_rss_feeds():
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    rss_settings = SolutionRssScraperSettings.create_key(service_user, service_identity).get()
    return SolutionRssSettingsTO.from_model(rss_settings)


@rest("/common/broadcast/rss/validate", "get", read_only_access=True, silent_result=True)
@returns(dict)
@arguments(url=unicode)
def rest_validate_rss_feed(url):
    from solutions.common.cron.news.rss import parse_rss_items
    try:
        response = urlfetch.fetch(url, deadline=10)  # type: urlfetch._URLFetchResult
        items, _ = parse_rss_items(response.content, url)
    except Exception as e:
        logging.exception('Failed to validate url')
        return {'exception': e.message}

    return {'items': [{
        'title': item.title,
        'url': item.url,
        'guid': item.guid,
        'id': item.id,
        'message': item.message,
        'date': str(item.date),
        'rss_url': item.rss_url,
        'image_url': item.image_url
    } for item in items]}


@rest('/common/news/rss', 'put', type=REST_TYPE_TO)
@returns(SolutionRssSettingsTO)
@arguments(data=SolutionRssSettingsTO)
def rest_save_news_rss_feeds(data):
    # type: (SolutionRssSettingsTO) -> SolutionRssSettingsTO
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    rss_settings = save_rss_urls(service_user, service_identity, data)
    return SolutionRssSettingsTO.from_model(rss_settings)


@rest('/common/news/rss/validate', 'post')
@returns(UrlReturnStatusTO)
@arguments(url=unicode, allow_empty=bool)
def rest_news_validate_rss(url, allow_empty=False):
    try:
        service_user = users.get_current_user()
        sln_settings = get_solution_settings(service_user)
        url = url.strip()
        if url or not allow_empty:
            if not (url.startswith("http://") or url.startswith("https://")):
                url = "http://%s" % url
            validate_broadcast_url(url, sln_settings.main_language)
        return UrlReturnStatusTO.create(True, None, url)
    except BusinessException as e:
        return UrlReturnStatusTO.create(False, e.message, url)


@rest('/common/settings', 'put')
@returns(SolutionSettingsTO)
@arguments(data=SolutionSettingsTO)
def settings_save(data):
    # type: (SolutionSettingsTO) -> SolutionSettingsTO
    try:
        service_user = users.get_current_user()
        session_ = users.get_current_session()
        service_identity = session_.service_identity
        sln_settings, sln_i_settings = save_settings(service_user, service_identity, data)
        return SolutionSettingsTO.fromModel(sln_settings, sln_i_settings)
    except BusinessException as e:
        raise HttpBadRequestException(e.message)


@rest('/common/settings', 'get', read_only_access=True)
@returns(SolutionSettingsTO)
@arguments()
def settings_load():
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    sln_settings = get_solution_settings(service_user)
    sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, service_identity)
    return SolutionSettingsTO.fromModel(sln_settings, sln_i_settings)


@rest('/common/available-place-types', 'get', read_only_access=True, silent_result=True)
@returns(dict)
@arguments()
def rest_get_place_types():
    service_user = users.get_current_user()
    sln_settings = get_solution_settings(service_user)
    result_list = []
    place_types = get_place_types(sln_settings.main_language)
    for place_type, label in place_types.iteritems():
        result_list.append([place_type, label])
    return {'results': sorted(([place_type, label] for place_type, label in place_types.iteritems()),
                              key=lambda x: x[1].lower())}


@rest('/common/countries', 'get', read_only_access=True, silent_result=True)
@returns(dict)
@arguments()
def rest_get_countries():
    service_user = users.get_current_user()
    sln_settings = get_solution_settings(service_user)
    locale = Locale(sln_settings.locale)
    return {'countries': sorted([[code, name] for code, name in locale.territories.iteritems()],
                                key=lambda x: x[1].lower())}


def is_place_visible_for_customer(place_details, customer):
    if not place_details.organization_types:
        return True
    if customer and customer.organization_type in place_details.organization_types:
        return True
    return False


def _get_city_services(community_id):
    customers = Customer.list_enabled_by_organization_type_in_community(community_id, OrganizationType.CITY)
    return [SimpleServiceTO(name=c.name, service_email=c.service_email) for c in customers if c.service_email]


@rest('/common/settings/paddle', 'get', type=REST_TYPE_TO, silent_result=True)
@returns(PaddleSettingsServicesTO)
@arguments()
def rest_get_paddle_settings():
    # type: () -> PaddleSettingsServicesTO
    service_user = users.get_current_user()
    settings_key = PaddleSettings.create_key(service_user)
    settings = settings_key.get() or PaddleSettings(key=settings_key)
    service_profile = get_service_profile(service_user)
    return PaddleSettingsServicesTO(settings=PaddleSettingsTO.from_model(settings),
                                    services=_get_city_services(service_profile.community_id))


@rest('/common/settings/paddle', 'put', type=REST_TYPE_TO, silent_result=True)
@returns(PaddleSettingsServicesTO)
@arguments(data=PaddleSettingsTO)
def rest_save_paddle_settings(data):
    # type: (PaddleSettingsTO) -> PaddleSettingsServicesTO
    service_user = users.get_current_user()
    settings_key = PaddleSettings.create_key(service_user)
    settings = settings_key.get() or PaddleSettings(key=settings_key)
    base_url = data.base_url.rstrip('/') if data.base_url else None
    base_url_changed = base_url != settings.base_url
    settings.base_url = base_url
    for m in settings.mapping:
        for mapping in data.mapping:
            if mapping.paddle_id == m.paddle_id:
                m.service_email = mapping.service_email
    to_put = [settings]
    paddle_info = None
    if base_url_changed:
        if settings.base_url:
            paddle_info = get_paddle_info(settings)
            # Overwrite existing mapping
            settings.mapping = [PaddleMapping(service_email=None, paddle_id=m.node.nid, title=m.node.title)
                                for m in paddle_info.units]
            to_put.append(paddle_info)
        else:
            PaddleOrganizationalUnits.create_key(service_user).delete()
            settings.mapping = []
    else:
        paddle_info = PaddleOrganizationalUnits.create_key(service_user).get()
    ndb.put_multi(to_put)
    if paddle_info:
        populate_info_from_paddle(settings, paddle_info)
    service_profile = get_service_profile(service_user)
    return PaddleSettingsServicesTO(settings=PaddleSettingsTO.from_model(settings),
                                    services=_get_city_services(service_profile.community_id))


@rest("/common/settings/publish_changes", "post")
@returns(ReturnStatusTO)
@arguments(friends=[BaseMemberTO])
def settings_publish_changes(friends=None):
    service_user = users.get_current_user()
    try:
        common_provision(service_user, friends=friends, run_checks=True)
        return RETURNSTATUS_TO_SUCCESS
    except InvalidValueException as e:
        reason = e.fields.get('reason')
        property_ = e.fields.get('property')
        logging.warning("Invalid value for property %s: %s", property_, reason, exc_info=1)
        return ReturnStatusTO.create(False, reason or e.message)
    except AvatarImageNotSquareException:
        sln_settings = get_solution_settings(service_user)
        message = common_translate(sln_settings.main_language,
                                   'please_select_valid_avatar_image')
        return ReturnStatusTO.create(False, message)
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@rest('/common/settings/auto-publish', 'post')
@returns(dict)
@arguments()
def api_check_auto_publish():
    service_user = users.get_current_user()
    sln_settings = get_solution_settings(service_user)
    error_lines = []
    countdown_seconds = 60 * AUTO_PUBLISH_MINUTES
    if sln_settings.updates_pending:
        if not sln_settings.update_date or not sln_settings.auto_publish_date:
            should_auto_publish = True
        else:
            expected_auto_publish_date = sln_settings.update_date + relativedelta(seconds=countdown_seconds)
            diff = expected_auto_publish_date - sln_settings.auto_publish_date
            # Only update the auto publish date when the update date is longer than 1 minute after the auto publish date
            should_auto_publish = expected_auto_publish_date > sln_settings.auto_publish_date and diff.seconds > 60
        if should_auto_publish:
            error_lines = validate_before_provision(service_user, sln_settings)
            valid = not error_lines
            if sln_settings.auto_publish_task_id:
                logging.debug('Canceling scheduled auto publish task')
                taskqueue.Queue(SCHEDULED_QUEUE).delete_tasks(taskqueue.Task(name=sln_settings.auto_publish_task_id))
                sln_settings.auto_publish_date = None
                sln_settings.auto_publish_task_id = None
            if valid:
                logging.debug('Scheduling auto publish task')
                sln_settings.auto_publish_date = datetime.now() + relativedelta(seconds=countdown_seconds)
                new_task = deferred.defer(auto_publish, service_user, _countdown=countdown_seconds,
                                          _queue=SCHEDULED_QUEUE)  # type: taskqueue.Task
                sln_settings.auto_publish_task_id = new_task.name
            sln_settings.put()
    return {
        'valid': not error_lines,
        'publish_date': sln_settings.auto_publish_date and (sln_settings.auto_publish_date.isoformat() + 'Z'),
        'errors': error_lines,
    }


@rest("/common/settings/publish_changes/users", "post")
@returns()
@arguments(user_keys=[unicode])
def settings_save_publish_changes_users(user_keys):
    service_user = users.get_current_user()
    sln_settings = get_solution_settings(service_user)
    sln_settings.publish_changes_users = user_keys
    sln_settings.put()


@rest('/common/settings/logo', 'put')
@returns(BrandingSettingsTO)
@arguments(data=BrandingSettingsTO)
def rest_update_logo(data):
    service_identity = users.get_current_session().service_identity
    return BrandingSettingsTO.from_model(set_logo(users.get_current_user(), data.logo_url, service_identity))


@rest('/common/settings/avatar', 'put', type=REST_TYPE_TO)
@returns(BrandingSettingsTO)
@arguments(data=BrandingSettingsTO)
def rest_update_avatar(data):
    return BrandingSettingsTO.from_model(set_avatar(users.get_current_user(), data.avatar_url))


@rest("/common/menu/save", "post")
@returns(ReturnStatusTO)
@arguments(menu=MenuTO)
def menu_save(menu):
    from solutions.common.bizz.menu import save_menu
    try:
        service_user = users.get_current_user()
        save_menu(service_user, menu)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@rest("/common/menu/import", "post", silent=True)
@returns(ReturnStatusTO)
@arguments(file_contents=str)
def menu_import(file_contents):
    """" import menu from excel files """
    from solutions.common.bizz.menu import import_menu_from_excel
    try:
        service_user = users.get_current_user()
        import_menu_from_excel(service_user, file_contents)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@rest("/common/menu/save_name", "post")
@returns(ReturnStatusTO)
@arguments(name=unicode)
def menu_save_name(name):
    from solutions.common.bizz.menu import save_menu_name
    try:
        service_user = users.get_current_user()
        save_menu_name(service_user, name)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@rest("/common/menu/load", "get", read_only_access=True)
@returns(MenuTO)
@arguments()
def load_menu():
    from solutions.common.dal import get_restaurant_menu
    service_user = users.get_current_user()
    menu = get_restaurant_menu(service_user)
    if not menu:
        logging.info('Setting menu')
        menu = _put_default_menu(service_user)
    return MenuTO.fromMenuObject(menu)


@rest("/common/bulkinvite", "post")
@returns(ReturnStatusTO)
@arguments(emails=[unicode], invitation_message=unicode)
def bulk_invite(emails, invitation_message):
    from solutions.common.bizz.bulk_invite import bulk_invite
    try:
        service_user = users.get_current_user()
        session_ = users.get_current_session()
        service_identity = session_.service_identity
        bulk_invite(service_user, service_identity, emails, invitation_message)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@rest("/common/calendar/delete", "post")
@returns(ReturnStatusTO)
@arguments(calendar_id=(int, long))
def delete_calendar(calendar_id):
    service_user = users.get_current_user()
    sln_settings = get_solution_settings(service_user)
    try:
        sc = SolutionCalendar.create_key(calendar_id, service_user, sln_settings.solution).get()
        if sc.events.count(1) > 0:
            raise BusinessException(common_translate(sln_settings.main_language,
                                                     'calendar-remove-failed-has-events'))

        sc.deleted = True
        sc.put()
        sln_settings.updates_pending = True
        put_and_invalidate_cache(sln_settings)
        broadcast_updates_pending(sln_settings)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@rest("/common/calendar/save", "post")
@returns(ReturnStatusTO)
@arguments(calendar=SolutionCalendarTO)
def save_calendar(calendar):
    service_user = users.get_current_user()
    sln_settings = get_solution_settings(service_user)
    try:
        if calendar.id:
            sc = SolutionCalendar.create_key(calendar.id, service_user, sln_settings.solution).get()
        else:
            sc = SolutionCalendar(parent=parent_ndb_key(service_user, sln_settings.solution))

        for c in get_solution_calendars(service_user, sln_settings.solution):

            if c.name.lower() == calendar.name.lower():
                if calendar.id != c.calendar_id:
                    raise BusinessException(common_translate(sln_settings.main_language,
                                                             'calendar-name-already-exists', name=calendar.name))

        sc.name = calendar.name
        sc.put()
        sln_settings.updates_pending = True
        put_and_invalidate_cache(sln_settings)
        broadcast_updates_pending(sln_settings)

        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@rest("/common/calendar/load", "get", silent_result=True, read_only_access=True)
@returns([SolutionCalendarWebTO])
@arguments()
def load_calendar():
    service_user = users.get_current_user()
    sln_settings = get_solution_settings(service_user)
    base_url = get_server_settings().baseUrl
    return [SolutionCalendarWebTO.fromSolutionCalendar(sln_settings, calendar, base_url, True)
            for calendar in get_solution_calendars(service_user, sln_settings.solution)]


@rest("/common/calendar/load/more", "get", silent_result=True, read_only_access=True)
@returns(SolutionCalendarWebTO)
@arguments(calendar_id=(int, long), cursor=unicode)
def load_calendar_more(calendar_id, cursor=None):
    service_user = users.get_current_user()
    sln_settings = get_solution_settings(service_user)
    base_url = get_server_settings().baseUrl
    calendar = SolutionCalendar.create_key(calendar_id, service_user, sln_settings.solution).get()
    return SolutionCalendarWebTO.fromSolutionCalendar(sln_settings, calendar, base_url, True, cursor)


@rest("/common/calendar/google/authenticate/url", "get", read_only_access=True)
@returns(unicode)
@arguments(calendar_id=(int, long))
def calendar_google_authenticate_url(calendar_id):
    return get_google_authenticate_url(calendar_id)


@rest("/common/calendar/google/load", "get", read_only_access=True)
@returns(SolutionGoogleCalendarStatusTO)
@arguments(calendar_id=(int, long))
def calendar_google_load(calendar_id):
    service_user = users.get_current_user()
    return get_google_calendars(service_user, calendar_id)


@rest("/common/calendar/import/google/put", "post")
@returns(ReturnStatusTO)
@arguments(calendar_id=(int, long), google_calendars=[SolutionUserKeyLabelTO])
def calendar_put_google_import(calendar_id, google_calendars):
    service_user = users.get_current_user()
    sln_settings = get_solution_settings(service_user)
    try:
        def trans():
            sc = SolutionCalendar.create_key(calendar_id, service_user, sln_settings.solution).get()
            if not sc:
                raise BusinessException(
                    common_translate(sln_settings.main_language, 'Calendar not found'))

            deferred.defer(update_events_from_google, service_user, calendar_id, _transactional=True)

            sc.google_calendar_ids = []
            sc.google_calendar_names = []
            for google_calendar in google_calendars:
                sc.google_calendar_ids.append(google_calendar.key)
                sc.google_calendar_names.append(google_calendar.label)
            sc.google_sync_events = bool(sc.google_calendar_ids)
            sc.put()

        ndb.transaction(trans)

        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@rest("/common/events/put", "post", type=REST_TYPE_TO)
@returns(EventItemTO)
@arguments(data=CreateEventItemTO)
def put_event(data):
    from solutions.common.bizz.events import put_event as put_event_bizz
    try:
        service_user = users.get_current_user()
        sln_settings = get_solution_settings(service_user)
        org_type = get_organization_type(service_user)
        service_profile = get_service_profile(service_user)
        event = put_event_bizz(sln_settings, data, service_profile.community_id, org_type)
        return EventItemTO.from_model(event, get_server_settings().baseUrl, destination_app=False)
    except BusinessException as e:
        raise HttpBadRequestException(e.message)


@rest("/common/events/delete", "post")
@returns(ReturnStatusTO)
@arguments(event_id=(int, long))
def delete_event(event_id):
    from solutions.common.bizz.events import delete_event as delete_event_bizz
    try:
        service_user = users.get_current_user()
        delete_event_bizz(service_user, event_id)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@rest("/common/events/uit/actor/load", "get", read_only_access=True)
@returns(unicode)
@arguments()
def load_uit_actor_id():
    service_user = users.get_current_user()
    settings = get_solution_settings(service_user)
    return settings.uitdatabank_actor_id


@rest("/common/events/uit/actor/put", "post")
@returns(ReturnStatusTO)
@arguments(uit_id=unicode)
def put_uit_actor_id(uit_id):
    service_user = users.get_current_user()
    settings = get_solution_settings(service_user)
    settings.uitdatabank_actor_id = uit_id
    settings.put()
    return RETURNSTATUS_TO_SUCCESS


@rest("/common/settings/getTimezoneOffset", "get", read_only_access=True)
@returns(long)
@arguments()
def get_timezone_offset():
    service_user = users.get_current_user()
    settings = get_solution_settings(service_user)
    return timezone_offset(settings.timezone)


@rest("/common/friends/load", "get", read_only_access=True)
@returns(FriendListResultTO)
@arguments(batch_count=int, cursor=unicode)
def load_friends_list(batch_count, cursor):
    from rogerthat.service.api.friends import list_friends
    from rogerthat.utils.crypto import encrypt
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    frto = list_friends(service_identity, cursor, batch_count=batch_count)
    for f in frto.friends:
        f.email = unicode(encrypt(service_user, f.email))
    return frto


@rest("/common/statistics/load", "get", silent_result=True, read_only_access=True)
@returns(StatisticsResultTO)
@arguments()
def load_service_statistics():
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    si_stats = system.get_statistics(service_identity)

    result = StatisticsResultTO()
    result.service_identity_statistics = si_stats
    return result


@rest('/common/users/search', 'get', read_only_access=True)
@returns([UserDetailsTO])
@arguments(query=unicode, app_id=unicode)
def search_connected_users(query, app_id=None):
    from rogerthat.bizz.profile import search_users_via_friend_connection_and_name_or_email
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    if service_identity is None:
        service_identity = ServiceIdentity.DEFAULT
    connection = remove_slash_default(create_service_identity_user(service_user, service_identity)).email()
    return search_users_via_friend_connection_and_name_or_email(connection, query, app_id, True)


@rest("/common/users/roles/load", "get")
@returns([AppUserRolesTO])
@arguments()
def users_load_roles():
    """
        Gather inbox forwarders, calendar admins and news publishers
        from different places/models
    """
    service_user = users.get_current_user()
    sln_settings = get_solution_settings(service_user)

    # get inbox forwarders and news publishers
    inbox_forwarders = inbox_load_forwarders()
    news_publishers = get_solution_news_publishers(service_user, sln_settings.solution)

    # create AppUserRolesTO for every role type
    # with different additional information for every type
    all_user_roles = defaultdict(AppUserRolesTO)

    mobile_inbox_forwarders = [f for f in inbox_forwarders if f.type == SolutionSettings.INBOX_FORWARDER_TYPE_MOBILE]
    email_inbox_forwarders = [f for f in inbox_forwarders if f.type == SolutionSettings.INBOX_FORWARDER_TYPE_EMAIL]

    # mobile forwarders may have an app id
    for forwarder in mobile_inbox_forwarders:
        email = forwarder.key
        try:
            app_id = email.split(':')[1]
        except IndexError:
            app_id = None
        user_roles = all_user_roles[email]
        user_roles.app_user_email = email
        user_roles.app_id = app_id
        # additional info: forwarder type
        user_roles.add_forwarder_type(SolutionSettings.INBOX_FORWARDER_TYPE_MOBILE)

    for publisher in news_publishers:
        email = publisher.app_user.email()
        user_roles = all_user_roles[email]
        user_roles.app_user_email = email
        user_roles.app_id = get_app_id_from_app_user(publisher.app_user)
        user_roles.news_publisher = True

    # because email forwarders are stored only by email, without an app id
    # after gathering all roles, check if a user with this email
    # is a mobile forwarder, then just append the type
    for forwarder in email_inbox_forwarders:
        email = forwarder.key  # email only
        has_roles = False  # check if any roles have this email
        for user_email, user_roles in all_user_roles.iteritems():
            # user_email may contain an app id, so check if it contains
            # email, then append the email forwarder type
            if email in user_email:
                user_roles.add_forwarder_type(SolutionSettings.INBOX_FORWARDER_TYPE_EMAIL)
                has_roles = True

        # no user roles for this email, then create it
        if not has_roles:
            user_roles = all_user_roles[email]
            user_roles.app_user_email = email
            user_roles.add_forwarder_type(SolutionSettings.INBOX_FORWARDER_TYPE_EMAIL)

    return all_user_roles.values()


@rest("/common/users/roles/add", "post")
@returns(ReturnStatusTO)
@arguments(key=unicode, user_roles=AppUserRolesTO)
def users_add_user_roles(key, user_roles):
    # type: (str, AppUserRolesTO) -> ReturnStatusTO
    """ set different app roles for a user """
    try:
        service_user = users.get_current_user()
        session_ = users.get_current_session()
        service_identity = session_.service_identity
        sln_settings = get_solution_settings(service_user)
        sln_i_settings = get_solution_settings_or_identity_settings(sln_settings,
                                                                    service_identity)

        # try first to get the user from user key
        app_user = users.User(key)
        email, app_id = get_app_user_tuple(app_user)
        is_existing_user = is_existing_friend(email.email(), app_id, service_identity)

        # add inbox forwarder
        if user_roles.inbox_forwarder:
            forwarder_types = user_roles.forwarder_types
            for forwarder_type in forwarder_types:
                if forwarder_type:
                    if forwarder_type == SolutionSettings.INBOX_FORWARDER_TYPE_EMAIL:
                        # only email without an app id
                        key = get_human_user_from_app_user(app_user).email()
                    else:
                        key = app_user.email()

                    if not EMAIL_REGEX.match(key):
                        return ReturnStatusTO.create(False,
                                                     common_translate(sln_settings.main_language,
                                                                      'Please provide a valid e-mail address'))
                    forwarders = sln_i_settings.get_forwarders_by_type(forwarder_type)
                    if key not in forwarders:
                        forwarders.append(key)
            sln_i_settings.put()

        if is_existing_user:
            # add as news publisher
            if user_roles.news_publisher:
                create_news_publisher(app_user, service_user, sln_settings.solution)

        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@rest("/common/users/roles/delete", "post")
@returns(ReturnStatusTO)
@arguments(key=unicode, forwarder_types=[unicode], calendar_ids=[(int, long)])
def users_delete_user_roles(key, forwarder_types, calendar_ids):
    """ remove all the user app roles """
    try:
        service_user = users.get_current_user()
        session_ = users.get_current_session()
        service_identity = session_.service_identity
        sln_settings = get_solution_settings(service_user)
        sln_i_settings = get_solution_settings_or_identity_settings(sln_settings,
                                                                    service_identity)
        app_user = users.User(key)

        # inbox
        if forwarder_types:
            key = app_user.email()
            for forwarder_type in forwarder_types:
                if forwarder_type == SolutionSettings.INBOX_FORWARDER_TYPE_EMAIL:
                    key = get_human_user_from_app_user(app_user).email()

                forwarders = sln_i_settings.get_forwarders_by_type(forwarder_type)
                if key in forwarders:
                    forwarders.remove(key)
            sln_i_settings.put()

        # news
        delete_news_publisher(app_user, service_user, sln_settings.solution)

        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@rest('/common/users/admins', 'get')
@returns([unicode])
@arguments()
def rest_load_service_admins():
    service_user = users.get_current_user()
    return get_service_admins(service_user)


@rest('/common/users/admins', 'post')
@returns(ReturnStatusTO)
@arguments(user_email=unicode)
def rest_add_service_email(user_email):
    base_url = GenericRESTRequestHandler.getCurrentRequest().headers.get('Origin') or get_server_settings().baseUrl
    try:
        service_user = users.get_current_user()
        if not EMAIL_REGEX.match(user_email):
            sln_settings = get_solution_settings(service_user)
            message = common_translate(sln_settings.main_language, 'invalid_email_format', email=user_email)
            return ReturnStatusTO.create(False, message)
        add_service_admin(service_user, user_email, base_url)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@rest("/common/inbox/forwarders/load", "get", read_only_access=True)
@returns([SolutionInboxForwarder])
@arguments()
def inbox_load_forwarders():
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    if is_default_service_identity(service_identity):
        sln_i_settings = get_solution_settings(service_user)
    else:
        sln_i_settings = get_solution_identity_settings(service_user, service_identity)
    forwarder_profiles = dict(zip(sln_i_settings.inbox_forwarders,
                                  db.get(
                                      [get_profile_key(u) for u in map(users.User, sln_i_settings.inbox_forwarders)])))

    forwarders_to_be_removed = list()
    sifs = []
    for fw_type, forwarders in [(SolutionSettings.INBOX_FORWARDER_TYPE_MOBILE, sln_i_settings.inbox_forwarders),
                                (SolutionSettings.INBOX_FORWARDER_TYPE_EMAIL, sln_i_settings.inbox_mail_forwarders), ]:
        for forwarder in forwarders:
            sif = SolutionInboxForwarder()
            sif.type = fw_type
            sif.key = forwarder
            if fw_type == SolutionSettings.INBOX_FORWARDER_TYPE_MOBILE:
                up = forwarder_profiles[forwarder]
                if up:
                    sif.label = u"%s (%s)" % (up.name, get_human_user_from_app_user(up.user).email())
                else:
                    forwarders_to_be_removed.append(forwarder)
                    continue
            else:
                sif.label = forwarder
            sifs.append(sif)

    if forwarders_to_be_removed:
        logging.info('Inbox forwarders %s do not exist anymore', forwarders_to_be_removed)

        def trans():
            if is_default_service_identity(service_identity):
                sln_i_settings = get_solution_settings(service_user)
            else:
                sln_i_settings = get_solution_identity_settings(service_user, service_identity)
            for fwd in forwarders_to_be_removed:
                sln_i_settings.inbox_forwarders.remove(fwd)
            sln_i_settings.put()

        db.run_in_transaction(trans)
    return sifs


@rest("/common/inbox/forwarders/add", "post")
@returns(ReturnStatusTO)
@arguments(key=unicode, forwarder_type=unicode)
def inbox_add_forwarder(key, forwarder_type=SolutionSettings.INBOX_FORWARDER_TYPE_MOBILE):
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    sln_settings = get_solution_settings(service_user)
    sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, service_identity)

    if forwarder_type == SolutionSettings.INBOX_FORWARDER_TYPE_EMAIL:
        if not EMAIL_REGEX.match(key):
            return ReturnStatusTO.create(False, common_translate(sln_settings.main_language,
                                                                 'Please provide a valid e-mail address'))
    elif forwarder_type == SolutionSettings.INBOX_FORWARDER_TYPE_MOBILE:
        app_user = sanitize_app_user(users.User(key))
        get_user_profile(app_user)
        key = app_user.email()

    forwarders = sln_i_settings.get_forwarders_by_type(forwarder_type)
    if key not in forwarders:
        forwarders.append(key)
        sln_i_settings.put()
    return RETURNSTATUS_TO_SUCCESS


@rest("/common/inbox/forwarders/delete", "post")
@returns(ReturnStatusTO)
@arguments(key=unicode, forwarder_type=unicode)
def inbox_delete_forwarder(key, forwarder_type=SolutionSettings.INBOX_FORWARDER_TYPE_MOBILE):
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    if is_default_service_identity(service_identity):
        sln_i_settings = get_solution_settings(service_user)
    else:
        sln_i_settings = get_solution_identity_settings(service_user, service_identity)
    forwarders = sln_i_settings.get_forwarders_by_type(forwarder_type)
    if key in forwarders:
        forwarders.remove(key)
        sln_i_settings.put()
    else:
        logging.warn('%s inbox forwarder "%s" not found', forwarder_type, key)
    return RETURNSTATUS_TO_SUCCESS


@rest("/common/appointment/settings/load", "get", read_only_access=True)
@returns(SolutionAppointmentSettingsTO)
@arguments()
def load_appointment_settings():
    service_user = users.get_current_user()
    sln_settings = get_solution_settings(service_user)
    sln_appointment_settings = get_solution_appointment_settings(service_user)
    return SolutionAppointmentSettingsTO.fromModel(sln_appointment_settings, sln_settings.main_language)


@rest("/common/appointment/settings/put", "post")
@returns(ReturnStatusTO)
@arguments(text_1=unicode)
def put_appointment_settings(text_1):
    service_user = users.get_current_user()
    try:
        sln_appointment_settings_key = SolutionAppointmentSettings.create_key(service_user)
        sln_appointment_settings = SolutionAppointmentSettings.get(sln_appointment_settings_key)
        if not sln_appointment_settings:
            sln_appointment_settings = SolutionAppointmentSettings(key=sln_appointment_settings_key)
        sln_appointment_settings.text_1 = text_1
        sln_appointment_settings.put()

        sln_settings = get_solution_settings(service_user)
        sln_settings.updates_pending = True
        put_and_invalidate_cache(sln_appointment_settings, sln_settings)
        broadcast_updates_pending(sln_settings)
        send_message(service_user, u"solutions.common.appointment.settings.update")
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@rest("/common/appointment/settings/timeframe/put", "post")
@returns(ReturnStatusTO)
@arguments(appointment_id=(int, long, NoneType), day=int, time_from=int, time_until=int)
def put_appointment_weekday_timeframe(appointment_id, day, time_from, time_until):
    from solutions.common.bizz.appointment import \
        put_appointment_weekday_timeframe as put_appointment_weekday_timeframe_bizz
    service_user = users.get_current_user()
    try:
        put_appointment_weekday_timeframe_bizz(service_user, appointment_id, day, time_from, time_until)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@rest("/common/appointment/settings/timeframe/load", "get", read_only_access=True)
@returns([SolutionAppointmentWeekdayTimeframeTO])
@arguments()
def load_appointment_weekday_timeframes():
    service_user = users.get_current_user()
    sln_settings = get_solution_settings(service_user)
    return [SolutionAppointmentWeekdayTimeframeTO.fromModel(f, sln_settings.main_language or DEFAULT_LANGUAGE) for f in
            SolutionAppointmentWeekdayTimeframe.list(service_user, sln_settings.solution)]


@rest("/common/appointment/settings/timeframe/delete", "post")
@returns(ReturnStatusTO)
@arguments(appointment_id=(int, long))
def delete_appointment_weekday_timeframe(appointment_id):
    from solutions.common.bizz.appointment import \
        delete_appointment_weekday_timeframe as delete_appointment_weekday_timeframe_bizz
    service_user = users.get_current_user()
    try:
        delete_appointment_weekday_timeframe_bizz(service_user, appointment_id)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@rest("/common/settings/branding", "get", read_only_access=True)
@returns(BrandingSettingsTO)
@arguments()
def get_branding_settings():
    branding_settings = SolutionBrandingSettings.get_by_user(users.get_current_user())
    return BrandingSettingsTO.from_model(branding_settings)


@rest("/common/settings/branding_and_menu", "get", read_only_access=True)
@returns(BrandingSettingsAndMenuItemsTO)
@arguments()
def rest_get_branding_settings_and_menu():
    branding_settings = SolutionBrandingSettings.get_by_user(users.get_current_user())
    branding_settings_to = BrandingSettingsTO.from_model(branding_settings)
    service_menu = system.get_menu_item()
    smi_dict = {'x'.join(map(str, smi.coords)): smi for smi in service_menu.items}
    service_menu_items = list()
    z = 0
    for y in xrange(3):
        row = list()
        for x in xrange(4):
            coords = 'x'.join(map(str, [x, y, z]))
            label = None
            icon_name = None
            if y == 0:
                if x == 0:
                    label = service_menu.aboutLabel or u'About'
                    icon_name = u'fa-info'
                elif x == 1:
                    label = service_menu.messagesLabel or u'History'
                    icon_name = u'fa-envelope'
                elif x == 2:
                    if service_menu.phoneNumber:
                        label = service_menu.callLabel or u'Call'
                    icon_name = u'fa-phone'
                elif x == 3:
                    if service_menu.shareQRId:
                        label = service_menu.shareLabel or u'Recommend'
                        icon_name = u'fa-thumbs-o-up'
                icon_url = None
            else:
                smi = smi_dict.get(coords)
                label = smi.label if smi else None
                icon_url = smi.iconUrl if smi else None
                icon_name = smi.iconName if smi else None

            row.append(ServiceMenuItemWithCoordinatesTO.create(label, icon_name, icon_url, coords))
        service_menu_items.append(ServiceMenuItemWithCoordinatesListTO.create(row))
    return BrandingSettingsAndMenuItemsTO.create(branding_settings_to, service_menu_items)


@rest("/common/settings/branding", "post")
@returns(ReturnStatusTO)
@arguments(branding_settings=BrandingSettingsTO)
def rest_save_branding_settings(branding_settings):
    """
    Args:
        branding_settings (BrandingSettingsTO)
    """
    try:
        branding_settings.background_color = MISSING
        branding_settings.text_color = MISSING
        save_branding_settings(users.get_current_user(), branding_settings)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@rest('/common/q-matic', 'get')
@returns(dict)
@arguments()
def rest_get_qmatic_settings():
    return get_qmatic_settings(users.get_current_user()).to_dict()


@rest('/common/q-matic', 'put')
@returns(dict)
@arguments(data=dict)
def rest_save_qmatic_settings(data):
    return save_qmatic_settings(users.get_current_user(), data['url'], data['auth_token']).to_dict()


@rest('/common/jcc-appointments', 'get')
@returns(dict)
@arguments()
def rest_get_jcc_settings():
    return get_jcc_settings(users.get_current_user()).to_dict()


@rest('/common/jcc-appointments', 'put')
@returns(dict)
@arguments(data=dict)
def rest_save_jcc_settings(data):
    return save_jcc_settings(users.get_current_user(), **data).to_dict()


@rest("/common/repair/settings/load", "get", read_only_access=True)
@returns(SolutionRepairSettingsTO)
@arguments()
def repair_settings_load():
    service_user = users.get_current_user()
    sln_settings = get_solution_settings(service_user)
    sln_repair_settings = get_solution_repair_settings(service_user)
    return SolutionRepairSettingsTO.fromModel(sln_repair_settings, sln_settings.main_language)


@rest("/common/repair/settings/put", "post")
@returns(ReturnStatusTO)
@arguments(text_1=unicode)
def put_repair_settings(text_1):
    service_user = users.get_current_user()
    try:
        sln_repair_settings_key = SolutionRepairSettings.create_key(service_user)
        sln_repair_settings = SolutionRepairSettings.get(sln_repair_settings_key)
        if not sln_repair_settings:
            sln_repair_settings = SolutionRepairSettings(key=sln_repair_settings_key)
        sln_repair_settings.text_1 = text_1
        sln_repair_settings.put()

        sln_settings = get_solution_settings(service_user)
        sln_settings.updates_pending = True
        put_and_invalidate_cache(sln_repair_settings, sln_settings)
        broadcast_updates_pending(sln_settings)
        send_message(service_user, u"solutions.common.repair.settings.update")
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@rest("/common/repair_order/delete", "post")
@returns(ReturnStatusTO)
@arguments(order_key=unicode, message=unicode)
def repair_order_delete(order_key, message):
    service_user = users.get_current_user()
    try:
        delete_repair_order(service_user, order_key, message)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@rest("/common/repair_order/load", "get", read_only_access=True)
@returns([SolutionRepairOrderTO])
@arguments()
def repair_orders_load():
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    sln_settings = get_solution_settings(service_user)
    return map(SolutionRepairOrderTO.fromModel,
               get_solution_repair_orders(service_user, service_identity, sln_settings.solution))


@rest("/common/repair_order/sendmessage", "post")
@returns(ReturnStatusTO)
@arguments(order_key=unicode, order_status=int, message=unicode)
def repair_order_send_message(order_key, order_status, message):
    service_user = users.get_current_user()
    try:
        send_message_for_repair_order(service_user, order_key, order_status, message)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@rest("/common/sandwich/settings/load", "get", read_only_access=True)
@returns(SandwichSettingsTO)
@arguments()
def rest_load_sandwich_settings():
    service_user = users.get_current_user()
    sln_settings = get_solution_settings(service_user)

    types = SandwichType.list(service_user, sln_settings.solution).run()
    toppings = SandwichTopping.list(service_user, sln_settings.solution).run()
    options = SandwichOption.list(service_user, sln_settings.solution).run()
    sandwich_settings = SandwichSettings.get_settings(service_user, sln_settings.solution)

    return SandwichSettingsTO.from_model(sandwich_settings, types, toppings, options, sln_settings.currency)


@rest("/common/sandwich/settings/save", "post")
@returns(SandwichSettingsTO)
@arguments(sandwich_settings=SandwichSettingsTO)
def save_sandwich_settings(sandwich_settings):
    """
    Args:
        sandwich_settings (SandwichSettingsTO)
    Returns:
        sandwich_settings (SandwichSettingsTO)
    """
    service_user = users.get_current_user()

    sln_settings = get_solution_settings(service_user)
    simple_members = get_members(SandwichSettingsTO)[1]
    to_put = []

    if any(getattr(sandwich_settings, name) is not MISSING for name, _ in simple_members):
        sandwich_settings_model = SandwichSettings.get_settings(service_user, sln_settings.solution)
        if sandwich_settings.show_prices != MISSING:
            sandwich_settings_model.show_prices = sandwich_settings.show_prices
        if sandwich_settings.days != MISSING:
            sandwich_settings_model.status_days = sandwich_settings.days
        if sandwich_settings.from_ != MISSING:
            sandwich_settings_model.time_from = sandwich_settings.from_
        if sandwich_settings.till != MISSING:
            sandwich_settings_model.time_until = sandwich_settings.till
        if sandwich_settings.leap_time is not MISSING:
            sandwich_settings_model.leap_time = sandwich_settings.leap_time
        if sandwich_settings.leap_time_enabled is not MISSING:
            sandwich_settings_model.leap_time_enabled = sandwich_settings.leap_time_enabled
        if sandwich_settings.leap_time_type is not MISSING:
            sandwich_settings_model.leap_time_type = sandwich_settings.leap_time_type

        to_put.append(sandwich_settings_model)

    has_new = False

    def update(items, clazz):
        has_new_items = False
        # XXX: multiget
        for item in items:
            if item.id is MISSING:
                item_model = clazz(parent=parent_key(service_user, sln_settings.solution))
                has_new_items = True
            else:
                item_model = clazz.get_by_id(item.id, parent_key(service_user, sln_settings.solution))
                if item.deleted:
                    item_model.deleted = True
            item_model.description = item.description
            item_model.price = item.price
            item_model.order = item.order
            to_put.append(item_model)
            return has_new_items

    if sandwich_settings.types != MISSING:
        has_new = has_new or update(sandwich_settings.types, SandwichType)
    if sandwich_settings.toppings != MISSING:
        has_new = has_new or update(sandwich_settings.toppings, SandwichTopping)
    if sandwich_settings.options != MISSING:
        has_new = has_new or update(sandwich_settings.options, SandwichOption)
    sln_settings.updates_pending = True
    to_put.append(sln_settings)
    put_in_chunks(to_put)

    broadcast_updates_pending(sln_settings)
    if has_new:
        return rest_load_sandwich_settings()


@rest("/common/sandwich/orders/load", "get", read_only_access=True)
@returns([SandwichOrderTO])
@arguments()
def load_sandwich_orders():
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    sln_settings = get_solution_settings(service_user)
    return [SandwichOrderTO.fromModel(m) for m in
            SandwichOrder.list(service_user, service_identity, sln_settings.solution)]


@rest("/common/sandwich/orders/reply", "post")
@returns(ReturnStatusTO)
@arguments(sandwich_id=unicode, message=unicode)
def sandwich_order_reply(sandwich_id, message):
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    try:
        reply_sandwich_order(service_user, service_identity, sandwich_id, message)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@rest("/common/sandwich/orders/ready", "post")
@returns(ReturnStatusTO)
@arguments(sandwich_id=unicode, message=unicode)
def sandwich_order_ready(sandwich_id, message):
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    try:
        ready_sandwich_order(service_user, service_identity, sandwich_id, message)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@rest("/common/sandwich/orders/delete", "post")
@returns(ReturnStatusTO)
@arguments(sandwich_id=unicode, message=unicode)
def sandwich_order_delete(sandwich_id, message):
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    try:
        delete_sandwich_order(service_user, service_identity, sandwich_id, message)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@rest("/common/group_purchase/broadcast", "post")
@returns(ReturnStatusTO)
@arguments(group_purchase_id=(int, long), message=unicode)
def group_purchase_broadcast(group_purchase_id, message=unicode):
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    try:
        broadcast_group_purchase(service_user, service_identity, group_purchase_id, message)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@rest("/common/group_purchase/load", "get", silent_result=True, read_only_access=True)
@returns([SolutionGroupPurchaseTO])
@arguments()
def group_purchase_load():
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    sln_settings = get_solution_settings(service_user)
    return [SolutionGroupPurchaseTO.fromModel(m, include_picture=True, incude_subscriptions=True) for m in
            SolutionGroupPurchase.list(service_user, service_identity, sln_settings.solution)]


@rest("/common/group_purchase/save", "post")
@returns(ReturnStatusTO)
@arguments(group_purchase=SolutionGroupPurchaseTO)
def group_purchase_save(group_purchase):
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    try:
        save_group_purchase(service_user, service_identity, group_purchase)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@rest("/common/group_purchase/delete", "post")
@returns(ReturnStatusTO)
@arguments(group_purchase_id=(int, long))
def group_purchase_delete(group_purchase_id):
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    try:
        delete_group_purchase(service_user, service_identity, group_purchase_id)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@rest("/common/group_purchase/subscriptions/add", "post")
@returns(ReturnStatusTO)
@arguments(group_purchase_id=(int, long), name=unicode, units=int)
def group_purchase_subscription_add(group_purchase_id, name, units):
    service_user = users.get_current_user()
    try:
        new_group_purchase_subscription(service_user, None, group_purchase_id, name, None, units)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@rest("/common/group_purchase/settings/load", "get", read_only_access=True)
@returns(SolutionGroupPurchaseSettingsTO)
@arguments()
def group_purchase_settings_load():
    service_user = users.get_current_user()
    sln_settings = get_solution_settings(service_user)
    return SolutionGroupPurchaseSettingsTO.fromModel(
        get_solution_group_purchase_settings(service_user, sln_settings.solution))


@rest("/common/group_purchase/settings/save", "post")
@returns(ReturnStatusTO)
@arguments(group_purchase_settings=SolutionGroupPurchaseSettingsTO)
def group_purchase_settings_save(group_purchase_settings):
    service_user = users.get_current_user()
    try:
        def trans():
            sln_settings = get_solution_settings(service_user)
            sgps = get_solution_group_purchase_settings(service_user, sln_settings.solution)
            sgps.visible = group_purchase_settings.visible

            sln_settings.updates_pending = True
            put_and_invalidate_cache(sgps, sln_settings)
            return sln_settings

        xg_on = db.create_transaction_options(xg=True)
        sln_settings = db.run_in_transaction_options(xg_on, trans)

        broadcast_updates_pending(sln_settings)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@rest('/common/menu/item/image/upload', 'post', read_only_access=False, silent_result=True)
@returns(ImageReturnStatusTO)
@arguments(image=unicode, image_id_to_delete=(int, long, NoneType))
def upload_menu_item_image(image=None, image_id_to_delete=None):
    service_user = users.get_current_user()
    sln_settings = get_solution_settings(service_user)
    logging.info('%s uploaded a small file', sln_settings.name)
    azzert(image)
    if image_id_to_delete:
        delete_file_blob(service_user, image_id_to_delete)
    try:
        image = create_file_blob(service_user, base64.b64decode(image.split(',', 1)[1]))
        return ImageReturnStatusTO.create(True, None, image.key().id())

    except BusinessException as ex:
        return ImageReturnStatusTO.create(False, ex.message, None)


@rest('/common/menu/item/image/qr_url', 'get')
@returns(unicode)
@arguments(category_index=(int, long), item_index=(int, long))
def menu_item_qr_url(category_index, item_index):
    service_user = users.get_current_user()
    return get_menu_item_qr_url(service_user, category_index, item_index)


@rest('/common/menu/item/image/remove', 'post', read_only_access=False)
@returns(ReturnStatusTO)
@arguments(image_id=(int, long))
def remove_file_blob(image_id):
    delete_file_blob(users.get_current_user(), image_id)


@rest('/common/customer/signup/all', 'get')
@returns([CustomerSignupTO])
@arguments()
def rest_get_customer_signups():
    service_user = users.get_current_user()
    city_customer = get_customer(service_user)
    return [CustomerSignupTO.from_model(s) for s in get_customer_signups(city_customer)]


@rest('/common/customer/signup/reply', 'post')
@returns(ReturnStatusTO)
@arguments(signup_key=unicode, message=unicode)
def rest_customer_signup_reply(signup_key, message):
    signup = db.get(signup_key)  # type: CustomerSignup

    if signup and not signup.done and signup.can_update:
        service_user = users.get_current_user()
        city_customer = get_customer(service_user)
        set_customer_signup_status(city_customer, signup, approved=False, reason=message)

    return RETURNSTATUS_TO_SUCCESS


@rest('/common/functionalities/modules/activated', 'get')
@returns([unicode])
@arguments()
def rest_get_activated_modules():
    service_user = users.get_current_user()
    sln_settings = get_solution_settings(service_user)
    modules = sln_settings.modules

    for module in sln_settings.modules_to_put:
        if module not in modules:
            modules.append(module)
    for module in sln_settings.modules_to_remove:
        if module in modules:
            modules.remove(module)

    return modules


@rest('/common/functionalities/modules/enable', 'post')
@returns(ReturnStatusTO)
@arguments(name=unicode, enabled=bool)
def rest_enable_or_disable_module(name, enabled):
    try:
        service_user = users.get_current_user()
        if not validate_enable_or_disable_solution_module(service_user, name, enabled):
            language = get_solution_settings(service_user).main_language
            return ReturnStatusTO.create(False, common_translate(language, 'cannot_enable_solution_module'))

        enable_or_disable_solution_module(service_user, name, enabled)

        return ReturnStatusTO.create()
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@rest('/common/files/<prefix:.*>', 'post')
@returns(UploadedImageTO)
@arguments(prefix=unicode)
def rest_upload_file(prefix):
    request = GenericRESTRequestHandler.getCurrentRequest()
    uploaded_file = request.POST.get('file')
    reference_type = request.POST.get('reference_type')
    ref_id = request.POST.get('reference')
    service_user = users.get_current_user()
    reference = None
    if ref_id and reference_type:
        if reference_type == 'form':
            form_id = long(ref_id)
            form_key = OcaForm.create_key(form_id, service_user)
            form = form_key.get()
            if not form:
                raise FormNotFoundException(form_id)
            prefix = 'forms/%d' % form_id
            reference = form_key
        elif reference_type == 'branding_settings':
            reference = ndb.Key.from_old_key(SolutionBrandingSettings.create_key(service_user))

    result = upload_file(users.get_current_user(), uploaded_file, prefix, reference)
    return UploadedImageTO.from_dict(result.to_dict(extra_properties=['url']))


@rest('/common/files', 'get', read_only_access=True, silent_result=True)
@returns([GcsFileTO])
@arguments(prefix=unicode)
def rest_list_uploaded_files(prefix=None):
    # Only returns images for now
    return [GcsFileTO(url=get_serving_url(i.cloudstorage_path), content_type=i.content_type, size=i.size or -1)
            for i in list_files(users.get_current_user(), prefix) if
            i.content_type in (AttachmentTO.CONTENT_TYPE_IMG_JPG, AttachmentTO.CONTENT_TYPE_IMG_PNG)]


@rest('/common/image-gallery/<prefix:[^/]+>', 'get', read_only_access=True, silent_result=True)
@returns([GcsFileTO])
@arguments(prefix=unicode)
def rest_list_gallery_images(prefix):
    path = '/%s/image-library/%s/' % (OCA_FILES_BUCKET, prefix)
    if DEBUG:
        return [
            GcsFileTO(url='https://storage.googleapis.com/oca-files/image-library/%s/merchant.jpg' % prefix,
                      content_type='image/jpeg',
                      size=-1),
            GcsFileTO(url='https://storage.googleapis.com/oca-files/image-library/%s/community-service.jpg' % prefix,
                      content_type='image/jpeg',
                      size=-1),
            GcsFileTO(url='https://storage.googleapis.com/oca-files/image-library/%s/association.jpg' % prefix,
                      content_type='image/jpeg',
                      size=-1),
            GcsFileTO(url='https://storage.googleapis.com/oca-files/image-library/%s/care.jpg' % prefix,
                      content_type='image/jpeg',
                      size=-1),
        ]
    return [GcsFileTO(url=get_serving_url(f.filename), content_type=f.content_type, size=f.st_size) for f in cloudstorage.listbucket(path) if f.filename != path]


@rest('/common/i18n/<prefix:[^/]+>/<lang:[^/]+>.json', 'get', read_only_access=True, authenticated=False, silent=True,
      silent_result=True)
@returns(dict)
@arguments(lang=unicode, prefix=unicode)
def api_get_translations(lang, prefix):
    language_translations = translations.get(lang, {})
    prefix_with_dot = prefix + '.'
    mapping = {key.replace(prefix_with_dot, ''): translation
               for key, translation in language_translations.iteritems()
               if key.startswith(prefix_with_dot)}
    translation_re = re.compile(r'%\((.*)\)s')
    # Replace %(var)s with {{ var }}
    for key in TRANSLATION_MAPPING.get(prefix, []):
        if key in language_translations:
            mapping[key] = translation_re.sub(r'{{ \1 }}', language_translations[key])
        elif DEBUG:
            logging.warning('Translation not found for language %s: %s', lang, key)
    return {prefix: mapping}


@rest('/common/consts', 'get', read_only_access=True, silent=True, silent_result=True)
@returns(dict)
@arguments()
def api_get_consts():
    session = get_current_session()
    return {'is_shop_user': session.shop}
