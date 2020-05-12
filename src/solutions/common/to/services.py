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

from mcfw.properties import typed_property, unicode_list_property, long_property, unicode_property

from solutions.common.to.qanda import ModuleTO


class ModuleAndBroadcastTypesTO(object):
    modules = typed_property('1', ModuleTO, True)
    broadcast_types = unicode_list_property('2')

    def __init__(self, modules=None, broadcast_types=None):
        self.modules = sorted(modules, key=lambda m: m.label.lower())
        self.broadcast_types = sorted(broadcast_types)


class ServiceStatisticTO(object):
    future_events_count = long_property('1')
    broadcasts_last_month = long_property('2')
    static_content_count = long_property('3')
    last_unanswered_question_timestamp = long_property('4')

    @classmethod
    def create(cls, future_events_count, broadcasts_last_month, static_content_count,
               last_unanswered_question_timestamp):
        to = cls()
        to.future_events_count = future_events_count
        to.broadcasts_last_month = broadcasts_last_month
        to.static_content_count = static_content_count
        to.last_unanswered_question_timestamp = last_unanswered_question_timestamp
        return to


class ServiceListTO(object):
    service_email = unicode_property('0')
    name = unicode_property('1')
    statistics = typed_property('2', ServiceStatisticTO)
    modules = unicode_list_property('3')
    customer_id = long_property('4')

    def __init__(self, service_email=None, name=None, statistics=None, modules=None, customer_id=None):
        self.service_email = service_email
        self.name = name
        self.statistics = statistics
        self.modules = modules
        self.customer_id = customer_id


class ServicesTO(object):
    services = typed_property('1', ServiceListTO, True)
    generated_on = long_property('2')
    cursor = unicode_property('3')

    def __init__(self, services=None, generated_on=None, cursor=None):
        self.services = services
        self.generated_on = generated_on
        self.cursor = cursor
