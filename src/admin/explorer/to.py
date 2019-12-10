# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
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

from mcfw.properties import long_property, unicode_property, bool_property, typed_property, float_property
from rogerthat.to import TO


class CreateScriptTO(TO):
    name = unicode_property('name')
    source = unicode_property('source')


class UpdateScriptTO(CreateScriptTO):
    id = long_property('id')
    version = long_property('version')


class RunScriptTO(TO):
    function = unicode_property('function')
    deferred = bool_property('deferred')


class RunResultTO(TO):
    result = unicode_property('result')
    succeeded = bool_property('succeeded')
    time = float_property('time')
    date = unicode_property('date')
    user = unicode_property('user')
    task_id = unicode_property('task_id')
    request_id = unicode_property('request_id')
    script = typed_property('script', dict)
    url = unicode_property('url')
