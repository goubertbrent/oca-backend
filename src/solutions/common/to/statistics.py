# -*- coding: utf-8 -*-
# Copyright 2016 Mobicage NV
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
# @@license_version:1.1@@

from mcfw.properties import typed_property, unicode_list_property, bool_property
from rogerthat.to.statistics import FlowStatisticsListResultTO, ServiceIdentityStatisticsTO


class StatisticsResultTO(object):
    service_identity_statistics = typed_property('1', ServiceIdentityStatisticsTO, False)
    has_app_broadcasts = bool_property('2')


class AppBroadcastStatisticsTO(object):
    flow_statistics = typed_property('1', FlowStatisticsListResultTO, False)
    messages = unicode_list_property('2')

    def __init__(self, flow_statistics=None, messages=None):
        if messages is None:
            messages = []
        self.flow_statistics = flow_statistics
        self.messages = messages
