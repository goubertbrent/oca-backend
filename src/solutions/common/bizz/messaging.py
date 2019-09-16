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

import json
import logging
from base64 import b64encode
from datetime import datetime
from types import NoneType

from google.appengine.api import urlfetch
from google.appengine.ext import deferred, db
from google.appengine.ext.deferred import PermanentTaskFailure

import cloudstorage
import pytz
from mcfw.consts import MISSING
from mcfw.properties import azzert, object_factory
from mcfw.rpc import returns, arguments, serialize_complex_value
from rogerthat.bizz.messaging import CanOnlySendToFriendsException
from rogerthat.bizz.service import InvalidAppIdException
from rogerthat.consts import SCHEDULED_QUEUE, ROGERTHAT_ATTACHMENTS_BUCKET, FAST_QUEUE
from rogerthat.dal import parent_key, put_and_invalidate_cache, parent_key_unsafe
from rogerthat.models import Message, ServiceIdentity, ServiceInteractionDef
from rogerthat.models.news import NewsItem
from rogerthat.models.properties.forms import FormResult, Form
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from rogerthat.service.api import messaging, system
from rogerthat.to import ReturnStatusTO, RETURNSTATUS_TO_SUCCESS
from rogerthat.to.messaging import AttachmentTO, BroadcastTargetAudienceTO, MemberTO, AnswerTO, KeyValueTO
from rogerthat.to.messaging.flow import FLOW_STEP_MAPPING
from rogerthat.to.messaging.forms import TextBlockFormTO, TextBlockTO
from rogerthat.to.messaging.service_callback_results import MessageAcknowledgedCallbackResultTO, \
    FormCallbackResultTypeTO, FormAcknowledgedCallbackResultTO, PokeCallbackResultTO, \
    FlowMemberResultCallbackResultTO, MessageCallbackResultTypeTO, FlowCallbackResultTypeTO
from rogerthat.to.news import MediaType, BaseMediaTO
from rogerthat.to.service import UserDetailsTO
from rogerthat.translations import DEFAULT_LANGUAGE
from rogerthat.utils import now, try_or_defer
from rogerthat.utils.app import create_app_user_by_email
from rogerthat.utils.channel import send_message
from solutions import translate as common_translate
from solutions.common import SOLUTION_COMMON
from solutions.common.bizz import _format_date, _format_time, timezone_offset, \
    SolutionModule, create_news_publisher
from solutions.common.bizz.appointment import appointment_asked
from solutions.common.bizz.city_vouchers import solution_voucher_resolve, solution_voucher_activate, \
    solution_voucher_redeem, solution_voucher_confirm_redeem, solution_voucher_pin_activate
from solutions.common.bizz.coupons import API_METHOD_SOLUTION_COUPON_REDEEM, solution_coupon_redeem, \
    solution_coupon_resolve, API_METHOD_SOLUTION_COUPON_RESOLVE
from solutions.common.bizz.customer_signups import deny_signup
from solutions.common.bizz.discussion_groups import poke_discussion_groups, follow_discussion_groups
from solutions.common.bizz.events import new_event_received, poke_new_event, API_METHOD_SOLUTION_EVENTS_REMIND, \
    solution_remind_event, API_METHOD_SOLUTION_EVENTS_ADDTOCALENDER, solution_add_to_calender_event, \
    API_METHOD_SOLUTION_EVENTS_REMOVE, solution_event_remove, API_METHOD_SOLUTION_EVENTS_GUEST_STATUS, \
    solution_event_guest_status, API_METHOD_SOLUTION_EVENTS_GUESTS, solution_event_guests, \
    API_METHOD_SOLUTION_CALENDAR_BROADCAST, solution_calendar_broadcast, \
    API_METHOD_SOLUTION_EVENTS_LOAD, solution_load_events
from solutions.common.bizz.forms import poke_forms
from solutions.common.bizz.group_purchase import API_METHOD_GROUP_PURCHASE_PURCHASE, solution_group_purchcase_purchase
from solutions.common.bizz.inbox import add_solution_inbox_message, create_solution_inbox_message, \
    send_styled_inbox_forwarders_email
from solutions.common.bizz.loyalty import API_METHOD_SOLUTION_LOYALTY_LOAD, solution_loyalty_load, solution_loyalty_put, \
    API_METHOD_SOLUTION_LOYALTY_PUT, API_METHOD_SOLUTION_LOYALTY_REDEEM, solution_loyalty_redeem, \
    stop_loyalty_reminders, \
    solution_loyalty_scan, API_METHOD_SOLUTION_LOYALTY_SCAN, API_METHOD_SOLUTION_LOYALTY_LOTTERY_CHANCE, \
    solution_loyalty_lottery_chance, solution_loyalty_couple, API_METHOD_SOLUTION_LOYALTY_COUPLE, \
    API_METHOD_SOLUTION_VOUCHER_RESOLVE, API_METHOD_SOLUTION_VOUCHER_ACTIVATE, \
    API_METHOD_SOLUTION_VOUCHER_REDEEM, \
    API_METHOD_SOLUTION_VOUCHER_CONFIRM_REDEEM, API_METHOD_SOLUTION_VOUCHER_PIN_ACTIVATE
from solutions.common.bizz.menu import set_menu_item_image
from solutions.common.bizz.order import order_received, poke_order
from solutions.common.bizz.pharmacy.order import pharmacy_order_received
from solutions.common.bizz.repair import repair_order_received
from solutions.common.bizz.reservation import reservation_part1, my_reservations_poke, my_reservations_overview_updated, \
    my_reservations_detail_updated
from solutions.common.bizz.sandwich import order_sandwich_received, \
    sandwich_order_from_broadcast_pressed
from solutions.common.dal import get_solution_main_branding, get_solution_settings, get_solution_identity_settings, \
    get_solution_settings_or_identity_settings, get_news_publisher_from_app_user
from solutions.common.models import SolutionMessage, SolutionScheduledBroadcast, SolutionInboxMessage, \
    SolutionSettings, SolutionMainBranding, SolutionBrandingSettings
from solutions.common.to import UrlTO, TimestampTO, SolutionInboxMessageTO
from solutions.common.utils import is_default_service_identity, create_service_identity_user, \
    create_service_identity_user_wo_default

POKE_TAG_APPOINTMENT = u"__sln__.appointment"
POKE_TAG_ASK_QUESTION = u"__sln__.question"
POKE_TAG_BROADCAST_CREATE_NEWS = u"__sln__.broadcast_create_news"
POKE_TAG_BROADCAST_CREATE_NEWS_CONNECT = u"broadcast_create_news_connect_via_scan"
POKE_TAG_DISCUSSION_GROUPS = u"__sln__.discussion_groups"
POKE_TAG_GROUP_PURCHASE = u"__sln__group_purchase"
POKE_TAG_LOCATION = u"__sln__.location"
POKE_TAG_LOYALTY = u"__sln__.loyalty"
POKE_TAG_SANDWICH_BAR = u"__sln__.sandwich_bar"
POKE_TAG_REPAIR = u"__sln__.repair"
POKE_TAG_WHEN_WHERE = u'when_where'
POKE_TAG_MENU = u'menu'
POKE_TAG_MENU_ITEM_IMAGE_UPLOAD = u'menu_item_image_upload'
POKE_TAG_EVENTS = u'agenda'
POKE_TAG_NEW_EVENT = u'agenda.new_event'
POKE_TAG_ORDER = u"__sln__.order"
POKE_TAG_PHARMACY_ORDER = u"__sln__.pharmacy_order"
POKE_TAG_FORMS = u'__sln__.forms'

POKE_TAG_EVENTS_CONNECT_VIA_SCAN = u'agenda.connect_via_scan'

POKE_TAG_INBOX_FORWARDING_REPLY = u"inbox_forwarding_reply"
POKE_TAG_INBOX_FORWARDING_REPLY_TEXT_BOX = u"inbox_forwarding_reply_text_box"
POKE_TAG_CONNECT_INBOX_FORWARDER_VIA_SCAN = u"inbox_forwarder_connect_via_scan"
POKE_TAG_LOYALTY_ADMIN = u"loyalty_admin"
POKE_TAG_LOYALTY_REMINDERS = u"loyalty_reminders"

POKE_TAG_FORM_TOMBOLA_WINNER = u'form_tombola_winner'

POKE_TAG_RESERVE_PART1 = u'reserve1'
POKE_TAG_RESERVE_PART2 = u'reserve2'
MESSAGE_TAG_RESERVE_FAIL = u'reserve_fail'
MESSAGE_TAG_RESERVE_SUCCESS = u'reserve_success'
POKE_TAG_MY_RESERVATIONS = u'my_reservations'

MESSAGE_TAG_SANDWICH_ORDER_NOW = u'sandwich.order.now'

MESSAGE_TAG_MY_RESERVATIONS_OVERVIEW = u'my-reservations-overview'
MESSAGE_TAG_MY_RESERVATIONS_DETAIL = u'my-reservations-detail'
MESSAGE_TAG_MY_RESERVATIONS_EDIT_COMMENT = u'my-reservations-edit-comment'
MESSAGE_TAG_MY_RESERVATIONS_EDIT_PEOPLE = u'my-reservations-edit-people'
MESSAGE_TAG_DENY_SIGNUP = u'deny-signup'

FMR_POKE_TAG_MAPPING = {
    POKE_TAG_SANDWICH_BAR: order_sandwich_received,
    POKE_TAG_APPOINTMENT: appointment_asked,
    POKE_TAG_REPAIR: repair_order_received,
    POKE_TAG_RESERVE_PART1: reservation_part1,
    POKE_TAG_ORDER: order_received,
    POKE_TAG_PHARMACY_ORDER: pharmacy_order_received,
    POKE_TAG_NEW_EVENT: new_event_received,
    POKE_TAG_MENU_ITEM_IMAGE_UPLOAD: set_menu_item_image,
}

POKE_TAG_MAPPING = {
    POKE_TAG_MY_RESERVATIONS: my_reservations_poke,
    POKE_TAG_NEW_EVENT: poke_new_event,
    POKE_TAG_DISCUSSION_GROUPS: poke_discussion_groups,
    POKE_TAG_ORDER: poke_order,
    POKE_TAG_FORMS: poke_forms,
}

MESSAGE_TAG_MAPPING = {
    MESSAGE_TAG_SANDWICH_ORDER_NOW: sandwich_order_from_broadcast_pressed,
    MESSAGE_TAG_MY_RESERVATIONS_OVERVIEW: my_reservations_overview_updated,
    MESSAGE_TAG_MY_RESERVATIONS_DETAIL: my_reservations_detail_updated,
    MESSAGE_TAG_DENY_SIGNUP: deny_signup,
    POKE_TAG_LOYALTY_REMINDERS: stop_loyalty_reminders,
    POKE_TAG_DISCUSSION_GROUPS: follow_discussion_groups
}

API_METHOD_MAPPING = {
    API_METHOD_SOLUTION_EVENTS_LOAD: solution_load_events,
    API_METHOD_SOLUTION_EVENTS_REMIND: solution_remind_event,
    API_METHOD_SOLUTION_EVENTS_ADDTOCALENDER: solution_add_to_calender_event,
    API_METHOD_SOLUTION_EVENTS_REMOVE: solution_event_remove,
    API_METHOD_SOLUTION_EVENTS_GUEST_STATUS: solution_event_guest_status,
    API_METHOD_SOLUTION_EVENTS_GUESTS: solution_event_guests,
    API_METHOD_SOLUTION_CALENDAR_BROADCAST: solution_calendar_broadcast,
    API_METHOD_GROUP_PURCHASE_PURCHASE: solution_group_purchcase_purchase,
    API_METHOD_SOLUTION_LOYALTY_LOAD: solution_loyalty_load,
    API_METHOD_SOLUTION_LOYALTY_SCAN: solution_loyalty_scan,
    API_METHOD_SOLUTION_LOYALTY_PUT: solution_loyalty_put,
    API_METHOD_SOLUTION_LOYALTY_REDEEM: solution_loyalty_redeem,
    API_METHOD_SOLUTION_LOYALTY_LOTTERY_CHANCE: solution_loyalty_lottery_chance,
    API_METHOD_SOLUTION_LOYALTY_COUPLE: solution_loyalty_couple,
    API_METHOD_SOLUTION_VOUCHER_RESOLVE: solution_voucher_resolve,
    API_METHOD_SOLUTION_VOUCHER_PIN_ACTIVATE: solution_voucher_pin_activate,
    API_METHOD_SOLUTION_VOUCHER_ACTIVATE: solution_voucher_activate,
    API_METHOD_SOLUTION_VOUCHER_REDEEM: solution_voucher_redeem,
    API_METHOD_SOLUTION_VOUCHER_CONFIRM_REDEEM: solution_voucher_confirm_redeem,
    API_METHOD_SOLUTION_COUPON_REDEEM: solution_coupon_redeem,
    API_METHOD_SOLUTION_COUPON_RESOLVE: solution_coupon_resolve
}

FLOW_STATISTICS_MAPPING = {
    POKE_TAG_ORDER: SolutionModule.ORDER,
    POKE_TAG_SANDWICH_BAR: SolutionModule.SANDWICH_BAR,
    POKE_TAG_APPOINTMENT: SolutionModule.APPOINTMENT,
    POKE_TAG_REPAIR: SolutionModule.REPAIR,
    POKE_TAG_RESERVE_PART1: SolutionModule.RESTAURANT_RESERVATION,
    POKE_TAG_PHARMACY_ORDER: SolutionModule.PHARMACY_ORDER,
    POKE_TAG_ASK_QUESTION: SolutionModule.ASK_QUESTION
}


def _get_step_with_id(steps, step_id):
    for step in reversed(steps):
        if step.step_id == step_id:
            return step
    return None


@returns(NoneType)
@arguments(url=unicode, language=unicode)
def validate_broadcast_url(url, language=DEFAULT_LANGUAGE):
    if url is None or not (url.startswith("http://") or url.startswith("https://")):
        logging.debug("Invalid url (%(url)s). It must be reachable over http or https." % {'url': url})
        raise BusinessException(common_translate(language, SOLUTION_COMMON,
                                                 "Invalid url (%(url)s). It must be reachable over http or https.",
                                                 url=url))

    logging.info('validating url: %s', url)
    try:
        result = urlfetch.fetch(url, method="HEAD", deadline=10)
    except:
        logging.debug("Could not validate url (%(url)s)" % {'url': url}, exc_info=True)
        raise BusinessException(common_translate(language, SOLUTION_COMMON, "Could not validate url %(url)s", url=url))

    if result.status_code != 200:
        logging.debug("Could not validate url (%s). Response status code: %s", url, result.status_code)
        try:
            result = urlfetch.fetch(url, method="GET", deadline=10)
        except:
            raise BusinessException(
                common_translate(language, SOLUTION_COMMON, "Could not validate url %(url)s", url=url))

        if result.status_code != 200:
            logging.debug("Could not validate url via GET. Response status code: %s", result.status_code)
            raise BusinessException(
                common_translate(language, SOLUTION_COMMON, "Could not validate url %(url)s", url=url))


@returns(ReturnStatusTO)
@arguments(service_user=users.User, service_identity=unicode, broadcast_type=unicode, message=unicode,
           target_audience_enabled=bool, target_audience_min_age=int,
           target_audience_max_age=int, target_audience_gender=unicode, msg_attachments=[AttachmentTO],
           msg_urls=[UrlTO], broadcast_date=TimestampTO, broadcast_to_all_locations=bool)
def broadcast_send(service_user, service_identity, broadcast_type, message,
                   target_audience_enabled=False, target_audience_min_age=0, target_audience_max_age=0,
                   target_audience_gender="MALE_OR_FEMALE", msg_attachments=None, msg_urls=None,
                   broadcast_date=None, broadcast_to_all_locations=False):
    # function that takes message type and message text and spreads it to users.
    try:
        sln_settings = get_solution_settings(service_user)
        attachments = list()
        error_msgs = list()
        if msg_attachments:
            for ma in msg_attachments:
                at = AttachmentTO()
                at.download_url = ma.download_url
                at.name = ma.name
                # extract the cloudstorage file path from the url and determine content type and size
                filename = ma.download_url.split(ROGERTHAT_ATTACHMENTS_BUCKET)[1]
                stat = cloudstorage.stat(ROGERTHAT_ATTACHMENTS_BUCKET + filename)
                at.size = stat.st_size
                at.content_type = stat.content_type.decode('utf-8')
                attachments.append(at)

        if msg_urls:
            for mu in msg_urls:
                mu.url = mu.url.strip()
                try:
                    if not mu.url.startswith("mailto:"):
                        validate_broadcast_url(mu.url, sln_settings.main_language)
                except BusinessException as e:
                    error_msgs.append(e.message)

        if broadcast_date:
            now_ = now()
            broadcast_epoch = broadcast_date.toEpoch()
            countdown = (broadcast_epoch + timezone_offset(sln_settings.timezone)) - now_
            if countdown >= 60 * 60 * 24 * 30:
                error_msgs.append(common_translate(sln_settings.main_language, SOLUTION_COMMON,
                                                   u'broadcast-schedule-too-far-in-future'))

        if error_msgs:
            logging.info(error_msgs)
            return ReturnStatusTO.create(False, "\n".join(error_msgs))

        send_broadcast(service_user, service_identity, broadcast_type, message, target_audience_enabled,
                       target_audience_min_age, target_audience_max_age, target_audience_gender, attachments, msg_urls,
                       broadcast_date, broadcast_to_all_locations)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException as e:
        return ReturnStatusTO.create(False, e.message)


@returns(PokeCallbackResultTO)
@arguments(service_user=users.User, email=unicode, tag=unicode, result_key=unicode, context=unicode,
           service_identity=unicode, user_details=[UserDetailsTO])
def poke_invite(service_user, email, tag, result_key, context, service_identity, user_details):
    from solutions.common.handlers import JINJA_ENVIRONMENT

    sln_settings, main_branding = db.get([SolutionSettings.create_key(service_user),
                                          SolutionMainBranding.create_key(service_user)])
    flow_params = dict(branding_key=main_branding.branding_key, language=sln_settings.main_language)
    flow = JINJA_ENVIRONMENT.get_template('flows/welcome.xml').render(flow_params)

    poke_result = PokeCallbackResultTO()
    poke_result.type = u'flow'
    result = FlowCallbackResultTypeTO()
    result.tag = tag
    result.flow = flow if isinstance(flow, unicode) else flow.decode("utf8")
    result.force_language = None
    poke_result.value = result
    return poke_result


POKE_TAG_MAPPING[ServiceInteractionDef.TAG_INVITE] = poke_invite


@returns(PokeCallbackResultTO)
@arguments(service_user=users.User, email=unicode, tag=unicode, result_key=unicode, context=unicode,
           service_identity=unicode, user_details=[UserDetailsTO])
def poke_inbox_forwarder_connect_via_scan(service_user, email, tag, result_key, context, service_identity,
                                          user_details):
    app_user = user_details[0].toAppUser()
    app_user_email = app_user.email()
    if is_default_service_identity(service_identity):
        sln_i_settings = get_solution_settings(service_user)
    else:
        sln_i_settings = get_solution_identity_settings(service_user, service_identity)
    if app_user_email in sln_i_settings.inbox_forwarders:
        return
    sln_i_settings.inbox_forwarders.append(app_user_email)
    sln_i_settings.put()
    send_message(service_user, u"solutions.common.inbox.new.forwarder.via.scan",
                 service_identity=service_identity,
                 key=app_user_email,
                 label=user_details[0].name)


POKE_TAG_MAPPING[POKE_TAG_CONNECT_INBOX_FORWARDER_VIA_SCAN] = poke_inbox_forwarder_connect_via_scan


@returns(PokeCallbackResultTO)
@arguments(service_user=users.User, email=unicode, tag=unicode, result_key=unicode, context=unicode,
           service_identity=unicode, user_details=[UserDetailsTO])
def poke_broadcast_create_news_connect_via_scan(service_user, email, tag, result_key, context, service_identity,
                                                user_details):
    sln_settings = get_solution_settings(service_user)
    app_user = user_details[0].toAppUser()
    create_news_publisher(app_user, service_user,
                          sln_settings.solution)
    send_message(service_user, u"solution.common.settings.roles.updated")


POKE_TAG_MAPPING[POKE_TAG_BROADCAST_CREATE_NEWS_CONNECT] = poke_broadcast_create_news_connect_via_scan


@returns(FlowMemberResultCallbackResultTO)
@arguments(service_user=users.User, message_flow_run_id=unicode, member=unicode,
           steps=[object_factory("step_type", FLOW_STEP_MAPPING)], end_id=unicode, end_message_flow_id=unicode,
           parent_message_key=unicode, tag=unicode, result_key=unicode, flush_id=unicode, flush_message_flow_id=unicode,
           service_identity=unicode, user_details=[UserDetailsTO])
def broadcast_create_news_item(service_user, message_flow_run_id, member, steps, end_id, end_message_flow_id,
                               parent_message_key,
                               tag, result_key, flush_id, flush_message_flow_id, service_identity, user_details):
    from solutions.common.bizz.news import put_news_item
    logging.debug('creating a news item from the flow result...')

    def result_message(message):
        result = FlowMemberResultCallbackResultTO()
        result.type = u'message'
        result.value = MessageCallbackResultTypeTO()
        result.value.message = unicode(message)
        result.value.answers = []
        result.value.attachments = []
        result.value.flags = Message.FLAG_ALLOW_DISMISS
        result.value.alert_flags = 1
        result.value.branding = get_solution_main_branding(service_user).branding_key
        result.value.dismiss_button_ui_flags = 0
        result.value.step_id = u''
        result.value.tag = POKE_TAG_BROADCAST_CREATE_NEWS
        return result

    # check if the app user is a news publisher
    user_details = user_details[0]
    app_user = user_details.toAppUser()
    solution = get_solution_settings(service_user).solution
    if not get_news_publisher_from_app_user(app_user, service_user, solution):
        return result_message(common_translate(user_details.language,
                                               SOLUTION_COMMON,
                                               u'no_permission'))

    news_type = NewsItem.TYPE_NORMAL
    first_step = steps[0]
    if first_step.step_id == u'message_news_type':
        steps = steps[1:]
        if first_step.answer_id.endswith(u'coupon'):
            news_type = NewsItem.TYPE_QR_CODE

    if len(steps) == 6:
        # upload a photo is included
        (content_title_step, content_message_step,
         cover_photo_step, image_step, group_type_step, app_ids_step) = steps
    else:
        image_step = None
        (content_title_step, content_message_step,
         cover_photo_step, group_type_step, app_ids_step) = steps

    title = content_title_step.form_result.result.value
    message = content_message_step.form_result.result.value

    image = ''
    # use cover photo
    if cover_photo_step.answer_id.endswith(u'use_cover_photo'):
        branding_settings = db.get(SolutionBrandingSettings.create_key(service_user))
        if branding_settings and branding_settings.logo_url:
            image = branding_settings.logo_url

    # use an uploaded photo
    if image_step and image_step.form_result:
        image_url = image_step.form_result.result.value
        if image_url:
            # get the image content and encode it (base64)
            # the image should be as <meta,img64data>
            result = urlfetch.fetch(image_url, deadline=30)

            if result.status_code != 200:
                message = common_translate(user_details.language,
                                           SOLUTION_COMMON,
                                           u'broadcast_could_not_get_item_photo')
                return result_message(message)

            image = ',' + b64encode(result.content)

    group_type = group_type_step.form_result.result.value
    app_ids = app_ids_step.form_result.result.values
    if is_default_service_identity(service_identity):
        service_identity_user = create_service_identity_user(service_user)
    else:
        service_identity_user = create_service_identity_user(service_user,
                                                             service_identity)

    try:
        media = BaseMediaTO(type=MediaType.IMAGE, content=image) if image else None
        put_news_item(service_identity_user, title, message, action_button=None, news_type=news_type,
                      qr_code_caption=title, app_ids=app_ids, scheduled_at=0, news_id=None, media=media,
                      group_type=group_type)
        message = common_translate(user_details.language,
                                   SOLUTION_COMMON, u'news_item_published')
        result = result_message(message)
    except BusinessException as e:
        sln_settings = get_solution_settings(service_user)
        try:
            message = common_translate(sln_settings.main_language, SOLUTION_COMMON, e.message)
        except ValueError:
            message = e.message
        result = result_message(message)

    return result


FMR_POKE_TAG_MAPPING[POKE_TAG_BROADCAST_CREATE_NEWS] = broadcast_create_news_item


@returns()
@arguments(service_user=users.User, message_flow_run_id=unicode, member=unicode,
           steps=[object_factory("step_type", FLOW_STEP_MAPPING)], end_id=unicode, end_message_flow_id=unicode,
           parent_message_key=unicode, tag=unicode, result_key=unicode, flush_id=unicode, flush_message_flow_id=unicode,
           service_identity=unicode, user_details=[UserDetailsTO])
def _question_asked(service_user, message_flow_run_id, member, steps, end_id, end_message_flow_id, parent_message_key,
                    tag, result_key, flush_id, flush_message_flow_id, service_identity, user_details):
    logging.info("_flow_member_result_ask_question: \n %s" % steps)
    step = _get_step_with_id(steps, 'message_question') or _get_step_with_id(steps,
                                                                             'message_1')  # message_1 for backwards compatibility
    azzert(step,
           "Did not find step with id 'message_question'. Can not process message_flow_member_result with tag %s" % tag)

    if step.answer_id == 'positive' and step.form_result and step.form_result.result:
        logging.info("Saving question from %s" % user_details[0].email)
        msg = step.form_result.result.value
        message = create_solution_inbox_message(service_user, service_identity,
                                                SolutionInboxMessage.CATEGORY_ASK_QUESTION, None, False, user_details,
                                                step.acknowledged_timestamp, msg, True)
        app_user = user_details[0].toAppUser()
        send_inbox_forwarders_message(service_user, service_identity, app_user, msg, {
            'if_name': user_details[0].name,
            'if_email': user_details[0].email
        }, message_key=message.solution_inbox_message_key, reply_enabled=message.reply_enabled)
        sln_settings = get_solution_settings(service_user)
        sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, service_identity)
        send_message(service_user, u"solutions.common.messaging.update",
                     service_identity=service_identity,
                     message=serialize_complex_value(
                         SolutionInboxMessageTO.fromModel(message, sln_settings, sln_i_settings, True),
                         SolutionInboxMessageTO, False))


@returns()
@arguments(service_user=users.User, message_flow_run_id=unicode, member=unicode,
           steps=[object_factory("step_type", FLOW_STEP_MAPPING)], end_id=unicode, end_message_flow_id=unicode,
           parent_message_key=unicode, tag=unicode, result_key=unicode, flush_id=unicode, flush_message_flow_id=unicode,
           service_identity=unicode, user_details=[UserDetailsTO])
def question_asked(service_user, message_flow_run_id, member, steps, end_id, end_message_flow_id, parent_message_key,
                   tag, result_key, flush_id, flush_message_flow_id, service_identity, user_details):
    try_or_defer(_question_asked, service_user, message_flow_run_id, member, steps, end_id, end_message_flow_id,
                 parent_message_key, tag, result_key, flush_id, flush_message_flow_id, service_identity, user_details,
                 log_first_error=True)


@returns(MessageAcknowledgedCallbackResultTO)
@arguments(service_user=users.User, status=int, answer_id=unicode, received_timestamp=int, member=unicode,
           message_key=unicode, tag=unicode, acked_timestamp=int, parent_message_key=unicode, result_key=unicode,
           service_identity=unicode, user_details=[UserDetailsTO])
def inbox_forwarding_reply_pressed(service_user, status, answer_id, received_timestamp, member, message_key, tag,
                                   acked_timestamp, parent_message_key, result_key, service_identity, user_details):
    if not answer_id:
        return None  # status is STATUS_RECEIVED or user dismissed

    info = json.loads(answer_id)
    human_user_email = info['email']

    result = MessageAcknowledgedCallbackResultTO()
    result.type = u'form'
    result.value = FormCallbackResultTypeTO()
    result.value.alert_flags = 0
    result.value.branding = get_solution_main_branding(service_user).branding_key
    result.value.flags = Message.FLAG_ALLOW_DISMISS | Message.FLAG_AUTO_LOCK
    result.value.form = TextBlockFormTO()

    result.value.form.negative_button = common_translate(user_details[0].language, SOLUTION_COMMON, u'Cancel')
    result.value.form.negative_button_ui_flags = 0
    result.value.form.negative_confirmation = None
    result.value.form.positive_button = common_translate(user_details[0].language, SOLUTION_COMMON, u'Send')
    result.value.form.positive_button_ui_flags = 0
    result.value.form.positive_confirmation = None
    result.value.form.javascript_validation = None
    result.value.form.type = TextBlockTO.TYPE
    result.value.form.widget = TextBlockTO()
    result.value.form.widget.max_chars = 500
    result.value.form.widget.place_holder = u''
    result.value.form.widget.value = u''

    result.value.message = common_translate(user_details[0].language, SOLUTION_COMMON, u'inbox-forwarding-reply-to') % {
        'if_name': user_details[0].name,
        'if_email': human_user_email
    }
    result.value.tag = POKE_TAG_INBOX_FORWARDING_REPLY_TEXT_BOX + answer_id
    result.value.attachments = []
    result.value.step_id = None
    return result


# deprecated since we used chats
@returns(FormAcknowledgedCallbackResultTO)
@arguments(service_user=users.User, status=int, form_result=FormResult, answer_id=unicode, member=unicode,
           message_key=unicode, tag=unicode, received_timestamp=int, acked_timestamp=int, parent_message_key=unicode,
           result_key=unicode, service_identity=unicode, user_details=[UserDetailsTO])
def reply_on_inbox_forwarding(service_user, status, form_result, answer_id, member, message_key, tag,
                              received_timestamp, acked_timestamp, parent_message_key, result_key,
                              service_identity, user_details):
    if answer_id != Form.POSITIVE:
        return None

    info = json.loads(tag[len(POKE_TAG_INBOX_FORWARDING_REPLY_TEXT_BOX):])

    if info.get("message_key"):
        m = SolutionMessage.get(info['message_key'])
        if m and not m.deleted:
            now_ = now()
            msg = form_result.result.value or ''
            human_user_email = info['email']
            app_id = info['app_id']

            memberTO = MemberTO()
            memberTO.member = human_user_email
            memberTO.app_id = app_id
            memberTO.alert_flags = Message.ALERT_FLAG_VIBRATE
            messaging.send(parent_key=None,
                           parent_message_key=None,
                           message=msg,
                           answers=[],
                           flags=Message.FLAG_ALLOW_DISMISS,
                           members=[memberTO],
                           branding=get_solution_main_branding(service_user).branding_key,
                           tag=None,
                           service_identity=service_identity)
            m.deleted = True
            m.reply = form_result.result.value or ''
            m.put()
            sim_parent, _ = add_solution_inbox_message(service_user, m.solution_inbox_message_key, True, user_details,
                                                       now_, msg)
            sln_settings = get_solution_settings(service_user)
            sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, service_identity)
            send_message(service_user, u"solutions.common.messaging.update",
                         service_identity=service_identity,
                         message=serialize_complex_value(
                             SolutionInboxMessageTO.fromModel(sim_parent, sln_settings, sln_i_settings, True),
                             SolutionInboxMessageTO, False))
    return None


@returns(NoneType)
@arguments(service_user=users.User, sim_key=unicode, message=unicode)
def send_reply(service_user, sim_key, message):
    now_ = now()
    sim_parent, _ = add_solution_inbox_message(service_user, sim_key, True, None, now_, message, mark_as_unread=False,
                                               mark_as_read=True)

    sln_settings = get_solution_settings(service_user)
    sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, sim_parent.service_identity)
    send_message(service_user, u"solutions.common.messaging.update",
                 service_identity=sim_parent.service_identity,
                 message=serialize_complex_value(
                     SolutionInboxMessageTO.fromModel(sim_parent, sln_settings, sln_i_settings, True),
                     SolutionInboxMessageTO, False))

    send_inbox_forwarders_message(service_user, sim_parent.service_identity, None, message, {
        'if_name': sim_parent.sender.name,
        'if_email': sim_parent.sender.email
    }, message_key=sim_parent.solution_inbox_message_key, reply_enabled=sim_parent.reply_enabled)


@returns(NoneType)
@arguments(service_user=users.User, service_identity=unicode)
def delete_all_trash(service_user, service_identity):
    deferred.defer(_delete_all_trash, service_user, service_identity)


@returns(NoneType)
@arguments(service_user=users.User, service_identity=unicode)
def _delete_all_trash(service_user, service_identity):
    service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
    ancestor = parent_key_unsafe(service_identity_user, SOLUTION_COMMON)
    qry = SolutionInboxMessage.all().ancestor(ancestor).filter('parent_message_key =', None)
    qry.filter('deleted =', False)
    qry.filter('trashed =', True)
    message_keys = []
    to_put = []
    for sim in qry:
        sim.deleted = True
        to_put.append(sim)
        message_keys.append(sim.solution_inbox_message_key)
    db.put(to_put)
    send_message(service_user, u"solutions.common.messaging.deleted",
                 service_identity=service_identity,
                 message_keys=message_keys)


@returns(NoneType)
@arguments(service_user=users.User, service_identity=unicode, broadcast_type=unicode, message=unicode,
           target_audience_enabled=bool,
           target_audience_min_age=int, target_audience_max_age=int, target_audience_gender=unicode,
           attachments=[AttachmentTO], urls=[UrlTO], broadcast_date=TimestampTO, broadcast_to_all_locations=bool)
def send_broadcast(service_user, service_identity, broadcast_type, message, target_audience_enabled,
                   target_audience_min_age,
                   target_audience_max_age, target_audience_gender, attachments, urls, broadcast_date,
                   broadcast_to_all_locations=False):
    sln_main_branding = get_solution_main_branding(service_user)
    branding = sln_main_branding.branding_key if sln_main_branding else None
    if target_audience_enabled:
        target_audience = BroadcastTargetAudienceTO()
        target_audience.min_age = target_audience_min_age
        target_audience.max_age = target_audience_max_age
        target_audience.gender = target_audience_gender
        target_audience.app_id = MISSING
    else:
        target_audience = None

    answers = []
    if urls:
        for url in urls:
            btn = AnswerTO()
            btn.id = u'broadcast-website: %s' % url.url
            btn.type = u'button'
            btn.caption = url.name
            btn.action = url.url
            btn.ui_flags = 0
            answers.append(btn)

    sln_settings = get_solution_settings(service_user)

    now_ = now()
    ssb = SolutionScheduledBroadcast(parent=parent_key(service_user, SOLUTION_COMMON))
    if broadcast_date:
        broadcast_epoch = broadcast_date.toEpoch()
        countdown = (broadcast_epoch + timezone_offset(sln_settings.timezone)) - now_
        if countdown > 0:
            ssb.deleted = False
            ssb.put()
            logging.debug("Scheduled broadcast in %s seconds", countdown)
            deferred.defer(_send_scheduled_broadcast, service_user, ssb.key_str,
                           _countdown=countdown, _queue=SCHEDULED_QUEUE)
    else:
        ssb.deleted = True  # Save non-delayed broadcasts as well for statistical purposes.
        broadcast_epoch = now_
    ssb.service_identity = service_identity
    ssb.timestamp = now_
    ssb.broadcast_epoch = broadcast_epoch
    ssb.broadcast_type = broadcast_type
    ssb.message = message
    ssb.target_audience_enabled = target_audience_enabled
    ssb.target_audience_min_age = target_audience_min_age
    ssb.target_audience_max_age = target_audience_max_age
    ssb.target_audience_gender = target_audience_gender
    ssb.json_attachments = json.dumps(serialize_complex_value(attachments, AttachmentTO, True))
    ssb.json_urls = json.dumps(serialize_complex_value(urls, UrlTO, True))
    ssb.broadcast_to_all_locations = broadcast_to_all_locations
    if broadcast_date:
        ssb.put()
        return

    if broadcast_to_all_locations and sln_settings.identities:
        identities = [ServiceIdentity.DEFAULT]
        identities.extend(sln_settings.identities)
    else:
        identities = [service_identity if service_identity else ServiceIdentity.DEFAULT]

    ssb.statistics_keys = []
    ssb.identities = []
    for service_identity in identities:
        result = messaging.broadcast(broadcast_type=broadcast_type,
                                     message=message,
                                     answers=answers,
                                     flags=Message.FLAG_ALLOW_DISMISS,
                                     branding=branding,
                                     tag=None,
                                     service_identity=service_identity,
                                     target_audience=target_audience,
                                     attachments=attachments)
        if result.statistics_key:
            ssb.statistics_keys.append(result.statistics_key)
            ssb.identities.append(service_identity)

    if not ssb.statistics_keys:
        raise BusinessException(
            common_translate(sln_settings.main_language, SOLUTION_COMMON, "Broadcast failed, no connected users"))
    ssb.put()

    sln_settings.broadcast_to_all_locations = broadcast_to_all_locations
    put_and_invalidate_cache(sln_settings)


@returns(NoneType)
@arguments(service_user=users.User, str_key=unicode)
def _send_scheduled_broadcast(service_user, str_key):
    ssb = SolutionScheduledBroadcast.get(str_key)
    if not ssb:
        return
    azzert(ssb.service_user == service_user)
    if not ssb.deleted:
        users.set_user(service_user)
        try:
            send_broadcast(service_user, ssb.service_identity, ssb.broadcast_type, ssb.message,
                           ssb.target_audience_enabled,
                           ssb.target_audience_min_age, ssb.target_audience_max_age, ssb.target_audience_gender,
                           ssb.attachments, ssb.urls, None, ssb.broadcast_to_all_locations)
        finally:
            users.clear_user()
        ssb.delete()


@returns(NoneType)
@arguments(service_user=users.User, key=unicode)
def delete_scheduled_broadcast(service_user, key):
    service_user = users.get_current_user()
    ssb = SolutionScheduledBroadcast.get(key)
    if ssb:
        if ssb.service_user != service_user:
            raise BusinessException("No permission to delete this scheduled broadcast")
        ssb.delete()


@returns(NoneType)
@arguments(service_user=users.User, service_identity=unicode, app_user=users.User, body=unicode, msg_params=dict,
           solution=unicode,
           message_key=unicode, attachments=[AttachmentTO], reply_enabled=bool, send_reminder=bool, answers=[AnswerTO],
           store_tag=unicode, flags=(int, long))
def send_inbox_forwarders_message(service_user, service_identity, app_user, body, msg_params, solution=SOLUTION_COMMON,
                                  message_key=None, attachments=None, reply_enabled=False, send_reminder=True,
                                  answers=None, store_tag=None, flags=Message.FLAG_ALLOW_DISMISS):
    deferred.defer(_send_inbox_forwarders_message, service_user, service_identity, app_user, body, msg_params, solution,
                   message_key, attachments, reply_enabled, send_reminder, answers, store_tag, flags,
                   _transactional=db.is_in_transaction(), _queue=FAST_QUEUE)


@returns(NoneType)
@arguments(service_user=users.User, service_identity=unicode, app_user=users.User, body=unicode, msg_params=dict,
           solution=unicode,
           message_key=unicode, attachments=[AttachmentTO], reply_enabled=bool, send_reminder=bool, answers=[AnswerTO],
           store_tag=unicode, flags=(int, long))
def _send_inbox_forwarders_message(service_user, service_identity, app_user, body, msg_params, solution=SOLUTION_COMMON,
                                   message_key=None, attachments=None, reply_enabled=False, send_reminder=True,
                                   answers=None, store_tag=None, flags=Message.FLAG_ALLOW_DISMISS):
    try_or_defer(_send_inbox_forwarders_message_by_email, service_user, service_identity, app_user, msg_params,
                 message_key, send_reminder, _queue=FAST_QUEUE)
    try_or_defer(_send_inbox_forwarders_message_by_app, service_user, service_identity, app_user, body, msg_params,
                 solution, message_key, attachments, reply_enabled, send_reminder, answers, store_tag, flags,
                 _queue=FAST_QUEUE)


@returns(NoneType)
@arguments(service_user=users.User, service_identity=unicode, app_user=users.User, msg_params=dict, message_key=unicode,
           send_reminder=bool)
def _send_inbox_forwarders_message_by_email(service_user, service_identity, app_user, msg_params, message_key=None,
                                            send_reminder=True):
    if not (send_reminder and app_user and message_key):
        return

    if is_default_service_identity(service_identity):
        sln_i_settings = get_solution_settings(service_user)
    else:
        sln_i_settings = get_solution_identity_settings(service_user, service_identity)

    if not sln_i_settings.inbox_mail_forwarders:
        return

    message = SolutionInboxMessage.get(message_key)
    sender_app_user = create_app_user_by_email(message.sender.email, message.sender.app_id)
    if app_user in sln_i_settings.inbox_forwarders and sender_app_user != app_user:
        return

    send_styled_inbox_forwarders_email(service_user, message_key, msg_params)


@returns(NoneType)
@arguments(service_user=users.User, service_identity=unicode, app_user=users.User, body=unicode, msg_params=dict,
           solution=unicode,
           message_key=unicode, attachments=[AttachmentTO], reply_enabled=bool, send_reminder=bool, answers=[AnswerTO],
           store_tag=unicode, flags=(int, long))
def _send_inbox_forwarders_message_by_app(service_user, service_identity, app_user, body, msg_params,
                                          solution=SOLUTION_COMMON,
                                          message_key=None, attachments=None, reply_enabled=False, send_reminder=True,
                                          answers=None, store_tag=None, flags=Message.FLAG_ALLOW_DISMISS):
    if answers is None:
        answers = list()

    sln_settings = get_solution_settings(service_user)
    date_sent = datetime.fromtimestamp(now(), pytz.timezone(sln_settings.timezone))
    msg_params['if_date'] = _format_date(sln_settings.main_language, date_sent)
    msg_params['if_time'] = _format_time(sln_settings.main_language, date_sent)

    sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, service_identity)
    members = [MemberTO.from_user(users.User(f)) for f in sln_i_settings.inbox_forwarders]
    inbox_forwarders = list(members)
    tag = POKE_TAG_INBOX_FORWARDING_REPLY + json.dumps({'message_key': message_key})
    if not reply_enabled:
        while inbox_forwarders:
            users.set_user(service_user)
            try:
                messaging.send(parent_key=None,
                               parent_message_key=None,
                               message=body,
                               answers=answers,
                               flags=flags,
                               members=inbox_forwarders,
                               branding=get_solution_main_branding(service_user).branding_key,
                               tag=tag,
                               service_identity=service_identity,
                               attachments=attachments)
                break
            except CanOnlySendToFriendsException as e:
                logging.exception('Tried to forward inbox message to a non-friend: %s', e.fields)
                for member in inbox_forwarders:
                    if member.member == e.fields['member'] and member.app_id == e.fields['app_id']:
                        inbox_forwarders.remove(member)
                        break
                else:
                    raise PermanentTaskFailure('Non-friend not found in members. Should never happen.')
                sln_i_settings.inbox_forwarders.remove(
                    create_app_user_by_email(e.fields['member'], e.fields['app_id']).email())
            except InvalidAppIdException as e:
                logging.warn(e)
                app_id = e.fields['app_id']
                for member in inbox_forwarders:
                    if member.app_id == app_id:
                        inbox_forwarders.remove(member)
                        sln_i_settings.inbox_forwarders.remove(
                            create_app_user_by_email(member.member, member.app_id).email())
            finally:
                users.clear_user()
                if inbox_forwarders != members:
                    sln_i_settings.put()
    else:
        message = SolutionInboxMessage.get(message_key)
        users.set_user(service_user)
        try:
            if app_user and app_user.email() not in sln_i_settings.inbox_forwarders:
                sender_member = MemberTO.from_user(app_user)
            else:
                sender_member = None

            if not message.message_key:
                from rogerthat.service.api.messaging import ChatFlags
                if not sender_member:
                    members.append(
                        MemberTO.from_user(create_app_user_by_email(message.sender.email, message.sender.app_id)))
                flags = ChatFlags.ALLOW_ANSWER_BUTTONS | ChatFlags.ALLOW_PICTURE | ChatFlags.ALLOW_VIDEO
                metadata = []
                metadata.append(KeyValueTO.create(common_translate(sln_settings.main_language, SOLUTION_COMMON, "Date"),
                                                  "%s %s" % (msg_params['if_date'], msg_params['if_time'])))
                avatar = system.get_avatar()
                try:
                    message.message_key = messaging.start_chat(list(set(members)),
                                                               common_translate(sln_settings.main_language,
                                                                                SOLUTION_COMMON,
                                                                                message.chat_topic_key),
                                                               "%s <%s>" % (
                                                                   msg_params['if_name'], msg_params['if_email']),
                                                               service_identity=service_identity,
                                                               tag=tag,
                                                               flags=flags,
                                                               metadata=metadata,
                                                               avatar=avatar,
                                                               default_sticky=True)
                except InvalidAppIdException as e:
                    app_id = e.fields['app_id']
                    for member in inbox_forwarders:
                        if member.app_id == app_id:
                            inbox_forwarders.remove(member)
                            sln_i_settings.inbox_forwarders.remove(
                                create_app_user_by_email(member.member, member.app_id).email())

                    if inbox_forwarders != members:
                        sln_i_settings.put()

                    raise

                if sender_member:
                    message.awaiting_first_message = True
                message.put()
            else:
                if sender_member:
                    members.append(sender_member)
                elif app_user is None:
                    members.append(
                        MemberTO.from_user(create_app_user_by_email(message.sender.email, message.sender.app_id)))
                messaging.add_chat_members(message.message_key, list(set(members)))

            chat_message_key = messaging.send_chat_message(message.message_key, body, answers, attachments,
                                                           sender_member, None, True, tag=tag)
            if store_tag:
                message_key_by_tag = dict()
                if message.message_key_by_tag:
                    message_key_by_tag = json.loads(message.message_key_by_tag)
                message_key_by_tag[store_tag] = chat_message_key

                message.message_key_by_tag = json.dumps(message_key_by_tag)
                message.put()
        except:
            logging.error('send_inbox_forwarders_message chat error', exc_info=True, _suppress=False)
            raise
        finally:
            users.clear_user()


FMR_POKE_TAG_MAPPING[POKE_TAG_ASK_QUESTION] = question_asked
MESSAGE_TAG_MAPPING[POKE_TAG_INBOX_FORWARDING_REPLY] = inbox_forwarding_reply_pressed
