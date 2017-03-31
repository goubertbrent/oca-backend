# -*- coding: utf-8 -*-
# Copyright 2017 GIG Technology NV
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
# @@license_version:1.2@@

import logging
from types import NoneType

from rogerthat.dal import parent_key, put_and_invalidate_cache
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from rogerthat.to.messaging.flow import FLOW_STEP_MAPPING
from rogerthat.to.messaging.service_callback_results import FlowMemberResultCallbackResultTO
from rogerthat.to.service import UserDetailsTO
from rogerthat.translations import DEFAULT_LANGUAGE
from rogerthat.utils.app import create_app_user_by_email
from rogerthat.utils.channel import send_message
from mcfw.properties import object_factory
from mcfw.rpc import returns, arguments, serialize_complex_value
from solutions import translate as common_translate
from solutions.common import SOLUTION_COMMON
from solutions.common.bizz import broadcast_updates_pending
from solutions.common.bizz.inbox import create_solution_inbox_message
from solutions.common.dal import get_solution_settings, get_solution_settings_or_identity_settings
from solutions.common.models import SolutionInboxMessage
from solutions.common.models.appointment import SolutionAppointmentWeekdayTimeframe
from solutions.common.to import SolutionInboxMessageTO

@returns(FlowMemberResultCallbackResultTO)
@arguments(service_user=users.User, message_flow_run_id=unicode, member=unicode,
           steps=[object_factory("step_type", FLOW_STEP_MAPPING)], end_id=unicode, end_message_flow_id=unicode,
           parent_message_key=unicode, tag=unicode, result_key=unicode, flush_id=unicode, flush_message_flow_id=unicode,
           service_identity=unicode, user_details=[UserDetailsTO])
def appointment_asked(service_user, message_flow_run_id, member, steps, end_id, end_message_flow_id, parent_message_key,
                   tag, result_key, flush_id, flush_message_flow_id, service_identity, user_details):
    from solutions.common.bizz.messaging import _get_step_with_id, send_inbox_forwarders_message

    logging.info("_flow_member_result_appointment: \n %s" % steps)


    day = _get_step_with_id(steps, 'message_day')
    if not day:
        logging.error("Did not find step with id 'day'. Can not process message_flow_member_result with tag %s" % tag)
        return None

    phone = _get_step_with_id(steps, 'message_phone')
    if not phone:
        logging.error("Did not find step with id 'phone'. Can not process message_flow_member_result with tag %s" % tag)
        return None

    reason = _get_step_with_id(steps, 'message_reason')
    if not reason:
        logging.error("Did not find step with id 'reason'. Can not process message_flow_member_result with tag %s" % tag)
        return None

    logging.info("Saving appointment from %s" % user_details[0].email)

    sln_settings = get_solution_settings(service_user)
    days_str = []

    language = sln_settings.main_language or DEFAULT_LANGUAGE

    for timeframe_id in day.form_result.result.values:
        sawt = SolutionAppointmentWeekdayTimeframe.get_by_id(int(timeframe_id), parent_key(service_user, sln_settings.solution))
        if sawt:
            days_str.append(sawt.label(language))

    msg_appointment = """%s:
%s

%s: %s

%s:
%s""" % (common_translate(language, SOLUTION_COMMON , 'days'),
         "\n".join(days_str),
         common_translate(language, SOLUTION_COMMON , 'phone'),
         phone.form_result.result.value,
         common_translate(language, SOLUTION_COMMON , 'reason'),
         reason.form_result.result.value)

    msg = common_translate(language, SOLUTION_COMMON, 'if-appointment-received', appointment=msg_appointment)

    message = create_solution_inbox_message(service_user, service_identity, SolutionInboxMessage.CATEGORY_APPOINTMENT, None, False, user_details, reason.acknowledged_timestamp, msg, True)

    app_user = create_app_user_by_email(user_details[0].email, user_details[0].app_id)

    send_inbox_forwarders_message(service_user, service_identity, app_user, msg, {
                'if_name': user_details[0].name,
                'if_email':user_details[0].email
            }, message_key=message.solution_inbox_message_key, reply_enabled=message.reply_enabled)

    sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, service_identity)
    send_message(service_user, u"solutions.common.messaging.update",
                 service_identity=service_identity,
                 message=serialize_complex_value(SolutionInboxMessageTO.fromModel(message, sln_settings, sln_i_settings, True), SolutionInboxMessageTO, False))

    return None

@returns(NoneType)
@arguments(service_user=users.User, appointment_id=(int, long, NoneType), day=int, time_from=int, time_until=int)
def put_appointment_weekday_timeframe(service_user, appointment_id, day, time_from, time_until):
    sln_settings = get_solution_settings(service_user)
    if time_from == time_until:
        raise BusinessException(common_translate(sln_settings.main_language, SOLUTION_COMMON, 'time-start-end-equal'))
    if time_from >= time_until:
        raise BusinessException(common_translate(sln_settings.main_language, SOLUTION_COMMON, 'time-start-end-smaller'))

    sln_settings = get_solution_settings(service_user)
    if appointment_id:
        sawt = SolutionAppointmentWeekdayTimeframe.get_by_id(appointment_id, parent_key(service_user, sln_settings.solution))
        sawt.day = day
        sawt.time_from = time_from
        sawt.time_until = time_until
    else:
        sawt = SolutionAppointmentWeekdayTimeframe.get_or_create(parent_key(service_user, sln_settings.solution), day,
                                                                 time_from, time_until)
    sawt.put()

    sln_settings = get_solution_settings(service_user)
    sln_settings.updates_pending = True
    put_and_invalidate_cache(sln_settings)

    broadcast_updates_pending(sln_settings)
    send_message(service_user, u"solutions.common.appointment.settings.timeframe.update")


@returns(NoneType)
@arguments(service_user=users.User, appointment_id=(int, long))
def delete_appointment_weekday_timeframe(service_user, appointment_id):
    sln_settings = get_solution_settings(service_user)
    sawt = SolutionAppointmentWeekdayTimeframe.get_by_id(appointment_id, parent_key(service_user, sln_settings.solution))
    if sawt:
        sawt.delete()
        sln_settings = get_solution_settings(service_user)
        sln_settings.updates_pending = True
        put_and_invalidate_cache(sln_settings)

        broadcast_updates_pending(sln_settings)
        send_message(service_user, u"solutions.common.appointment.settings.timeframe.update")
