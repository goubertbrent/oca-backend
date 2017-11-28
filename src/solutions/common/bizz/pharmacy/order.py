# -*- coding: utf-8 -*-
# Copyright 2017 Mobicage NV
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

from google.appengine.ext import db, deferred
from mcfw.properties import azzert, object_factory
from mcfw.rpc import returns, arguments, serialize_complex_value
from rogerthat.dal import parent_key_unsafe
from rogerthat.models import Message
from rogerthat.rpc import users
from rogerthat.service.api import messaging
from rogerthat.to.messaging import AttachmentTO, MemberTO
from rogerthat.to.messaging.flow import FLOW_STEP_MAPPING
from rogerthat.to.messaging.service_callback_results import FlowMemberResultCallbackResultTO
from rogerthat.to.service import UserDetailsTO
from rogerthat.utils import now
from rogerthat.utils.app import create_app_user_by_email
from rogerthat.utils.channel import send_message
from solutions import translate
from solutions.common import SOLUTION_COMMON
from solutions.common.bizz import _get_value
from solutions.common.bizz.inbox import create_solution_inbox_message, add_solution_inbox_message
from solutions.common.bizz.loyalty import update_user_data_admins
from solutions.common.dal import get_solution_main_branding, get_solution_settings, \
    get_solution_settings_or_identity_settings
from solutions.common.models import SolutionInboxMessage
from solutions.common.models.pharmacy.order import SolutionPharmacyOrder
from solutions.common.models.properties import SolutionUser
from solutions.common.to import SolutionInboxMessageTO
from solutions.common.utils import create_service_identity_user_wo_default


@returns(FlowMemberResultCallbackResultTO)
@arguments(service_user=users.User, message_flow_run_id=unicode, member=unicode,
           steps=[object_factory("step_type", FLOW_STEP_MAPPING)], end_id=unicode, end_message_flow_id=unicode,
           parent_message_key=unicode, tag=unicode, result_key=unicode, flush_id=unicode, flush_message_flow_id=unicode,
           service_identity=unicode, user_details=[UserDetailsTO])
def pharmacy_order_received(service_user, message_flow_run_id, member, steps, end_id, end_message_flow_id, parent_message_key,
                            tag, result_key, flush_id, flush_message_flow_id, service_identity, user_details):

    from solutions.common.bizz.messaging import send_inbox_forwarders_message

    sln_settings = get_solution_settings(service_user)
    logging.info("_flow_member_result_pharmacy_order: \n %s" % steps)

    if "button_button_yes" == steps[0].answer_id:
        picture_url = _get_value(steps[1], u'message_photo_upload_prescription')
        description = None
        if u"positive" == steps[2].answer_id:
            remarks = _get_value(steps[2], u'message_message_remarks_box')
        else:
            remarks = ""
    else:
        if u"positive" == steps[1].answer_id:
            picture_url = _get_value(steps[1], u'message_message_photo_upload_box')
            description = None
            if u"positive" == steps[2].answer_id:
                remarks = _get_value(steps[2], u'message_message_remarks_box')
            else:
                remarks = ""
        else:
            picture_url = None
            description = _get_value(steps[2], u'message_message_describe_box')
            if u"positive" == steps[3].answer_id:
                remarks = _get_value(steps[3], u'message_message_remarks_box')
            else:
                remarks = ""

    logging.info("Saving pharmacy order from %s" % user_details[0].email)

    app_user = create_app_user_by_email(user_details[0].email, user_details[0].app_id)
    service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
    o = SolutionPharmacyOrder(parent=parent_key_unsafe(service_identity_user, SOLUTION_COMMON))
    o.description = description
    o.remarks = remarks
    o.sender = SolutionUser.fromTO(user_details[0])
    o.timestamp = steps[2].received_timestamp
    o.status = SolutionPharmacyOrder.STATUS_RECEIVED
    o.picture_url = picture_url
    o.user = app_user

    msg = translate(sln_settings.main_language, SOLUTION_COMMON, 'if-order-received',
                    remarks=remarks,
                    phone_number="")

    message = create_solution_inbox_message(service_user, service_identity,
                                            SolutionInboxMessage.CATEGORY_PHARMACY_ORDER, None, False, user_details,
                                            steps[2].received_timestamp, msg, True,
                                            [picture_url] if picture_url else [])
    o.solution_inbox_message_key = message.solution_inbox_message_key
    o.put()
    message.category_key = unicode(o.key())
    message.put()

    sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, service_identity)

    sm_data = []
    sm_data.append({u"type": u"solutions.common.pharmacy_orders.update"})
    sm_data.append({u"type": u"solutions.common.messaging.update",
                    u"message": serialize_complex_value(SolutionInboxMessageTO.fromModel(message, sln_settings, sln_i_settings, True), SolutionInboxMessageTO, False)})
    send_message(service_user, sm_data, service_identity=service_identity)

    if picture_url:
        att = AttachmentTO()
        att.content_type = AttachmentTO.CONTENT_TYPE_IMG_JPG
        att.download_url = picture_url
        att.name = translate(sln_settings.main_language, SOLUTION_COMMON, u'picture')
        att.size = 0
        send_inbox_forwarders_message(service_user, service_identity, app_user, msg, {
            'if_name': user_details[0].name,
            'if_email': user_details[0].email
        }, message_key=message.solution_inbox_message_key, attachments=[att], reply_enabled=message.reply_enabled)
    else:
        send_inbox_forwarders_message(service_user, service_identity, app_user, msg, {
            'if_name': user_details[0].name,
            'if_email': user_details[0].email
        }, message_key=message.solution_inbox_message_key, reply_enabled=message.reply_enabled)

    return None


@returns(NoneType)
@arguments(service_user=users.User, order_key=unicode, message=unicode)
def delete_pharmacy_order(service_user, order_key, message):
    from solutions.common.bizz.messaging import send_inbox_forwarders_message

    def txn():
        m = SolutionPharmacyOrder.get(order_key)
        azzert(service_user == m.service_user)
        m.deleted = True
        m.put()
        return m
    order = db.run_in_transaction(txn)

    sm_data = []
    sm_data.append({u"type": u"solutions.common.pharmacy_orders.update"})

    sln_settings = get_solution_settings(service_user)
    if message:
        if order.solution_inbox_message_key:
            sim_parent, _ = add_solution_inbox_message(service_user, order.solution_inbox_message_key, True, None,
                                                       now(), message, mark_as_unread=False, mark_as_read=True,
                                                       mark_as_trashed=True)
            send_inbox_forwarders_message(service_user, sim_parent.service_identity, None, message, {
                'if_name': sim_parent.sender.name,
                'if_email': sim_parent.sender.email
            }, message_key=sim_parent.solution_inbox_message_key, reply_enabled=sim_parent.reply_enabled)

            sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, order.service_identity)

            sm_data.append({u"type": u"solutions.common.messaging.update",
                            u"message": serialize_complex_value(SolutionInboxMessageTO.fromModel(sim_parent, sln_settings, sln_i_settings, True), SolutionInboxMessageTO, False)})
        else:
            branding = get_solution_main_branding(service_user).branding_key
            member = MemberTO()
            member.alert_flags = Message.ALERT_FLAG_VIBRATE
            member.member = order.sender.email
            member.app_id = order.sender.app_id

            messaging.send(parent_key=None,
                           parent_message_key=None,
                           message=message,
                           answers=[],
                           flags=Message.FLAG_ALLOW_DISMISS,
                           members=[member],
                           branding=branding,
                           tag=None,
                           service_identity=order.service_identity)

    elif order.solution_inbox_message_key:
        sim_parent = SolutionInboxMessage.get(order.solution_inbox_message_key)
        if not sim_parent.trashed and not sim_parent.deleted:
            sim_parent.trashed = True
            sim_parent.put()
            deferred.defer(update_user_data_admins, service_user, order.service_identity)
        sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, order.service_identity)
        sm_data.append({u"type": u"solutions.common.messaging.update",
                        u"message": serialize_complex_value(SolutionInboxMessageTO.fromModel(sim_parent, sln_settings, sln_i_settings, True), SolutionInboxMessageTO, False)})

    send_message(service_user, sm_data, service_identity=order.service_identity)


@returns(NoneType)
@arguments(service_user=users.User, order_key=unicode, order_status=int, message=unicode)
def send_message_for_pharmacy_order(service_user, order_key, order_status, message):
    from solutions.common.bizz.messaging import send_inbox_forwarders_message

    azzert(order_status in SolutionPharmacyOrder.ORDER_STATUSES)

    def txn():
        m = SolutionPharmacyOrder.get(order_key)
        azzert(service_user == m.service_user)
        if m.status == SolutionPharmacyOrder.STATUS_RECEIVED and m.status != order_status:
            m.status = order_status
            m.put()
        return m
    order = db.run_in_transaction(txn)

    sm_data = []
    sm_data.append({u"type": u"solutions.common.pharmacy_orders.update"})

    sln_settings = get_solution_settings(service_user)
    if message:
        if order.solution_inbox_message_key:
            sim_parent, _ = add_solution_inbox_message(
                service_user, order.solution_inbox_message_key, True, None, now(), message, mark_as_unread=False, mark_as_read=True)
            send_inbox_forwarders_message(service_user, sim_parent.service_identity, None, message, {
                'if_name': sim_parent.sender.name,
                'if_email': sim_parent.sender.email
            }, message_key=sim_parent.solution_inbox_message_key, reply_enabled=sim_parent.reply_enabled)
            sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, order.service_identity)
            sm_data.append({u"type": u"solutions.common.messaging.update",
                            u"message": serialize_complex_value(SolutionInboxMessageTO.fromModel(sim_parent, sln_settings, sln_i_settings, True), SolutionInboxMessageTO, False)})
        else:
            sln_main_branding = get_solution_main_branding(service_user)
            branding = sln_main_branding.branding_key if sln_main_branding else None

            member = MemberTO()
            member.alert_flags = Message.ALERT_FLAG_VIBRATE
            member.member = order.sender.email
            member.app_id = order.sender.app_id

            messaging.send(parent_key=None,
                           parent_message_key=None,
                           message=message,
                           answers=[],
                           flags=Message.FLAG_ALLOW_DISMISS,
                           members=[member],
                           branding=branding,
                           tag=None,
                           service_identity=order.service_identity)

    elif order.solution_inbox_message_key:
        sim_parent = SolutionInboxMessage.get(order.solution_inbox_message_key)
        if not sim_parent.read:
            sim_parent.read = True
            sim_parent.put()
            deferred.defer(update_user_data_admins, service_user, order.service_identity)
        sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, order.service_identity)
        sm_data.append({u"type": u"solutions.common.messaging.update",
                        u"message": serialize_complex_value(SolutionInboxMessageTO.fromModel(sim_parent, sln_settings, sln_i_settings, True), SolutionInboxMessageTO, False)})

    send_message(service_user, sm_data, service_identity=order.service_identity)
