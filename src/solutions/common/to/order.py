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

from mcfw.properties import bool_property, long_property, unicode_property, typed_property
from rogerthat.to import TO
from solutions import translate as common_translate
from solutions.common.consts import SECONDS_IN_MINUTE
from solutions.common.models.order import SolutionOrderSettings
from solutions.common.to.payments import TransactionDetailsTO


class OrderPauseSettingsTO(TO):
    enabled = bool_property('enabled')
    paused_until = unicode_property('paused_until')
    message = unicode_property('message')


class SolutionOrderSettingsTO(TO):
    text_1 = unicode_property('1')
    order_type = long_property('2')
    leap_time = long_property('3')
    leap_time_type = long_property('4')
    order_ready_message = unicode_property('5')
    manual_confirmation = bool_property('6', default=False)
    pause_settings = typed_property('pause_settings', OrderPauseSettingsTO)
    disable_order_outside_hours = bool_property('disable_order_outside_hours')
    outside_hours_message = unicode_property('outside_hours_message')

    @classmethod
    def fromModel(cls, obj, language):
        # type: (SolutionOrderSettings, unicode) -> SolutionOrderSettingsTO
        if obj is None:
            return None
        to = cls()
        text_1 = None
        pause_msg = common_translate(language, 'default_orders_paused_message')
        outside_hours_msg = common_translate(language, 'default_outside_hours_message')
        if obj:
            text_1 = obj.text_1
            to.order_type = obj.order_type
            to.leap_time = obj.leap_time
            to.leap_time_type = obj.leap_time_type
            to.order_ready_message = obj.order_ready_message
            to.manual_confirmation = obj.manual_confirmation
            p_until = obj.pause_settings_paused_until.isoformat() + 'Z' if obj.pause_settings_paused_until else None
            to.pause_settings = OrderPauseSettingsTO(enabled=obj.pause_settings_enabled,
                                                     paused_until=p_until,
                                                     message=obj.pause_settings_message or pause_msg)
            to.disable_order_outside_hours = obj.disable_order_outside_hours
            to.outside_hours_message = obj.outside_hours_message or outside_hours_msg
        else:
            to.order_type = SolutionOrderSettings.DEFAULT_ORDER_TYPE
            to.leap_time = 15
            to.leap_time_type = SECONDS_IN_MINUTE
            to.pause_settings = OrderPauseSettingsTO(enabled=False, paused_until=None, message=pause_msg)
            to.disable_order_outside_hours = False
            to.outside_hours_message = outside_hours_msg
        if not text_1:
            text_1 = common_translate(language, 'order-flow-details')

        to.text_1 = text_1
        if not to.order_ready_message:
            to.order_ready_message = common_translate(language, 'order-ready')
        return to


class SolutionOrderTO(TO):
    key = unicode_property('1')
    description = unicode_property('2')
    status = long_property('3')
    sender_name = unicode_property('4')
    sender_avatar_url = unicode_property('5')
    timestamp = long_property('6')
    picture_url = unicode_property('7')
    phone_number = unicode_property('8')
    solution_inbox_message_key = unicode_property('9')
    takeaway_time = long_property('10')
    transaction = typed_property('transaction', TransactionDetailsTO)

    @classmethod
    def from_model(cls, model, transaction):
        to = SolutionOrderTO()
        to.key = unicode(model.solution_order_key)
        to.description = model.description
        to.status = model.status
        to.sender_name = model.sender.name
        to.sender_avatar_url = model.sender.avatar_url
        to.timestamp = model.timestamp
        to.picture_url = model.picture_url
        to.phone_number = model.phone_number
        to.solution_inbox_message_key = model.solution_inbox_message_key
        to.takeaway_time = model.takeaway_time
        to.transaction = TransactionDetailsTO.from_model(transaction) if transaction else None
        return to
