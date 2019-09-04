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

from datetime import datetime, timedelta, time
import json
import logging
from types import NoneType, FunctionType

import pytz

from babel.dates import format_date, format_time
from google.appengine.ext import db, deferred
from mcfw.properties import azzert, object_factory
from mcfw.rpc import returns, arguments, serialize_complex_value
from rogerthat.dal import put_and_invalidate_cache, parent_key_unsafe
from rogerthat.models import Message
from rogerthat.models.properties.forms import Form, FormResult
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from rogerthat.service.api import system, messaging
from rogerthat.to.messaging import AnswerTO, MemberTO
from rogerthat.to.messaging.flow import FLOW_STEP_MAPPING
from rogerthat.to.messaging.forms import TextBlockFormTO, TextBlockTO, SingleSliderFormTO, SingleSliderTO
from rogerthat.to.messaging.service_callback_results import FlowMemberResultCallbackResultTO, \
    FlowCallbackResultTypeTO, MessageCallbackResultTypeTO, PokeCallbackResultTO, MessageAcknowledgedCallbackResultTO, \
    FormCallbackResultTypeTO, FormAcknowledgedCallbackResultTO
from rogerthat.to.service import UserDetailsTO
from rogerthat.translations import DEFAULT_LANGUAGE
from rogerthat.utils import bizz_check, unset_flag, set_flag, is_flag_set, now, get_epoch_from_datetime
from rogerthat.utils.app import create_app_user, create_app_user_by_email
from rogerthat.utils.channel import send_message
from rogerthat.utils.service import get_service_user_from_service_identity_user
from solutions import translate as common_translate
from solutions.common import SOLUTION_COMMON
from solutions.common.bizz import _get_value
from solutions.common.bizz.holiday import is_in_holiday
from solutions.common.bizz.inbox import add_solution_inbox_message, create_solution_inbox_message
from solutions.common.bizz.reservation.job import handle_shift_updates
from solutions.common.dal import get_solution_main_branding, get_solution_settings, \
    get_solution_settings_or_identity_settings, get_solution_identity_settings
from solutions.common.dal.reservations import get_restaurant_profile, get_planned_reservations_by_user, \
    get_restaurant_settings, get_restaurant_reservation, get_reservations, get_upcoming_planned_reservations_by_table, \
    clear_table_id_in_reservations
from solutions.common.models import SolutionInboxMessage
from solutions.common.models.properties import SolutionUser
from solutions.common.models.reservation import RestaurantReservation, RestaurantSettings, RestaurantTable
from solutions.common.models.reservation.properties import Shift, Shifts
from solutions.common.to import TimestampTO, SolutionInboxMessageTO
from solutions.common.to.reservation import RestaurantReservationStatisticsTO, RestaurantReservationStatisticTO, \
    RestaurantShiftTO, TableTO
from solutions.common.utils import create_service_identity_user_wo_default, is_default_service_identity


STATUS_AVAILABLE = u'available'
STATUS_RESTAURANT_CLOSED = u'restaurant-closed'
STATUS_KITCHEN_CLOSED = u'kitchen-closed'
STATUS_PAST_RESERVATION = u'past-reservation'
STATUS_SHORT_NOTICE = u'short-notice'
STATUS_TOO_MANY_PEOPLE = u'too-many-people'
STATUS_NO_TABLES = u'no-tables'
STATUS_IN_HOLIDAY = u'in-holiday'


class ShiftOverlapException(BusinessException):
    pass

class ShiftConfigurationException(BusinessException):
    pass

class ReservationConflictException(BusinessException):
    pass

class InvalidTableException(BusinessException):
    pass


@returns(RestaurantSettings)
@arguments(service_user=users.User, service_identity=unicode, translate=FunctionType, default_lang=unicode)
def put_default_restaurant_settings(service_user, service_identity, translate, default_lang):
    service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
    settings = RestaurantSettings(key=RestaurantSettings.create_key(service_identity_user))
    settings.shifts = Shifts()

    shift = Shift()
    shift.name = translate('shift-lunch')
    shift.capacity = 50
    shift.max_group_size = 6
    shift.leap_time = 30
    shift.threshold = 70
    shift.start = 12 * 60 * 60
    shift.end = 14 * 60 * 60
    shift.days = [1, 2, 3, 4, 5]
    shift.comment = translate('shift-comment0')
    settings.shifts.add(shift)

    shift = Shift()
    shift.name = translate('shift-dinner')
    shift.capacity = 50
    shift.max_group_size = 6
    shift.leap_time = 30
    shift.threshold = 70
    shift.start = 18 * 60 * 60
    shift.end = 21 * 60 * 60
    shift.days = [1, 2, 3, 4, 5]
    shift.comment = translate('shift-comment1')
    settings.shifts.add(shift)
    settings.put()
    return settings


@returns(FlowMemberResultCallbackResultTO)
@arguments(service_user=users.User, message_flow_run_id=unicode, member=unicode,
           steps=[object_factory('step_type', FLOW_STEP_MAPPING)], end_id=unicode, end_message_flow_id=unicode,
           parent_message_key=unicode, tag=unicode, result_key=unicode, flush_id=unicode, flush_message_flow_id=unicode,
           service_identity=unicode, user_details=[UserDetailsTO])
def reservation_part1(service_user, message_flow_run_id, member, steps, end_id, end_message_flow_id, parent_message_key,
                   tag, result_key, flush_id, flush_message_flow_id, service_identity, user_details):
    from solutions.common.bizz.messaging import POKE_TAG_RESERVE_PART2
    date = _get_value(steps[0], u'message_date')
    people = int(_get_value(steps[1], u'message_people'))
    data = {'date': date, 'people': people}

    real_result = FlowMemberResultCallbackResultTO()
    status = availability_and_shift(service_user, service_identity, user_details, date, people)[0]
    if status == STATUS_AVAILABLE:
        real_result.type = u'flow'
        result = FlowCallbackResultTypeTO()
        result.tag = POKE_TAG_RESERVE_PART2 + json.dumps(data)
        result.flow = get_restaurant_profile(service_user).reserve_flow_part2
        result.force_language = None
    else:
        real_result.type = u'message'
        result = _fail_message(service_user, service_identity, user_details, status, date)
    real_result.value = result
    return real_result


@returns(FlowMemberResultCallbackResultTO)
@arguments(service_user=users.User, message_flow_run_id=unicode, member=unicode,
           steps=[object_factory('step_type', FLOW_STEP_MAPPING)], end_id=unicode, end_message_flow_id=unicode,
           parent_message_key=unicode, tag=unicode, result_key=unicode, flush_id=unicode, flush_message_flow_id=unicode,
           service_identity=unicode, user_details=[UserDetailsTO])
def reservation_part2(service_user, message_flow_run_id, member, steps, end_id, end_message_flow_id, parent_message_key,
                   tag, result_key, flush_id, flush_message_flow_id, service_identity, user_details):
    from solutions.common.bizz.messaging import POKE_TAG_RESERVE_PART2, MESSAGE_TAG_RESERVE_SUCCESS
    name = _get_value(steps[0], u'message_name')
    phone = _get_value(steps[1], u'message_phone')
    comment = _get_value(steps[2], u'message_comments')

    data = json.loads(tag[len(POKE_TAG_RESERVE_PART2):])
    date = data['date']
    people = data['people']

    real_result = FlowMemberResultCallbackResultTO()
    status = reserve_table(service_user, service_identity, user_details, date, people, name, phone, comment)
    if status == STATUS_AVAILABLE:
        real_result.type = u'message'
        result = MessageCallbackResultTypeTO()
        result.message = _translate_service_user(service_user, u'table-reserved')
        result.tag = MESSAGE_TAG_RESERVE_SUCCESS
        result.answers = []
        result.branding = get_solution_main_branding(service_user).branding_key
        result.flags = Message.FLAG_ALLOW_DISMISS | Message.FLAG_AUTO_LOCK
        result.alert_flags = 0
        result.dismiss_button_ui_flags = 0
        result.attachments = []
        result.step_id = u'message_table_is_reserved'  # for flow_stats
    else:
        real_result.type = u'message'
        result = _fail_message(service_user, service_identity, user_details, status)
    real_result.value = result
    return real_result

@returns(PokeCallbackResultTO)
@arguments(service_user=users.User, email=unicode, tag=unicode, result_key=unicode, context=unicode,
           service_identity=unicode, user_details=[UserDetailsTO])
def my_reservations_poke(service_user, email, tag, result_key, context, service_identity, user_details):
    result = PokeCallbackResultTO()
    result.type = u'message'
    result.value = _create_reservations_overview_message(service_user, service_identity, user_details)
    return result

@returns(MessageAcknowledgedCallbackResultTO)
@arguments(service_user=users.User, status=int, answer_id=unicode, received_timestamp=int, member=unicode,
           message_key=unicode, tag=unicode, acked_timestamp=int, parent_message_key=unicode, result_key=unicode,
           service_identity=unicode, user_details=[UserDetailsTO])
def my_reservations_overview_updated(service_user, status, answer_id, received_timestamp, member, message_key, tag,
                                     acked_timestamp, parent_message_key, result_key, service_identity, user_details):
    if not answer_id:
        return None  # status is STATUS_RECEIVED or user dismissed

    result = MessageAcknowledgedCallbackResultTO()
    result.type = u'message'
    result.value = _create_reservation_details_message(answer_id, user_details)
    return result

@returns(MessageAcknowledgedCallbackResultTO)
@arguments(service_user=users.User, status=int, answer_id=unicode, received_timestamp=int, member=unicode,
           message_key=unicode, tag=unicode, acked_timestamp=int, parent_message_key=unicode, result_key=unicode,
           service_identity=unicode, user_details=[UserDetailsTO])
def my_reservations_detail_updated(service_user, status, answer_id, received_timestamp, member, message_key, tag,
                                   acked_timestamp, parent_message_key, result_key, service_identity, user_details):
    if not answer_id:
        return None  # status is STATUS_RECEIVED or user dismissed

    from solutions.common.bizz.messaging import send_inbox_forwarders_message, MESSAGE_TAG_MY_RESERVATIONS_EDIT_PEOPLE, \
        MESSAGE_TAG_MY_RESERVATIONS_EDIT_COMMENT
    info = json.loads(answer_id)
    action = info.get('action')
    if action == 'cancel':
        cancel_reservation(service_user, info['reservation'])

        result = MessageAcknowledgedCallbackResultTO()
        result.type = u'message'
        result.value = MessageCallbackResultTypeTO()
        result.value.alert_flags = 0
        result.value.answers = []
        result.value.branding = get_solution_main_branding(service_user).branding_key
        result.value.dismiss_button_ui_flags = 0
        result.value.flags = Message.FLAG_ALLOW_DISMISS | Message.FLAG_AUTO_LOCK
        result.value.message = _translate_service_user(service_user, u'my-reservations-canceled')
        result.value.tag = None
        result.value.attachments = []
        result.value.step_id = u'message_reservation_canceled'

        reservation = db.get(info['reservation'])


        now_ = now()
        if reservation.solution_inbox_message_key:
            msg = _translate_service_user(service_user, 'if-update-reservation-cancel')
            message, _ = add_solution_inbox_message(service_user, reservation.solution_inbox_message_key, False, user_details, now_, msg)
        else:
            msg = _translate_service_user(service_user, 'update-reservation-cancel') % {
                'user_name': user_details[0].name,
                'user_email': user_details[0].email,
                'people': reservation.people,
                'weekday': _format_weekday_service_user(service_user, reservation.date),
                'date': _format_date_service_user(service_user, reservation.date),
                'time': _format_time_service_user(service_user, reservation.date)
            }
            message = create_solution_inbox_message(service_user, service_identity, SolutionInboxMessage.CATEGORY_RESTAURANT_RESERVATION, unicode(reservation.key()), False, user_details, now_, msg, True)
        sln_settings = get_solution_settings(service_user)
        sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, service_identity)
        send_message(service_user, u"solutions.common.messaging.update", service_identity=service_identity, message=serialize_complex_value(SolutionInboxMessageTO.fromModel(message, sln_settings, sln_i_settings, True), SolutionInboxMessageTO, False))

        app_user = user_details[0].toAppUser()
        send_inbox_forwarders_message(service_user, service_identity, app_user, msg, {
            'if_name': user_details[0].name,
            'if_email':user_details[0].email
        }, message_key=message.solution_inbox_message_key, reply_enabled=message.reply_enabled)

        return result

    elif action == 'edit-people':
        reservation = RestaurantReservation.get(info['reservation'])

        result = MessageAcknowledgedCallbackResultTO()
        result.type = u'form'
        result.value = FormCallbackResultTypeTO()
        result.value.alert_flags = 0
        result.value.branding = get_solution_main_branding(service_user).branding_key
        result.value.flags = Message.FLAG_ALLOW_DISMISS | Message.FLAG_AUTO_LOCK
        result.value.form = SingleSliderFormTO()
        result.value.form.negative_button = _translate_service_user(service_user, u'Cancel', SOLUTION_COMMON)
        result.value.form.negative_button_ui_flags = Message.UI_FLAG_EXPECT_NEXT_WAIT_5
        result.value.form.negative_confirmation = None
        result.value.form.positive_button = _translate_service_user(service_user, u'reservation-button-check-db')
        result.value.form.positive_button_ui_flags = Message.UI_FLAG_EXPECT_NEXT_WAIT_5
        result.value.form.positive_confirmation = None
        result.value.form.javascript_validation = None
        result.value.form.type = SingleSliderTO.TYPE
        result.value.form.widget = SingleSliderTO()
        result.value.form.widget.max = 20
        result.value.form.widget.min = 1
        result.value.form.widget.value = int(reservation.people)
        result.value.message = _translate_service_user(service_user, u'reservation-message-amount-people')
        result.value.tag = MESSAGE_TAG_MY_RESERVATIONS_EDIT_PEOPLE + json.dumps(dict(reservation=info['reservation'])).decode('utf8')
        result.value.attachments = []
        result.value.step_id = u'message_number_of_people'
        return result

    elif action == 'edit-comment':
        reservation = RestaurantReservation.get(info['reservation'])

        result = MessageAcknowledgedCallbackResultTO()
        result.type = u'form'
        result.value = FormCallbackResultTypeTO()
        result.value.alert_flags = 0
        result.value.branding = get_solution_main_branding(service_user).branding_key
        result.value.flags = Message.FLAG_ALLOW_DISMISS | Message.FLAG_AUTO_LOCK
        result.value.form = TextBlockFormTO()
        result.value.form.negative_button = _translate_service_user(service_user, u'Cancel', SOLUTION_COMMON)
        result.value.form.negative_button_ui_flags = Message.UI_FLAG_EXPECT_NEXT_WAIT_5
        result.value.form.negative_confirmation = None
        result.value.form.positive_button = _translate_service_user(service_user, u'Submit', SOLUTION_COMMON)
        result.value.form.positive_button_ui_flags = Message.UI_FLAG_EXPECT_NEXT_WAIT_5
        result.value.form.positive_confirmation = None
        result.value.form.javascript_validation = None
        result.value.form.type = TextBlockTO.TYPE
        result.value.form.widget = TextBlockTO()
        result.value.form.widget.max_chars = 500
        result.value.form.widget.place_holder = _translate_service_user(service_user, u'(optional)')
        result.value.form.widget.value = reservation.comment
        result.value.message = _translate_service_user(service_user, u'reservation-message-comments')
        result.value.tag = MESSAGE_TAG_MY_RESERVATIONS_EDIT_COMMENT + json.dumps(dict(reservation=info['reservation'])).decode('utf8')
        result.value.attachments = []
        result.value.step_id = u'message_edit_comment'
        return result

    else:
        logging.error("Unexpected answer_id: " % answer_id)
        return None


@returns(FormAcknowledgedCallbackResultTO)
@arguments(service_user=users.User, status=int, form_result=FormResult, answer_id=unicode, member=unicode,
           message_key=unicode, tag=unicode, received_timestamp=int, acked_timestamp=int, parent_message_key=unicode,
           result_key=unicode, service_identity=unicode, user_details=[UserDetailsTO])
def my_reservations_edit_comment_updated(service_user, status, form_result, answer_id, member, message_key, tag,
                                         received_timestamp, acked_timestamp, parent_message_key, result_key,
                                         service_identity, user_details):
    if answer_id != Form.POSITIVE:
        return None

    from solutions.common.bizz.messaging import MESSAGE_TAG_MY_RESERVATIONS_EDIT_COMMENT, send_inbox_forwarders_message
    info = json.loads(tag[len(MESSAGE_TAG_MY_RESERVATIONS_EDIT_COMMENT):])
    comment_new = form_result.result.value or ''
    status = edit_reservation(service_user, info['reservation'], comment=comment_new)

    result = FormAcknowledgedCallbackResultTO()
    result.type = u'message'
    if status == STATUS_AVAILABLE:
        result.value = _create_reservation_edited_message(service_user, user_details)

        reservation = db.get(info['reservation'])


        now_ = now()
        if reservation.solution_inbox_message_key:
            msg = _translate_service_user(service_user, 'if-update-reservation-comment') % {
                'comment': comment_new
            }
            message_parent, message = add_solution_inbox_message(service_user, reservation.solution_inbox_message_key, False, user_details, now_, msg)
        else:
            msg = _translate_service_user(service_user, 'update-reservation-comment') % {
                 'user_name': user_details[0].name,
                 'user_email': user_details[0].email,
                 'people': reservation.people,
                 'weekday': _format_weekday_service_user(service_user, reservation.date),
                 'date': _format_date_service_user(service_user, reservation.date),
                 'time': _format_time_service_user(service_user, reservation.date),
                 'comment': comment_new
            }
            message = create_solution_inbox_message(service_user, service_identity, SolutionInboxMessage.CATEGORY_RESTAURANT_RESERVATION, unicode(reservation.key()), False, user_details, now_, msg, True)
        sln_settings = get_solution_settings(service_user)
        sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, service_identity)
        send_message(service_user, u"solutions.common.messaging.update", service_identity=service_identity, message=serialize_complex_value(SolutionInboxMessageTO.fromModel(message_parent if message_parent else message, sln_settings, sln_i_settings, True), SolutionInboxMessageTO, False))

        app_user = user_details[0].toAppUser()
        send_inbox_forwarders_message(service_user, service_identity, app_user, msg, {
            'if_name': user_details[0].name,
            'if_email':user_details[0].email
        }, message_key=message_parent.solution_inbox_message_key if message_parent else message.solution_inbox_message_key, \
           reply_enabled=message_parent.reply_enabled if message_parent else message.reply_enabled)
    else:
        result.value = _fail_message(service_user, service_identity, user_details, status)
    return result


@returns(FormAcknowledgedCallbackResultTO)
@arguments(service_user=users.User, status=int, form_result=FormResult, answer_id=unicode, member=unicode,
           message_key=unicode, tag=unicode, received_timestamp=int, acked_timestamp=int, parent_message_key=unicode,
           result_key=unicode, service_identity=unicode, user_details=[UserDetailsTO])
def my_reservations_edit_people_updated(service_user, status, form_result, answer_id, member, message_key, tag,
                                         received_timestamp, acked_timestamp, parent_message_key, result_key,
                                         service_identity, user_details):
    if answer_id != Form.POSITIVE:
        return None

    from solutions.common.bizz.messaging import MESSAGE_TAG_MY_RESERVATIONS_EDIT_PEOPLE, send_inbox_forwarders_message
    info = json.loads(tag[len(MESSAGE_TAG_MY_RESERVATIONS_EDIT_PEOPLE):])
    reservation = db.get(info['reservation'])
    people_old = reservation.people
    people_new = int(form_result.result.value)

    status = edit_reservation(service_user, info['reservation'], people=people_new)

    result = FormAcknowledgedCallbackResultTO()
    result.type = u'message'
    if status == STATUS_AVAILABLE:
        result.value = _create_reservation_edited_message(service_user, user_details)

        msg = _translate_service_user(service_user, 'if-update-reservation-people') % {
            'people_old': people_old,
            'people_new': people_new,
        }

        now_ = now()
        if reservation.solution_inbox_message_key:
            message, _ = add_solution_inbox_message(service_user, reservation.solution_inbox_message_key, False, user_details, now_, msg)
        else:
            msg = _translate_service_user(service_user, 'update-reservation-people') % {
                'user_name': user_details[0].name,
                'user_email': user_details[0].email,
                'people_old': people_old,
                'people_new': people_new,
                'weekday': _format_weekday_service_user(service_user, reservation.date),
                'date': _format_date_service_user(service_user, reservation.date),
                'time': _format_time_service_user(service_user, reservation.date)
             }
            message = create_solution_inbox_message(service_user, service_identity, SolutionInboxMessage.CATEGORY_RESTAURANT_RESERVATION, unicode(reservation.key()), False, user_details, now_, msg, True)
        sln_settings = get_solution_settings(service_user)
        sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, service_identity)
        send_message(service_user, u"solutions.common.messaging.update", service_identity=service_identity, message=serialize_complex_value(SolutionInboxMessageTO.fromModel(message, sln_settings, sln_i_settings, True), SolutionInboxMessageTO, False))

        app_user = user_details[0].toAppUser()
        send_inbox_forwarders_message(service_user, service_identity, app_user, msg, {
            'if_name': user_details[0].name,
            'if_email':user_details[0].email,
        }, message_key=message.solution_inbox_message_key, reply_enabled=message.reply_enabled)
    else:
        result.value = _fail_message(service_user, service_identity, user_details, status)
    return result


@returns(MessageCallbackResultTypeTO)
@arguments(service_user=users.User, service_identity=unicode, user_details=[UserDetailsTO])
def _create_reservations_overview_message(service_user, service_identity, user_details):
    from solutions.common.bizz.messaging import MESSAGE_TAG_MY_RESERVATIONS_OVERVIEW
    reservations = get_planned_reservations_by_user(service_user,
                                                    service_identity,
                                                    user_details[0].toAppUser(),
                                                    datetime.now())

    def convert_reservation_to_button(reservation):
        btn = AnswerTO()
        btn.action = None
        btn.caption = _format_date_service_user(service_user, reservation.date)
        btn.id = unicode(reservation.key())
        btn.type = u'button'
        btn.ui_flags = Message.UI_FLAG_EXPECT_NEXT_WAIT_5
        return btn

    answers = map(convert_reservation_to_button, reservations)
    if answers:
        msg = _translate_service_user(service_user, u'my-reservations-select-reservation')
    else:
        msg = _translate_service_user(service_user, u'my-reservations-no-reservations')

    result = MessageCallbackResultTypeTO()
    result.alert_flags = 0
    result.answers = answers
    result.branding = get_solution_main_branding(service_user).branding_key
    result.dismiss_button_ui_flags = 0
    result.flags = Message.FLAG_ALLOW_DISMISS | Message.FLAG_AUTO_LOCK
    result.message = msg
    result.tag = MESSAGE_TAG_MY_RESERVATIONS_OVERVIEW
    result.attachments = []
    result.step_id = u'message_reservation_overview'
    return result

@returns(MessageCallbackResultTypeTO)
@arguments(reservation_key=unicode, user_details=[UserDetailsTO])
def _create_reservation_details_message(reservation_key, user_details):
    from solutions.common.bizz.messaging import MESSAGE_TAG_MY_RESERVATIONS_DETAIL
    reservation = RestaurantReservation.get(reservation_key)
    service_user = get_service_user_from_service_identity_user(reservation.service_identity_user)
    date = _format_date_service_user(service_user, reservation.date)
    time_ = _format_time_service_user(service_user, reservation.date)
    reservation_details = {'arrival_date' : date,
                           'arrival_time' : time_,
                           'comment' : reservation.comment or '-',
                           'number' : reservation.people,
                           'date_reservation_done' : _format_date_service_user(service_user, reservation.creation_date),
                           'arrival_date_time' : '%s %s' % (date, time_)
                           }

    btn_people = AnswerTO()
    btn_people.action = None
    btn_people.caption = _translate_service_user(service_user, u'my-reservations-btn-edit-people')
    btn_people.id = json.dumps(dict(reservation=reservation_key, action='edit-people')).decode('utf8')
    btn_people.type = u"button"
    btn_people.ui_flags = Message.UI_FLAG_EXPECT_NEXT_WAIT_5

    btn_comment = AnswerTO()
    btn_comment.action = None
    btn_comment.caption = _translate_service_user(service_user, u'my-reservations-btn-edit-comment')
    btn_comment.id = json.dumps(dict(reservation=reservation_key, action='edit-comment')).decode('utf8')
    btn_comment.type = u"button"
    btn_comment.ui_flags = Message.UI_FLAG_EXPECT_NEXT_WAIT_5

    btn_cancel = AnswerTO()
    btn_cancel.action = "confirm://" + (_translate_service_user(service_user, u'my-reservations-btn-cancel-confirm') % reservation_details)
    btn_cancel.caption = _translate_service_user(service_user, u'my-reservations-btn-cancel')
    btn_cancel.id = json.dumps(dict(reservation=reservation_key, action='cancel')).decode('utf8')
    btn_cancel.type = u"button"
    btn_cancel.ui_flags = Message.UI_FLAG_EXPECT_NEXT_WAIT_5

    result = MessageCallbackResultTypeTO()
    result.alert_flags = 0
    result.answers = [btn_people, btn_comment, btn_cancel]
    reservation_service_user = get_service_user_from_service_identity_user(reservation.service_identity_user)
    result.branding = get_solution_main_branding(reservation_service_user).branding_key
    result.dismiss_button_ui_flags = 0
    result.flags = Message.FLAG_ALLOW_DISMISS | Message.FLAG_AUTO_LOCK
    result.message = _translate_service_user(service_user, u'my-reservations-detail') % reservation_details
    result.tag = MESSAGE_TAG_MY_RESERVATIONS_DETAIL
    result.attachments = []
    result.step_id = u'message_reservation_detail'
    return result

@returns(MessageCallbackResultTypeTO)
@arguments(service_user=users.User, user_details=[UserDetailsTO])
def _create_reservation_edited_message(service_user, user_details):
    from solutions.common.bizz.messaging import MESSAGE_TAG_MY_RESERVATIONS_DETAIL
    result = MessageCallbackResultTypeTO()
    result.alert_flags = 0
    result.answers = []
    result.branding = get_solution_main_branding(service_user).branding_key
    result.dismiss_button_ui_flags = 0
    result.flags = Message.FLAG_ALLOW_DISMISS | Message.FLAG_AUTO_LOCK
    result.message = _translate_service_user(service_user, u'my-reservations-edited')
    result.tag = MESSAGE_TAG_MY_RESERVATIONS_DETAIL
    result.attachments = []
    result.step_id = u'message_reservation_edited'
    return result

@returns(MessageCallbackResultTypeTO)
@arguments(service_user=users.User, service_identity=unicode, user_details=[UserDetailsTO], status=unicode, date=(int, long))
def _fail_message(service_user, service_identity, user_details, status, date=0):
    from solutions.common.bizz.messaging import MESSAGE_TAG_RESERVE_FAIL
    result = MessageCallbackResultTypeTO()
    result.tag = MESSAGE_TAG_RESERVE_FAIL
    if status == STATUS_IN_HOLIDAY:
        if is_default_service_identity(service_identity):
            sln_i_settings = get_solution_settings(service_user)
        else:
            sln_i_settings = get_solution_identity_settings(service_user, service_identity)
        result.message = sln_i_settings.holiday_out_of_office_message
        result.answers = []
        result.step_id = u'message_in_holiday'  # for flow_stats
    else:
        result.message = _translate_service_user(service_user, status)
        if status in (STATUS_NO_TABLES, STATUS_SHORT_NOTICE, STATUS_TOO_MANY_PEOPLE):
            call = AnswerTO()
            call.id = u'call'
            call.type = u'button'
            call.caption = _translate_service_user(service_user, u'call-restaurant-btn')
            call.action = u'tel://%s' % system.get_identity(service_identity).phone_number
            call.ui_flags = 0
            result.answers = [call]
            result.step_id = u'message_%s' % status  # for flow_stats
        elif status == STATUS_KITCHEN_CLOSED and date:
            date = datetime.utcfromtimestamp(date)
            shifts = _get_shifts_on_date(service_user, service_identity, date)
            extra_line = _translate_service_user(service_user, u'kitchen-closed-extra-line') % { 'week_day': _format_weekday_service_user(service_user, date)}
            for shift in shifts:
                start_hour = shift.start / 3600
                start_minutes = (shift.start % 3600) / 60
                end_hour = shift.end / 3600
                end_minutes = (shift.end % 3600) / 60
                extra_line += "\n %s:%02d ==> %s:%02d" % (start_hour, start_minutes, end_hour, end_minutes)
            result.message = result.message % {'reservation_time': " (%s:%02d)" % (date.hour, date.minute)}
            result.message = "\n%s\n\n%s" % (result.message, extra_line)
            result.answers = []
            result.step_id = u'message_kitchen_closed'  # for flow_stats
        else:
            result.message = result.message % {'reservation_time': ''}
            result.answers = []
            result.step_id = u'message_reservation_not_possible'  # for flow_stats
    result.branding = get_solution_main_branding(service_user).branding_key
    result.flags = Message.FLAG_ALLOW_DISMISS | Message.FLAG_AUTO_LOCK
    result.alert_flags = 0
    result.dismiss_button_ui_flags = 0
    result.attachments = []
    return result

@returns(datetime)
@arguments(service_user=users.User)
def now_in_resto_timezone(service_user):
    sln_settings = get_solution_settings(service_user)
    timezone = pytz.timezone(sln_settings.timezone)
    now_in_resto_timezone = datetime.now(timezone)
    return datetime(now_in_resto_timezone.year, now_in_resto_timezone.month, now_in_resto_timezone.day,
                                     now_in_resto_timezone.hour, now_in_resto_timezone.minute)


@returns(tuple)
@arguments(service_user=users.User, service_identity=unicode, user_details=[UserDetailsTO], epoch=long, people=int, force=bool, total_people=int)
def availability_and_shift(service_user, service_identity, user_details, epoch, people, force=False, total_people=0):
    """Returns a pair, consisting of:
    (a) status code
    (c) The corresponding shift (datetime) if there is a table available"""

    logging.info('Checking date %d for %d people' % (epoch, people))

    if is_in_holiday(service_user, service_identity, epoch):
        return (STATUS_IN_HOLIDAY, None)

    now_ = now_in_resto_timezone(service_user)
    date = datetime.utcfromtimestamp(epoch)

    logging.info("now in restaurant:" + str(now_))
    logging.info("reservation date:" + str(date))

    if date <= now_:
        return (STATUS_PAST_RESERVATION, None)

    shift = _get_matching_shift(service_user, service_identity, epoch)
    if shift is None:
        shifts_on_reservation_day = _get_shifts_on_date(service_user, service_identity, date)
        if not shifts_on_reservation_day:
            return (STATUS_RESTAURANT_CLOSED , None)
        else:
            return (STATUS_KITCHEN_CLOSED, None)

    shift_start_time = time(shift.start / 3600, shift.start / 60 % 60)
    shift_start = datetime.combine(date.date(), shift_start_time)
    if shift.leap_time >= 0:
        leap_time = timedelta(minutes=shift.leap_time)
        if (now_.date() == date.date() and now_ >= shift_start - leap_time) and not force:
            return (STATUS_SHORT_NOTICE, None)

    if total_people:
        if total_people > shift.max_group_size and not force:
            return (STATUS_TOO_MANY_PEOPLE, None)
    else:
        if people > shift.max_group_size and not force:
            return (STATUS_TOO_MANY_PEOPLE, None)

    already_reserved = 0
    for reservation in get_restaurant_reservation(service_user, service_identity, shift_start):
        if is_flag_set(RestaurantReservation.STATUS_CANCELED, reservation.status) or is_flag_set(RestaurantReservation.STATUS_DELETED, reservation.status):
            continue
        already_reserved += reservation.people
    if already_reserved >= shift.capacity * shift.threshold / 100 and not force:
        return (STATUS_NO_TABLES, None)

    return (STATUS_AVAILABLE, shift_start)


@returns(unicode)
@arguments(service_user=users.User, service_identity=unicode, user_details=[UserDetailsTO], date=long,
           people=int, name=unicode, phone=unicode, comment=unicode, force=bool)
def reserve_table(service_user, service_identity, user_details, date, people, name, phone, comment, force=False):
    from solutions.common.bizz.messaging import send_inbox_forwarders_message
    # TODO: race conditions?
    status, shift_start = availability_and_shift(service_user, service_identity, user_details, date, people, force)
    if status != STATUS_AVAILABLE:
        return status

    logging.info('Reserving table on %d for %d people on name %s with comment "%s"'
                 % (date, people, name, comment))
    date = datetime.utcfromtimestamp(date)
    rogerthat_user = user_details[0].toAppUser() if user_details else None

    if user_details:
        msg = _translate_service_user(service_user, 'if-reservation-received') % {
                'reservation_weekday': _format_weekday_service_user(service_user, date),
                'reservation_date': _format_date_service_user(service_user, date),
                'reservation_time': _format_time_service_user(service_user, date),
                'reservation_count': people,
                'reservation_phone': phone,
                'reservation_remarks': comment
                }
    else:
        msg = None

    service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
    def trans():
        reservation = RestaurantReservation(service_user=service_identity_user,
                                            user=rogerthat_user, name=name or "John Doe", phone=phone, date=date,
                                            people=people, comment=comment, shift_start=shift_start,
                                            creation_date=datetime.now())
        if user_details:
            now_ = now()
            message = create_solution_inbox_message(service_user, service_identity, SolutionInboxMessage.CATEGORY_RESTAURANT_RESERVATION, None, False, user_details, now_, msg, True)
            reservation.solution_inbox_message_key = message.solution_inbox_message_key
            reservation.sender = SolutionUser.fromTO(user_details[0])
        else:
            message = None
        reservation.put()
        if message:
            message.category_key = unicode(reservation.key())
            message.put()
        return message
    xg_on = db.create_transaction_options(xg=True)
    message = db.run_in_transaction_options(xg_on, trans)

    if user_details:
        app_user = user_details[0].toAppUser()

        send_inbox_forwarders_message(service_user, service_identity, app_user, msg, {
                'if_name': user_details[0].name,
                'if_email':user_details[0].email,
            }, message_key=message.solution_inbox_message_key, reply_enabled=message.reply_enabled)


    start_time = TimestampTO.fromDatetime(shift_start)
    sm_data = []
    sm_data.append({u"type": u"solutions.restaurant.reservations.update",
                 u"shift": serialize_complex_value(start_time, TimestampTO, False)})

    if message:
        sln_settings = get_solution_settings(service_user)
        sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, service_identity)
        sm_data.append({u"type": u"solutions.common.messaging.update",
                     u"message": serialize_complex_value(SolutionInboxMessageTO.fromModel(message, sln_settings, sln_i_settings, True), SolutionInboxMessageTO, False)})

    send_message(service_user, sm_data, service_identity=service_identity)
    return STATUS_AVAILABLE

@returns(NoneType)
@arguments(service_user=users.User, service_identity=unicode, reservation_key=unicode, shift_name=unicode)
def move_reservation(service_user, service_identity, reservation_key, shift_name):
    settings = get_restaurant_settings(service_user, service_identity)
    bizz_check(shift_name in settings.shifts, "Cannot move reservation into unknown shift '%s'." % shift_name)
    def trans():
        reservation = db.get(reservation_key)
        bizz_check(reservation and isinstance(reservation, RestaurantReservation), "Reservation not found.")
        shift = settings.shifts[shift_name]
        bizz_check(reservation.date.isoweekday() in shift.days)
        shift_start = datetime(reservation.date.year, reservation.date.month, reservation.date.day, shift.start / 3600, shift.start % 3600 / 60)
        reservation.shift_start = shift_start
        reservation.status = unset_flag(RestaurantReservation.STATUS_SHIFT_REMOVED, reservation.status)
        reservation.put()
        return shift_start
    shift_start = db.run_in_transaction(trans)

    start_time = TimestampTO.fromDatetime(shift_start)

    send_message(service_user, u"solutions.restaurant.reservations.update",
                 service_identity=service_identity,
                 shift=serialize_complex_value(start_time, TimestampTO, False))


@returns(NoneType)
@arguments(service_user=users.User, reservation_key=(unicode, db.Key), notified=bool)
def cancel_reservation(service_user, reservation_key, notified=False):
    def trans():
        reservation = _cancel_reservation(service_user, reservation_key, notified)
        return reservation
    reservation = db.run_in_transaction(trans)

    start_time = TimestampTO.fromDatetime(reservation.shift_start)
    reservation_service_user = get_service_user_from_service_identity_user(reservation.service_identity_user)
    send_message(reservation_service_user, u"solutions.restaurant.reservations.update",
                 service_identity=reservation.service_identity,
                 shift=serialize_complex_value(start_time, TimestampTO, False))


@returns(NoneType)
@arguments(service_user=users.User, reservation_keys=[unicode])
def cancel_reservations(service_user, reservation_keys):

    def trans(reservation_key):
        reservation = _cancel_reservation(service_user, reservation_key, True)
        bizz_check(not reservation.user is None, "This is only for reservations made by the app.")
        deferred.defer(_send_cancellation_message, reservation_key, _transactional=True)

    for reservation_key in reservation_keys:
        db.run_in_transaction(trans, reservation_key)


def _send_cancellation_message(reservation_key):
    from solutions.common.bizz.messaging import send_inbox_forwarders_message

    try:
        reservation = RestaurantReservation.get(reservation_key)
        reservation_service_user = get_service_user_from_service_identity_user(reservation.service_identity_user)
        bizz_check(not reservation.user is None, "This is only for reservations made by the app.")
        message = _translate_service_user(reservation_service_user, u'cancellation-message')
        date = "%s %s" % (_format_date_service_user(reservation_service_user, reservation.date), _format_time_service_user(reservation_service_user, reservation.date))
        common_settings = get_solution_settings(reservation_service_user)
        resto = common_settings.name
        message = message % {'date': date, 'resto': resto}
        if reservation.solution_inbox_message_key:
            sln_settings = get_solution_settings(reservation_service_user)
            sim_parent, _ = add_solution_inbox_message(reservation_service_user, reservation.solution_inbox_message_key, True, None, now(), message, mark_as_unread=False, mark_as_read=True)
            send_inbox_forwarders_message(reservation_service_user, sim_parent.service_identity, None, message, {
                        'if_name': sim_parent.sender.name,
                        'if_email':sim_parent.sender.email
                    }, message_key=sim_parent.solution_inbox_message_key, reply_enabled=sim_parent.reply_enabled)

            sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, reservation.service_identity)
            send_message(reservation_service_user, "solutions.common.messaging.update",
                         service_identity=reservation.service_identity,
                         message=serialize_complex_value(SolutionInboxMessageTO.fromModel(sim_parent, sln_settings, sln_i_settings, True), SolutionInboxMessageTO, False))
        else:
            branding = get_solution_main_branding(reservation_service_user)
            users.set_user(reservation_service_user)
            try:
                messaging.send(parent_key=None,
                               parent_message_key=None,
                               message=message,
                               flags=1 | 64,
                               members=[reservation.user.email()],
                               branding=branding.branding_key,
                               tag=None,
                               service_identity=reservation.service_identity)
            finally:
                users.clear_user()
    except:
        logging.exception("Failed to send cancellation message.")

def _cancel_reservation(service_user, reservation_key, notified):
    reservation = RestaurantReservation.get(reservation_key)
    reservation_service_user = get_service_user_from_service_identity_user(reservation.service_identity_user)
    bizz_check(reservation_service_user == service_user, "Reservation not found.")
    reservation.status = set_flag(RestaurantReservation.STATUS_CANCELED, reservation.status)
    if notified:
        reservation.status = set_flag(RestaurantReservation.STATUS_NOTIFIED, reservation.status)
    reservation.status = unset_flag(RestaurantReservation.STATUS_SHIFT_REMOVED, reservation.status)
    reservation.put()
    return reservation


@returns(tuple)
@arguments(service_user=users.User, service_identity=unicode, now=datetime)
def get_shift_by_datetime(service_user, service_identity, now):
    seconds_from_midnight = now.hour * 3600 + now.minute * 60 + now.second
    weekday = now.isoweekday()
    shift = _get_matching_shift2(service_user, service_identity, seconds_from_midnight, weekday)
    if shift:
        return shift, datetime.combine(now.date(), time(shift.start / 3600, shift.start / 60 % 60))
    shifts = _get_sorted_shifts(service_user, service_identity)
    if shifts:
        # Try to find shift on the day in now
        for shift in ([x[1] for x in shifts if x[0] == weekday]):
            if shift.start > seconds_from_midnight:
                return shift, datetime.combine(now.date(), time(shift.start / 3600, shift.start / 60 % 60))
        # Get next shift after today
        days_added = 0
        while True:
            days_added += 1
            weekday = (weekday + 1) % 7
            for shift in ([x[1] for x in shifts if x[0] == weekday]):
                return shift, datetime.combine(timedelta(days=days_added) + now.date(), time(shift.start / 3600, shift.start / 60 % 60))
    return None, None


@returns(tuple)
@arguments(service_user=users.User, service_identity=unicode, current_shift=Shift, current_start_time=datetime)
def get_next_shift(service_user, service_identity, current_shift, current_start_time):
    current_day = current_start_time.isoweekday()
    shifts = _get_sorted_shifts(service_user, service_identity)
    shifts_length = len(shifts)
    for i in xrange(shifts_length):
        entry = shifts[i]
        if entry[1] == current_shift and current_day == entry[0]:
            next_index = (i + 1) % len(shifts)
            shift = shifts[next_index][1]
            day = shifts[next_index][0]
            days_added = (day - current_day) if day >= current_day else (day + 7 - current_day)
            return shift, datetime.combine(timedelta(days=days_added) + current_start_time.date(), time(shift.start / 3600, shift.start / 60 % 60))
    raise ValueError("Unknown shift")  # Actually cannot happen


@returns(RestaurantReservationStatisticsTO)
@arguments(service_user=users.User, service_identity=unicode, date=datetime)
def get_statistics(service_user, service_identity, date):
    # Get date without time portion
    today = datetime(date.year, date.month, date.day);
    tomorrow = today + timedelta(days=1)
    end_of_tomorrow = today + timedelta(days=2)
    date_until = today + timedelta(days=10)  # today, tomorrow, nextweek
    # Get shifts
    shifts = list()
    shift, start_time = get_shift_by_datetime(service_user, service_identity, date)
    if shift:
        shifts.append((shift, start_time))
        while shifts[-1][1] < date_until:
            shifts.append(get_next_shift(service_user, service_identity, *shifts[-1]))
        shifts.pop(-1)  # last shift is outside the boundaries

    # Get total capacities
    result = RestaurantReservationStatisticsTO()
    result.today = RestaurantReservationStatisticTO()
    result.tomorrow = RestaurantReservationStatisticTO()
    result.next_week = RestaurantReservationStatisticTO()
    result.start = TimestampTO.fromDatetime(today)
    result.end = TimestampTO.fromDatetime(date_until)
    for shift, start_time in shifts:
        if start_time < tomorrow:
            result.today.capacity += shift.capacity
            result.today.capacity_threshold += int((shift.capacity * shift.threshold) / 100)
        elif start_time < end_of_tomorrow:
            result.tomorrow.capacity += shift.capacity
            result.tomorrow.capacity_threshold += int((shift.capacity * shift.threshold) / 100)
        else:
            result.next_week.capacity += shift.capacity
            result.next_week.capacity_threshold += int((shift.capacity * shift.threshold) / 100)
    # Get reservations
    for reservation in get_reservations(service_user, service_identity, today, date_until):
        if is_flag_set(RestaurantReservation.STATUS_CANCELED, reservation.status):
            continue
        if reservation.shift_start < tomorrow:
            result.today.reservations += reservation.people
        elif reservation.shift_start < end_of_tomorrow:
            result.tomorrow.reservations += reservation.people
        else:
            result.next_week.reservations += reservation.people
    return result


@returns(RestaurantReservation)
@arguments(service_user=users.User, reservation_key=unicode)
def toggle_reservation_arrived(service_user, reservation_key):
    def trans():
        reservation = db.get(reservation_key)
        reservation_service_user = get_service_user_from_service_identity_user(reservation.service_identity_user)
        azzert(service_user == reservation_service_user)

        if reservation.status & RestaurantReservation.STATUS_ARRIVED == RestaurantReservation.STATUS_ARRIVED:
            reservation.status = reservation.status & ~RestaurantReservation.STATUS_ARRIVED
        else:
            reservation.status = reservation.status | RestaurantReservation.STATUS_ARRIVED

        reservation.put();
        return reservation
    return db.run_in_transaction(trans)


@returns(RestaurantReservation)
@arguments(service_user=users.User, reservation_key=unicode)
def toggle_reservation_cancelled(service_user, reservation_key):
    def trans():
        reservation = db.get(reservation_key)
        reservation_service_user = get_service_user_from_service_identity_user(reservation.service_identity_user)
        azzert(service_user == reservation_service_user)

        if reservation.status & RestaurantReservation.STATUS_CANCELED == RestaurantReservation.STATUS_CANCELED:
            reservation.status = reservation.status & ~RestaurantReservation.STATUS_CANCELED
        else:
            reservation.status = reservation.status | RestaurantReservation.STATUS_CANCELED

        reservation.put();
        return reservation
    reservation = db.run_in_transaction(trans)
    start_time = TimestampTO.fromDatetime(reservation.shift_start)
    send_message(service_user, u"solutions.restaurant.reservations.update",
                 service_identity=reservation.service_identity,
                 shift=serialize_complex_value(start_time, TimestampTO, False))
    return reservation


@returns(unicode)
@arguments(service_user=users.User, reservation_key=unicode, people=(NoneType, int), comment=unicode, force=bool, new_date=bool, new_epoch=long)
def edit_reservation(service_user, reservation_key, people=None, comment=None, force=False, new_date=False, new_epoch=0):
    azzert(people is not None or comment is not None)

    def trans():
        check = True
        date_updated = False
        reservation = db.get(reservation_key)
        if force:
            check = False
        elif people is None or people <= reservation.people:
            check = False

        date = get_epoch_from_datetime(reservation.date)

        if new_date and new_epoch != date:
            check = True
            date_updated = True
            date = new_epoch

        if check:
            @db.non_transactional()
            def get_status_and_shift_start():
                status, shift_start = availability_and_shift(service_user, reservation.service_identity, None, date, people - reservation.people, force, people)
                return status, shift_start

            status, shift_start = get_status_and_shift_start()
            if status != STATUS_AVAILABLE:
                return status, None, reservation.service_identity

        if people is not None:
            reservation.people = people
        if comment is not None:
            reservation.comment = comment
        if date_updated:
            reservation.date = datetime.utcfromtimestamp(date)
            reservation.shift_start = shift_start

        reservation.put()
        return STATUS_AVAILABLE, reservation.shift_start, reservation.service_identity

    xg_on = db.create_transaction_options(xg=True)
    status, shift_start, service_identity = db.run_in_transaction_options(xg_on, trans)
    if status == STATUS_AVAILABLE:
        start_time = TimestampTO.fromDatetime(shift_start)
        send_message(service_user, u"solutions.restaurant.reservations.update",
                     service_identity=service_identity,
                     shift=serialize_complex_value(start_time, TimestampTO, False))

    return status


@returns(NoneType)
@arguments(service_user=users.User, reservation_key=unicode, tables=[(int, long)])
def edit_reservation_tables(service_user, reservation_key, tables):
    def trans():
        reservation = db.get(reservation_key)
        reservation.tables = tables
        reservation.put()
        return reservation.shift_start, reservation.service_identity

    shift_start, service_identity = db.run_in_transaction(trans)
    start_time = TimestampTO.fromDatetime(shift_start)
    send_message(service_user, u"solutions.restaurant.reservations.update",
                 service_identity=service_identity,
                 shift=serialize_complex_value(start_time, TimestampTO, False))


@returns(NoneType)
@arguments(service_user=users.User, email=unicode, app_id=unicode, message=unicode, reservation_key=unicode)
def reply_reservation(service_user, email, app_id, message, reservation_key=None):
    from solutions.common.bizz.messaging import send_inbox_forwarders_message

    reservation = db.run_in_transaction(db.get, reservation_key) if reservation_key else None
    if reservation and reservation.solution_inbox_message_key:
            sln_settings = get_solution_settings(service_user)
            sim_parent, _ = add_solution_inbox_message(service_user, reservation.solution_inbox_message_key, True, None, now(), message, mark_as_unread=False, mark_as_read=True)
            send_inbox_forwarders_message(service_user, sim_parent.service_identity, None, message, {
                        'if_name': sim_parent.sender.name,
                        'if_email':sim_parent.sender.email
                    }, message_key=sim_parent.solution_inbox_message_key, reply_enabled=sim_parent.reply_enabled)
            sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, reservation.service_identity)
            send_message(service_user, u"solutions.common.messaging.update",
                         service_identity=reservation.service_identity,
                         message=serialize_complex_value(SolutionInboxMessageTO.fromModel(sim_parent, sln_settings, sln_i_settings, True), SolutionInboxMessageTO, False))
    else:
        m = MemberTO()
        m.member = email
        m.app_id = app_id
        m.alert_flags = Message.ALERT_FLAG_VIBRATE
        if reservation:
            service_identity = reservation.service_identity
        else:
            logging.error("reply_reservation but reservation key was None")
            service_identity = None

        messaging.send(parent_key=None,
                       parent_message_key=None,
                       message=message,
                       answers=[],
                       flags=Message.FLAG_ALLOW_DISMISS,
                       members=[m],
                       branding=get_solution_main_branding(service_user).branding_key,
                       tag=None,
                       service_identity=service_identity)

@returns([Shift])
@arguments(service_user=users.User, service_identity=unicode, date=datetime)
def _get_shifts_on_date(service_user, service_identity, date):
    date_day = date.isoweekday()
    return [shift for day, shift in _get_sorted_shifts(service_user, service_identity) if day == date_day]


@returns(list)
@arguments(service_user=users.User, service_identity=unicode)
def _get_sorted_shifts(service_user, service_identity):
    settings = get_restaurant_settings(service_user, service_identity)
    shifts = list()
    for shift in settings.shifts:
        for day in shift.days:
            shifts.append((day, shift))
    def shift_cmp(left, right):
        if left[0] < right[0]:
            return -1
        elif left[0] > right[0]:
            return 1
        else:
            return cmp(left[1].start, right[1].start)
    return sorted(shifts, cmp=shift_cmp)


@returns(Shift)
@arguments(service_user=users.User, service_identity=unicode, date=long)
def _get_matching_shift(service_user, service_identity, date):
    seconds_from_midnight = date % 86400
    weekday = datetime.utcfromtimestamp(date).isoweekday()
    return _get_matching_shift2(service_user, service_identity, seconds_from_midnight, weekday)


@returns(Shift)
@arguments(service_user=users.User, service_identity=unicode, seconds_from_midnight=(int, long), weekday=int)
def _get_matching_shift2(service_user, service_identity, seconds_from_midnight, weekday):
    settings = get_restaurant_settings(service_user, service_identity)
    for shift in settings.shifts:
        if weekday in shift.days and shift.start <= seconds_from_midnight < shift.end:
            return shift
    return None


@returns(unicode)
@arguments(service_user=users.User, key=unicode, solution=unicode)
def _translate_service_user(service_user, key, solution=SOLUTION_COMMON):
    settings = get_solution_settings(service_user)  # TODO: make cached
    return common_translate(settings.main_language, solution, key)


@returns(unicode)
@arguments(service_user=users.User, dt=datetime)
def _format_date_service_user(service_user, dt):
    sln_settings = get_solution_settings(service_user)
    return format_date(dt, format='long', locale=sln_settings.main_language or DEFAULT_LANGUAGE)


@returns(unicode)
@arguments(service_user=users.User, dt=datetime)
def _format_weekday_service_user(service_user, dt):
    sln_settings = get_solution_settings(service_user)
    return format_date(dt, format='EEEE', locale=sln_settings.main_language or DEFAULT_LANGUAGE)


@returns(unicode)
@arguments(service_user=users.User, dt=datetime)
def _format_time_service_user(service_user, dt):
    sln_settings = get_solution_settings(service_user)
    return format_time(dt, format='short', locale=sln_settings.main_language or DEFAULT_LANGUAGE)


@returns(NoneType)
@arguments(service_user=users.User, service_identity=unicode, shifts=[RestaurantShiftTO])
def save_shifts(service_user, service_identity, shifts):
    # Some checks
    for s in shifts:
        if s.start >= s.end:
            raise ShiftConfigurationException("Shift %s has an invalid end time" % s.name)
        if s.max_group_size > s.capacity:
            raise ShiftConfigurationException("Shift %s has an invalid maximum group size. It is bigger than the capacity." % s.name)
        for ss in shifts:
            if s == ss:
                continue
            if (s.start < ss.start < s.end or s.start < ss.end < s.end) and set(s.days).intersection(ss.days):
                raise ShiftOverlapException("Shift %s and %s overlap!" % (s.name, ss.name))

    now_ = now_in_resto_timezone(service_user)
    today = datetime(now_.year, now_.month, now_.day)

    def trans():
        # Save settings
        settings = get_restaurant_settings(service_user, service_identity)
        azzert(settings)
        settings.shifts = Shifts()
        for shift in shifts:
            settings.shifts.add(shift)
        put_and_invalidate_cache(settings)
        handle_shift_updates(service_user, service_identity, today, shifts)

    xg_on = db.create_transaction_options(xg=True)
    db.run_in_transaction_options(xg_on, trans)
    send_message(service_user, u"solutions.restaurant.reservations.update", service_identity=service_identity)


@returns(NoneType)
@arguments(service_user=users.User, service_identity=unicode, table=TableTO)
def add_table(service_user, service_identity, table):
    if not table.capacity > 0:
        raise InvalidTableException('The specified table must fit at least 1 person.')

    service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
    def trans():
        rt = RestaurantTable(parent=parent_key_unsafe(service_identity_user, SOLUTION_COMMON))
        rt.name = table.name
        rt.capacity = table.capacity
        rt.deleted = False
        rt.put()

    db.run_in_transaction(trans)
    send_message(service_user, u"solutions.restaurant.tables.update", service_identity=service_identity)


@returns(NoneType)
@arguments(service_user=users.User, service_identity=unicode, table=TableTO)
def update_table(service_user, service_identity, table):
    if not table.capacity > 0:
        raise InvalidTableException('The specified table must fit at least 1 person.')

    service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
    def trans():
        rt = RestaurantTable.get_by_id(table.key, parent_key_unsafe(service_identity_user, SOLUTION_COMMON))
        rt.name = table.name
        rt.capacity = table.capacity
        rt.put()

    db.run_in_transaction(trans)
    send_message(service_user, u"solutions.restaurant.tables.update", service_identity=service_identity)

@returns(tuple)
@arguments(service_user=users.User, service_identity=unicode, table_id=(int, long), force=bool)
def delete_table(service_user, service_identity, table_id, force):

    if not force:
        upcoming_planned_reservation = list(get_upcoming_planned_reservations_by_table(service_user, service_identity, table_id, datetime.now()))

        if upcoming_planned_reservation:
            return False, upcoming_planned_reservation

    clear_table_id_in_reservations(service_user, service_identity, table_id)

    service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
    def trans():
        rt = RestaurantTable.get_by_id(table_id, parent_key_unsafe(service_identity_user, SOLUTION_COMMON))
        rt.deleted = True
        rt.put()

    db.run_in_transaction(trans)
    send_message(service_user, u"solutions.restaurant.tables.update", service_identity=service_identity)
    return True, None
