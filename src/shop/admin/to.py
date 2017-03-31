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

from mcfw.properties import unicode_property, long_property, float_property, typed_property


class MonitoringQueueTO(object):
    name = unicode_property('1')
    oldest_eta_usec = long_property('2')
    executed_last_minute = long_property('3')
    in_flight = long_property('4')
    enforced_rate = float_property('5')

    @staticmethod
    def from_model(name, model):
        to = MonitoringQueueTO()
        to.name = unicode(name)
        to.oldest_eta_usec = long(model.oldest_eta_usec) if model.oldest_eta_usec else 0
        to.executed_last_minute = long(model.executed_last_minute) if model.executed_last_minute else 0
        to.in_flight = long(model.in_flight) if model.in_flight else 0
        to.enforced_rate = float(model.enforced_rate) if model.enforced_rate else 0.0
        return to


class MonitoringClientErrorTO(object):
    platform = unicode_property('1')
    count = long_property('2')
    description = unicode_property('3')
    parent_id = unicode_property('4')

    @staticmethod
    def from_model(model):
        to = MonitoringClientErrorTO()
        to.platform = model.platform_string
        to.count = model.parent().occurenceCount
        to.description = model.parent().description
        to.parent_id = model.parent().key().name()
        return to


class MonitoringStatusTO(object):
    error_count = long_property('1')
    skipped_count = long_property('2')
    queues = typed_property('3', MonitoringQueueTO, True)
    five_min_ago = long_property('4')
    client_errors = typed_property('5', MonitoringClientErrorTO, True)

    @classmethod
    def create(cls, status):
        to = cls()
        to.error_count = status['errorCount']
        to.skipped_count = status['skippedCount']
        to.queues = [MonitoringQueueTO.from_model(k, status['queues'][k]) for k in status['queues']]
        to.five_min_ago = status['five_min_ago']
        to.client_errors = [MonitoringClientErrorTO.from_model(c) for c in status['client_errors']]
        return to
