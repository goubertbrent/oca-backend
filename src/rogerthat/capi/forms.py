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

from mcfw.rpc import returns, arguments
from rogerthat.rpc.models import RpcCAPICall
from rogerthat.rpc.rpc import capi, mapping
from rogerthat.to.forms import TestFormRequestTO, TestFormResponseTO


@capi('com.mobicage.capi.forms.testForm')
@returns(TestFormResponseTO)
@arguments(request=TestFormRequestTO)
def testForm(request):
    pass


@mapping('com.mobicage.capi.forms.test_form_response_handler')
@returns()
@arguments(context=RpcCAPICall, result=TestFormResponseTO)
def test_form_response_handler(context, result):
    pass
