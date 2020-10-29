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

from mcfw.properties import unicode_property, long_property
from rogerthat.to import TO
from solutions.common.models.discussion_groups import DiscussionGroup


class DiscussionGroupTO(TO):
    id = long_property('1')
    topic = unicode_property('2')
    description = unicode_property('3')
    message_key = unicode_property('4')
    creation_timestamp = long_property('5')

    @classmethod
    def from_model(cls, model):
        # type: (DiscussionGroup) -> DiscussionGroupTO
        return cls(**model.to_dict(include=['id', 'topic', 'description', 'message_key', 'creation_timestamp']))
