# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
# NOTICE: THIS FILE HAS BEEN MODIFIED BY GREEN VALLEY BELGIUM NV IN ACCORDANCE WITH THE APACHE LICENSE VERSION 2.0
# Copyright 2018 GIG Technology NV
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
# @@license_version:1.6@@

from mcfw.properties import unicode_property, long_property, typed_property
from rogerthat.models.properties.forms import FormResult, Form
from rogerthat.to import TO


class BaseFlowStepTO(TO):
    TYPE_MESSAGE = u"message_step"
    TYPE_FORM = u"form_step"

    step_id = unicode_property('1')
    message_flow_id = unicode_property('2')
    received_timestamp = long_property('3')
    acknowledged_timestamp = long_property('4')
    step_type = unicode_property('5')
    answer_id = unicode_property('6')
    message = unicode_property('7')
    button = unicode_property('8')

    def get_value(self):
        raise NotImplementedError()


class MessageFlowStepTO(BaseFlowStepTO):
    TYPE = BaseFlowStepTO.TYPE_MESSAGE

    def get_value(self):
        return self.answer_id


class FormFlowStepTO(BaseFlowStepTO):
    TYPE = BaseFlowStepTO.TYPE_FORM
    form_result = typed_property('51', FormResult)
    display_value = unicode_property('52')
    form_type = unicode_property('53')

    def get_value(self):
        if self.answer_id == Form.POSITIVE:
            return self.form_result.result.get_value()
        else:
            return None


class MessageType(object):
    MESSAGE = MessageFlowStepTO.TYPE
    FORM = FormFlowStepTO.TYPE


FLOW_STEP_MAPPING = {MessageType.MESSAGE: MessageFlowStepTO, MessageType.FORM: FormFlowStepTO}


class MessageFlowDesignTO(object):
    identifier = unicode_property('1')
    name = unicode_property('2')
    last_modified = long_property('3')

    @staticmethod
    def fromMessageFlowDesign(design):
        mfd = MessageFlowDesignTO()
        mfd.identifier = unicode(design.key())
        mfd.name = unicode(design.name)
        mfd.last_modified = design.design_timestamp
        return mfd
