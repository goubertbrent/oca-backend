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

from mcfw.properties import unicode_property, long_property, typed_property, bool_property
from solutions.djmatic.models import DjMaticProfile


class DjmaticStatusHistoryTO(object):
    status = long_property('1')
    status_str = unicode_property('2')
    epoch = long_property('3')

    @staticmethod
    def fromDjmaticStatusHistoryTOObject(status, epoch):
        item = DjmaticStatusHistoryTO()
        item.status = status
        item.status_str = DjMaticProfile.status_string(status)
        item.epoch = epoch
        return item

class DjmaticProfileTO(object):
    player_id = unicode_property('0')
    status = long_property('1')
    history = typed_property('2', DjmaticStatusHistoryTO, True)
    type = unicode_property('3')
    connected_users = long_property('4')
    name = unicode_property('5')
    days_date = unicode_property('6')
    days = long_property('7')

    @staticmethod
    def fromDjmaticProfile(obj):
        dp = DjmaticProfileTO()
        dp.player_id = obj.player_id
        dp.status = int(obj.status)
        dp.history = list()
        for i in xrange(len(obj.status_history)):
            status = obj.status_history[i]
            epoch = obj.status_history_epoch[i]
            dp.history.append(DjmaticStatusHistoryTO.fromDjmaticStatusHistoryTOObject(status, epoch))
        dp.type = unicode(obj.type)
        dp.connected_users = obj.connected_users
        dp.name = obj.name
        dp.days_date = unicode(obj.days_date)
        dp.days = obj.days
        return dp

class DjmaticTrialsTO(object):
    cursor = unicode_property('1')
    has_more = bool_property('2')
    djmatic_profiles = typed_property('3', DjmaticProfileTO, True)
