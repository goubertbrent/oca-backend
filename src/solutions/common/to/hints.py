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

from mcfw.properties import long_property, unicode_property, unicode_list_property
from rogerthat.to import TO


class SolutionHintTO(TO):
    tag = unicode_property('1')
    language = unicode_property('2')
    id = long_property('3')
    text = unicode_property('4')
    modules = unicode_list_property('5')

    @staticmethod
    def fromModel(model):
        to = SolutionHintTO()
        to.tag = model.tag
        to.language = model.language
        to.id = model.id
        to.text = model.text
        to.modules = model.modules
        return to
