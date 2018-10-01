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

import itertools
import logging
from datetime import datetime
from types import NoneType

from google.appengine.ext import deferred, db, ndb

import pytz
from babel import dates
from babel.dates import format_datetime, get_timezone
from mcfw.properties import azzert
from mcfw.properties import object_factory
from mcfw.rpc import returns, arguments, serialize_complex_value
from rogerthat.models import Message
from rogerthat.models.properties.forms import PayWidgetResult
from rogerthat.rpc import users
from rogerthat.service.api import messaging
from rogerthat.to.messaging import MemberTO
from rogerthat.to.messaging.flow import FLOW_STEP_MAPPING
from rogerthat.to.messaging.service_callback_results import FlowMemberResultCallbackResultTO, \
    TYPE_MESSAGE, MessageCallbackResultTypeTO, MessageAcknowledgedCallbackResultTO, TYPE_FLOW, FlowCallbackResultTypeTO
from rogerthat.to.service import UserDetailsTO
from rogerthat.utils import now
from rogerthat.utils.app import create_app_user_by_email
from rogerthat.utils.channel import send_message
from solutions import translate as common_translate
from solutions.common import SOLUTION_COMMON
from solutions.common.bizz import get_first_fmr_step_result_value, SolutionModule
from solutions.common.bizz.inbox import create_solution_inbox_message, add_solution_inbox_message
from solutions.common.bizz.loyalty import update_user_data_admins
from solutions.common.bizz.payment import get_transaction_details
from solutions.common.dal import get_solution_settings, get_solution_main_branding, \
    get_solution_settings_or_identity_settings
from solutions.common.exceptions.sandwich import InvalidSandwichSettingsException
from solutions.common.models import SolutionInboxMessage
from solutions.common.models.properties import SolutionUser
from solutions.common.models.sandwich import SandwichType, SandwichTopping, \
    SandwichOrder, SandwichOption, SandwichSettings, SandwichOrderDetail
from solutions.common.to import SolutionInboxMessageTO
from solutions.common.utils import create_service_identity_user_wo_default


@returns(FlowMemberResultCallbackResultTO)
@arguments(service_user=users.User, message_flow_run_id=unicode, member=unicode,
           steps=[object_factory("step_type", FLOW_STEP_MAPPING)], end_id=unicode, end_message_flow_id=unicode,
           parent_message_key=unicode, tag=unicode, result_key=unicode, flush_id=unicode, flush_message_flow_id=unicode,
           service_identity=unicode, user_details=[UserDetailsTO])
def order_sandwich_received(service_user, message_flow_run_id, member, steps, end_id, end_message_flow_id,
                            parent_message_key, tag, result_key, flush_id, flush_message_flow_id, service_identity,
                            user_details):
    sln_settings = get_solution_settings(service_user)
    step_mapping = {
        'message_type': [],
        'message_topping': [],
        'message_customize': [],
    }

    for step in steps:
        if step.step_id in step_mapping:
            step_mapping[step.step_id].append(step.get_value())

    # if there is only one type, the 'type' step isn't shown, so we get that sandwich type from the db.
    default_sandwich_type_id = None
    if not step_mapping['message_type']:
        sandwich_type = SandwichType.list(service_user, sln_settings.solution).get()
        default_sandwich_type_id = 'type_%d' % sandwich_type.type_id
    sandwiches = []
    for type_, topping, customizations in itertools.izip_longest(step_mapping['message_type'],
                                                                 step_mapping['message_topping'],
                                                                 step_mapping['message_customize']):
        sandwiches.append({
            u'type': type_ or default_sandwich_type_id,
            u'topping': topping,
            u'customizations': customizations or []
        })

    remark = get_first_fmr_step_result_value(steps, u'message_remark')
    takeaway_time = get_first_fmr_step_result_value(steps, u'message_takeaway_time')
    pay_result = get_first_fmr_step_result_value(steps, u'message_pay_required') or \
                 get_first_fmr_step_result_value(steps, u'message_pay_optional')

    sln_settings = get_solution_settings(service_user)

    # check if it's only one type/topping
    if type_ is None:
        sandwich_type = SandwichType.list(service_user, sln_settings.solution).get()
        type_ = 'type_%d' % sandwich_type.type_id

    deferred.defer(process_sandwich_orders, service_user, service_identity, user_details, sandwiches,
                   remark, takeaway_time, parent_message_key, pay_result)

    main_branding = get_solution_main_branding(service_user)

    result = FlowMemberResultCallbackResultTO()
    result.type = TYPE_MESSAGE
    result.value = MessageCallbackResultTypeTO()
    result.value.flags = Message.FLAG_ALLOW_DISMISS | Message.FLAG_AUTO_LOCK
    result.value.answers = []
    result.value.alert_flags = Message.ALERT_FLAG_SILENT
    result.value.attachments = []
    result.value.branding = main_branding.branding_key
    result.value.dismiss_button_ui_flags = 0
    result.value.tag = None
    result.value.message = common_translate(sln_settings.main_language, SOLUTION_COMMON, u'order-sandwich-received')
    result.value.step_id = u'message_sandwich_ordered'
    return result


def get_sandwich_models(service_user, type_ids, topping_ids, option_ids):
    # type: (users.User, set[int], set[int], set[int]) -> tuple[dict[int, SandwichType], dict[int, SandwichTopping], dict[int, SandwichOption]]
    keys = [SandwichType.create_key(service_user, id_) for id_ in type_ids] + \
           [SandwichTopping.create_key(service_user, id_) for id_ in topping_ids] + \
           [SandwichOption.create_key(service_user, id_) for id_ in option_ids]
    models = ndb.get_multi(keys)
    types = {model.id: model for model in models if isinstance(model, SandwichType)}
    toppings = {model.id: model for model in models if isinstance(model, SandwichTopping)}
    options = {model.id: model for model in models if isinstance(model, SandwichOption)}
    return types, toppings, options


def process_sandwich_orders(service_user, service_identity, user_details, sandwiches,
                           remark, takeaway_time, parent_message_key, pay_result=None):
    from solutions.common.bizz.messaging import send_inbox_forwarders_message

    now_ = now()
    sln_settings = get_solution_settings(service_user)
    sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, service_identity)
    timezone_offset = datetime.now(pytz.timezone(sln_settings.timezone)).utcoffset().total_seconds()
    lang = sln_settings.main_language

    total_price = 0
    sandwich_msg = []
    sandwich_details = []
    logging.info("sandwiches: %s", sandwiches)
    type_ids = set()
    topping_ids = set()
    option_ids = set()
    for sandwich in sandwiches:
        type_id = int(sandwich[u'type'].split('_')[-1])
        topping_id = int(sandwich[u'topping'].split('_')[-1]) if sandwich[u'topping'] else None
        opt_ids = [int(c.split('_')[-1]) for c in sandwich[u'customizations'] or []]
        type_ids.add(type_id)
        topping_ids.add(topping_id)
        option_ids.update(opt_ids)
    types, toppings, options = get_sandwich_models(service_user, type_ids, topping_ids, option_ids)
    for sandwich in sandwiches:
        type_id = int(sandwich[u'type'].split('_')[-1])
        topping_id = int(sandwich[u'topping'].split('_')[-1]) if sandwich[u'topping'] else None
        option_ids = [int(c.split('_')[-1]) for c in sandwich[u'customizations'] or []]

        sandwich_details.append(SandwichOrderDetail(
            type_id=type_id,
            topping_id=topping_id,
            option_ids=option_ids,
        ))

        sandwich_type = types[type_id]
        sandwich_topping = toppings[topping_id]
        sandwich_options = [options[id_] for id_ in option_ids]

        logging.info("type: %s\ntopping: %s\n options: %s", sandwich_type, sandwich_topping, sandwich_options)

        total_price += sum(
            [sandwich_type.price, sandwich_topping.price if sandwich_topping else 0] + [sc.price for sc in
                                                                                        sandwich_options])

        customizations = ['']
        customizations.extend([sw.description for sw in sandwich_options])
        msg = common_translate(lang, SOLUTION_COMMON, 'if-sandwich-order-received-detail',
                               sandwich_type=sandwich_type.description,
                               topping=sandwich_topping.description if sandwich_topping else u"",
                               customizations=u"\n - ".join(customizations))
        sandwich_msg.append(msg)

    msg = common_translate(lang, SOLUTION_COMMON, 'if-sandwich-order-received',
                           sandwiches=u"\n".join(sandwich_msg),
                           remarks=remark or "")
    if takeaway_time:
        takeaway_time = long(takeaway_time - timezone_offset)
        takeaway_time_str = format_datetime(
            datetime.fromtimestamp(takeaway_time, tz=get_timezone(sln_settings.timezone)), format='short',
            locale=lang)
        msg = '%s\n%s: %s' % (msg, common_translate(lang, SOLUTION_COMMON, 'takeaway_time'), takeaway_time_str)

    create_inbox_message = True
    service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
    sandwich_key = SandwichOrder.create_key(parent_message_key, service_identity_user)
    sandwich = sandwich_key.get() or SandwichOrder(key=sandwich_key)
    if sandwich.solution_inbox_message_key:
        create_inbox_message = False

    sandwich.sender = SolutionUser.fromTO(user_details[0])
    sandwich.order_time = now_
    sandwich.price = total_price
    sandwich.details = sandwich_details
    sandwich.remark = remark
    sandwich.status = SandwichOrder.STATUS_RECEIVED
    sandwich.takeaway_time = takeaway_time
    if pay_result:
        assert isinstance(pay_result, PayWidgetResult)
        app_user = user_details[0].toAppUser()
        transaction_details = get_transaction_details(pay_result.provider_id, pay_result.transaction_id, service_user,
                                                      service_identity, app_user)
        sandwich.transaction_id = pay_result.transaction_id
        sandwich.payment_provider = pay_result.provider_id
        if transaction_details:
            msg += u'\n%s' % common_translate(lang, SOLUTION_COMMON, 'order_received_paid',
                                              amount=u'%.2f' % transaction_details.get_display_amount(),
                                              currency=transaction_details.currency)
        elif sln_i_settings.payment_enabled:
            msg += u'\n%s' % common_translate(lang, SOLUTION_COMMON, 'order_not_paid_yet')

    sm_data = [{u"type": u"solutions.common.sandwich.orders.update"}]

    if create_inbox_message:
        message = create_solution_inbox_message(service_user, service_identity, SolutionInboxMessage.CATEGORY_SANDWICH_BAR, None, False, user_details, now_, msg, True)
        sandwich.solution_inbox_message_key = message.solution_inbox_message_key
        sandwich.put()
        message.category_key = sandwich_key.urlsafe()
        message.put()

        sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, service_identity)

        sm_data.append({
            u'type': u'solutions.common.messaging.update',
            u'message': SolutionInboxMessageTO.fromModel(message, sln_settings, sln_i_settings, True).to_dict()
        })
        app_user = create_app_user_by_email(user_details[0].email, user_details[0].app_id)
        send_inbox_forwarders_message(service_user, service_identity, app_user, msg, {
                    'if_name': user_details[0].name,
                    'if_email': user_details[0].email
                }, message_key=message.solution_inbox_message_key, reply_enabled=message.reply_enabled)

    send_message(service_user, sm_data, service_identity=service_identity)

    if SolutionModule.LOYALTY in sln_settings.modules:
        deferred.defer(update_user_data_admins, service_user, service_identity)


@returns(NoneType)
@arguments(service_user=users.User, service_identity=unicode, sandwich_id=unicode, message=unicode)
def reply_sandwich_order(service_user, service_identity, sandwich_id, message=unicode):
    from solutions.common.bizz.messaging import send_inbox_forwarders_message

    sln_settings = get_solution_settings(service_user)
    sandwich_order = SandwichOrder.get_by_order_id(service_user, service_identity, sandwich_id)
    azzert(service_user == sandwich_order.service_user)
    sandwich_order.status = SandwichOrder.STATUS_REPLIED
    sandwich_order.put()

    sm_data = [{u'type': u'solutions.common.sandwich.orders.update'}]

    if sandwich_order.solution_inbox_message_key:
        sim_parent, _ = add_solution_inbox_message(service_user, sandwich_order.solution_inbox_message_key, True, None, now(), message, mark_as_unread=False, mark_as_read=True)
        send_inbox_forwarders_message(service_user, sim_parent.service_identity, None, message, {
                    'if_name': sim_parent.sender.name,
                    'if_email':sim_parent.sender.email
                }, message_key=sim_parent.solution_inbox_message_key, reply_enabled=sim_parent.reply_enabled)
        sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, sandwich_order.service_identity)
        sm_data.append({u"type": u"solutions.common.messaging.update",
                     u"message": serialize_complex_value(SolutionInboxMessageTO.fromModel(sim_parent, sln_settings, sln_i_settings, True), SolutionInboxMessageTO, False)})
    else:
        sln_main_branding = get_solution_main_branding(service_user)
        branding = sln_main_branding.branding_key if sln_main_branding else None

        member = MemberTO()
        member.alert_flags = Message.ALERT_FLAG_VIBRATE
        member.member = sandwich_order.sender.email
        member.app_id = sandwich_order.sender.app_id

        messaging.send(parent_key=None,
                       parent_message_key=None,
                       message=message,
                       answers=[],
                       flags=Message.FLAG_ALLOW_DISMISS,
                       members=[member],
                       branding=branding,
                       tag=None,
                       service_identity=sandwich_order.service_identity)

    send_message(service_user, sm_data, service_identity=sandwich_order.service_identity)


@returns(NoneType)
@arguments(service_user=users.User, service_identity=unicode, sandwich_id=unicode, message=unicode)
def ready_sandwich_order(service_user, service_identity, sandwich_id, message):
    from solutions.common.bizz.messaging import send_inbox_forwarders_message

    sln_settings = get_solution_settings(service_user)
    def txn():
        m = SandwichOrder.get_by_order_id(service_user, service_identity, sandwich_id)
        azzert(service_user == m.service_user)
        m.status = SandwichOrder.STATUS_READY
        m.put()
        return m

    xg_on = db.create_transaction_options(xg=True)
    sandwich_order = db.run_in_transaction_options(xg_on, txn)

    sm_data = [{u'type': u'solutions.common.sandwich.orders.update'}]

    if message:
        if sandwich_order.solution_inbox_message_key:
            sim_parent, _ = add_solution_inbox_message(service_user, sandwich_order.solution_inbox_message_key, True, None, now(), message, mark_as_unread=False, mark_as_read=True)
            send_inbox_forwarders_message(service_user, sim_parent.service_identity, None, message, {
                        'if_name': sim_parent.sender.name,
                        'if_email':sim_parent.sender.email
                    }, message_key=sim_parent.solution_inbox_message_key, reply_enabled=sim_parent.reply_enabled)
            sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, sandwich_order.service_identity)
            sm_data.append({u"type": u"solutions.common.messaging.update",
                         u"message": serialize_complex_value(SolutionInboxMessageTO.fromModel(sim_parent, sln_settings, sln_i_settings, True), SolutionInboxMessageTO, False)})
        else:
            branding = get_solution_main_branding(service_user).branding_key
            member = MemberTO()
            member.alert_flags = Message.ALERT_FLAG_VIBRATE
            member.member = sandwich_order.sender.email
            member.app_id = sandwich_order.sender.app_id

            messaging.send(parent_key=None,
                           parent_message_key=None,
                           message=message,
                           answers=[],
                           flags=Message.FLAG_ALLOW_DISMISS,
                           members=[member],
                           branding=branding,
                           tag=None,
                           service_identity=sandwich_order.service_identity)

    elif sandwich_order.solution_inbox_message_key:
        sim_parent = SolutionInboxMessage.get(sandwich_order.solution_inbox_message_key)
        if not sim_parent.read:
            sim_parent.read = True
            sim_parent.put()
            deferred.defer(update_user_data_admins, service_user, sandwich_order.service_identity)
        sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, sandwich_order.service_identity)
        sm_data.append({u"type": u"solutions.common.messaging.update",
                     u"message": serialize_complex_value(SolutionInboxMessageTO.fromModel(sim_parent, sln_settings, sln_i_settings, True), SolutionInboxMessageTO, False)})

    send_message(service_user, sm_data, service_identity=sandwich_order.service_identity)

@returns(NoneType)
@arguments(service_user=users.User, service_identity=unicode, sandwich_id=unicode, message=unicode)
def delete_sandwich_order(service_user, service_identity, sandwich_id, message):
    from solutions.common.bizz.messaging import send_inbox_forwarders_message

    sln_settings = get_solution_settings(service_user)

    def txn():
        m = SandwichOrder.get_by_order_id(service_user, service_identity, sandwich_id)
        azzert(service_user == m.service_user)
        m.deleted = True
        m.put()
        return m

    xg_on = db.create_transaction_options(xg=True)
    sandwich_order = db.run_in_transaction_options(xg_on, txn)

    sm_data = [{u"type": u"solutions.common.sandwich.orders.deleted", u'sandwich_id': sandwich_id}]

    if message:
        if sandwich_order.solution_inbox_message_key:
            sim_parent, _ = add_solution_inbox_message(service_user, sandwich_order.solution_inbox_message_key, True, None, now(), message, mark_as_unread=False, mark_as_read=True, mark_as_trashed=True)
            send_inbox_forwarders_message(service_user, sim_parent.service_identity, None, message, {
                        'if_name': sim_parent.sender.name,
                        'if_email':sim_parent.sender.email
                    }, message_key=sim_parent.solution_inbox_message_key, reply_enabled=sim_parent.reply_enabled)
            sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, sandwich_order.service_identity)
            sm_data.append({u"type": u"solutions.common.messaging.update",
                         u"message": serialize_complex_value(SolutionInboxMessageTO.fromModel(sim_parent, sln_settings, sln_i_settings, True), SolutionInboxMessageTO, False)})

        else:
            branding = get_solution_main_branding(service_user).branding_key
            member = MemberTO()
            member.alert_flags = Message.ALERT_FLAG_VIBRATE
            member.member = sandwich_order.sender.email
            member.app_id = sandwich_order.sender.app_id

            messaging.send(parent_key=None,
                           parent_message_key=None,
                           message=message,
                           answers=[],
                           flags=Message.FLAG_ALLOW_DISMISS,
                           members=[member],
                           branding=branding,
                           tag=None,
                           service_identity=sandwich_order.service_identity)

    elif sandwich_order.solution_inbox_message_key:
        sim_parent = SolutionInboxMessage.get(sandwich_order.solution_inbox_message_key)
        if not sim_parent.trashed and not sim_parent.deleted:
            sim_parent.trashed = True
            sim_parent.put()
            deferred.defer(update_user_data_admins, service_user, sandwich_order.service_identity)
        sln_i_settings = get_solution_settings_or_identity_settings(sln_settings, sandwich_order.service_identity)
        sm_data.append({u"type": u"solutions.common.messaging.update",
                     u"message": serialize_complex_value(SolutionInboxMessageTO.fromModel(sim_parent, sln_settings, sln_i_settings, True), SolutionInboxMessageTO, False)})

    send_message(service_user, sm_data, service_identity=sandwich_order.service_identity)


@returns(MessageAcknowledgedCallbackResultTO)
@arguments(service_user=users.User, status=int, answer_id=unicode, received_timestamp=int, member=unicode,
           message_key=unicode, tag=unicode, acked_timestamp=int, parent_message_key=unicode, result_key=unicode,
           service_identity=unicode, user_details=[UserDetailsTO])
def sandwich_order_from_broadcast_pressed(service_user, status, answer_id, received_timestamp, member, message_key, tag,
                                   acked_timestamp, parent_message_key, result_key, service_identity, user_details):
    from solutions.common.bizz.messaging import POKE_TAG_SANDWICH_BAR
    if answer_id != u'order':
        return

    result = MessageAcknowledgedCallbackResultTO()
    sln_settings = get_solution_settings(service_user)
    settings = SandwichSettings.get_settings(service_user, sln_settings.solution)
    result.type = TYPE_FLOW
    result.value = FlowCallbackResultTypeTO()
    result.value.flow = settings.order_flow
    result.value.force_language = None
    result.value.tag = POKE_TAG_SANDWICH_BAR
    return result


def get_sandwich_reminder_broadcast_type(language, day):
    return common_translate(language, SOLUTION_COMMON, u'order-sandwich-broadcast-day-broadcast-type',
                            day=dates.get_day_names('wide', 'format', language)[SandwichSettings.DAYS.index(day)])


def validate_sandwiches(language, sandwich_types, sandwich_toppings, sandwich_options):
    """
    Args:
        language (unicode)
        sandwich_types (list of SandwichType)
        sandwich_toppings (list of SandwichToppings)
        sandwich_options (list of SandwichOption)
    Raises:
        InvalidSandwichSettingsException
    """
    errors = set()
    type_labels = []
    topping_lables = []
    option_labels = []
    for sandwich_type in sandwich_types:
        if sandwich_type.description in type_labels:
            msg = common_translate(language, SOLUTION_COMMON, 'duplicate_sandwich_type',
                                   label=sandwich_type.description)
            errors.add(msg)
        else:
            type_labels.append(sandwich_type.description)
    if len(sandwich_toppings) < 2:
        errors.add(common_translate(language, SOLUTION_COMMON, 'insufficient_toppings'))
    for sandwich_topping in sandwich_toppings:
        if sandwich_topping.description in topping_lables:
            msg = common_translate(language, SOLUTION_COMMON, 'duplicate_sandwich_topping',
                                   label=sandwich_topping.description)
            errors.add(msg)
        else:
            topping_lables.append(sandwich_topping.description)
    for sandwich_option in sandwich_options:
        if sandwich_option.description in option_labels:
            msg = common_translate(language, SOLUTION_COMMON, 'duplicate_sandwich_option',
                                   label=sandwich_option.description)
            errors.add(msg)
        else:
            option_labels.append(sandwich_option.description)
    if errors:
        raise InvalidSandwichSettingsException('\n'.join(errors))
