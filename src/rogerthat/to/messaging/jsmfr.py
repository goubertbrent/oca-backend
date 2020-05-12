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

from mcfw.properties import unicode_property, typed_property, object_factory, unicode_list_property, bool_property, \
    long_property
from rogerthat.models.properties.forms import FormResult
from rogerthat.to.messaging import MessageTO
from rogerthat.to.messaging.flow import FLOW_STEP_MAPPING, MessageType
from rogerthat.to.messaging.forms import FormMessageTO
from rogerthat.to.system import LogErrorRequestTO


class Step(object_factory):
    step_type = unicode_property('step_type')

    def __init__(self):
        super(Step, self).__init__('step_type', FLOW_STEP_MAPPING, MessageType)


class JsMessageFlowMemberRunTO(object):
    parent_message_key = unicode_property('1')
    message_flow_run_id = unicode_property('2')
    sender = unicode_property('3')
    steps = typed_property('4', Step(), True)
    hashed_tag = unicode_property('5')  # when flow started by service menu item press: hashed_tag of item
    service_action = unicode_property('6')  # when flow started by QR scan: action of QR code
    flow_params = unicode_property('7')


class MessageFlowMemberResultRequestTO(object):
    flush_id = unicode_property('1')
    end_id = unicode_property('2')
    run = typed_property('3', JsMessageFlowMemberRunTO)
    results_email = bool_property('4')
    email_admins = bool_property('5')
    emails = unicode_list_property('6')
    message_flow_name = unicode_property('7')
    timestamp = long_property('8')


class MessageFlowMemberResultResponseTO(object):
    pass


class MessageFlowFinishedRequestTO(object):
    parent_message_key = unicode_property('1')
    message_flow_run_id = unicode_property('2')
    end_id = unicode_property('3')


class MessageFlowFinishedResponseTO(object):
    pass


class MessageFlowErrorRequestTO(LogErrorRequestTO):
    jsCommand = unicode_property('51')
    stackTrace = unicode_property('52')


class MessageFlowErrorResponseTO(object):
    pass


class NewMessageType(object):
    MESSAGE = 1
    FORM_MESSAGE = 2


class NewFlowMessageTO(object_factory):
    message_type = long_property('message_type')

    def __init__(self):
        super(NewFlowMessageTO, self).__init__('message_type', {NewMessageType.MESSAGE: MessageTO,
                                                                NewMessageType.FORM_MESSAGE: FormMessageTO},
                                               NewMessageType)


class NewFlowMessageRequestTO(object):
    message = typed_property('1', NewFlowMessageTO())
    message_flow_run_id = unicode_property('2', default=None)
    step_id = unicode_property('3', default=None)
    form_result = typed_property('101', FormResult)


class NewFlowMessageResponseTO(object):
    pass


class FlowStartedRequestTO(object):
    thread_key = unicode_property('1')
    service = unicode_property('2')
    static_flow_hash = unicode_property('3')
    message_flow_run_id = unicode_property('4')


class FlowStartedResponseTO(object):
    pass
