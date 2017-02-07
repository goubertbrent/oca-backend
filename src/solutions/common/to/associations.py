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

from mcfw.properties import typed_property, unicode_list_property, long_property, unicode_property
from solutions.common.to.qanda import ModuleTO


class ModuleAndBroadcastTypesTO(object):
    modules = typed_property('1', ModuleTO, True)
    broadcast_types = unicode_list_property('2')

    @classmethod
    def create(cls, modules, broadcast_types):
        to = cls()
        to.modules = sorted(modules, key=lambda m: m.label.lower())
        to.broadcast_types = sorted(broadcast_types)
        return to


class AssociationStatisticTO(object):
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


class ServiceTO(object):
    service_email = unicode_property('0')
    name = unicode_property('1')
    statistics = typed_property('2', AssociationStatisticTO)
    modules = unicode_list_property('3')

    @staticmethod
    def create(service_email, name, statistics, modules):
        service = ServiceTO()
        service.service_email = service_email
        service.name = name
        service.statistics = statistics
        service.modules = modules
        return service


class AssociationsTO(object):
    associations = typed_property('1', ServiceTO, True)
    generated_on = long_property('2')

    @classmethod
    def create(cls, associations, generated_on):
        obj = cls()
        obj.associations = associations
        obj.generated_on = generated_on
        return obj
