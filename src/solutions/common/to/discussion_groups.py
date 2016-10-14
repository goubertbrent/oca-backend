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

from mcfw.properties import unicode_property, long_property


class DiscussionGroupTO(object):
    id = long_property('1')
    topic = unicode_property('2')
    description = unicode_property('3')
    message_key = unicode_property('4')
    creation_timestamp = long_property('5')

    @classmethod
    def from_model(cls, model):
        to = cls()
        for prop in dir(DiscussionGroupTO):
            if not prop.startswith('__') and not callable(getattr(DiscussionGroupTO, prop)):
                setattr(to, prop, getattr(model, prop))
        return to
