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

from mcfw.properties import long_property, bool_property
from rogerthat.to import TO, ReturnStatusTO
from .form import DynamicFormTO, DynamicFormValueTO


class GetFormRequestTO(TO):
    id = long_property('id')


class GetFormResponseTO(DynamicFormTO):
    pass


class SubmitDynamicFormRequestTO(DynamicFormValueTO):
    test = bool_property('test', default=False)


class SubmitDynamicFormResponseTO(ReturnStatusTO):
    pass


class TestFormRequestTO(TO):
    id = long_property('id')
    version = long_property('version')


class TestFormResponseTO(TO):
    pass
