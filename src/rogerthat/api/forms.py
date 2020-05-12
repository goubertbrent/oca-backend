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

from __future__ import unicode_literals

from mcfw.rpc import returns, arguments
from rogerthat.bizz.forms import get_form, submit_form, LocalizedSubmitFormException, SubmitFormException
from rogerthat.bizz.user import get_lang
from rogerthat.rpc import users
from rogerthat.rpc.rpc import expose
from rogerthat.to.forms.client import GetFormResponseTO, GetFormRequestTO, SubmitDynamicFormRequestTO, \
    SubmitDynamicFormResponseTO
from rogerthat.translations import localize


@expose(('api',))
@returns(GetFormResponseTO)
@arguments(request=GetFormRequestTO)
def getForm(request):
    # type: (GetFormRequestTO) -> GetFormResponseTO
    return GetFormResponseTO.from_model(get_form(request.id))


@expose(('api',))
@returns(SubmitDynamicFormResponseTO)
@arguments(request=SubmitDynamicFormRequestTO)
def submitForm(request):
    # type: (SubmitDynamicFormRequestTO) -> SubmitDynamicFormResponseTO
    app_user = users.get_current_user()
    try:
        submit_form(request, app_user)
        return SubmitDynamicFormResponseTO(success=True, errormsg=None)
    except LocalizedSubmitFormException as e:
        msg = localize(get_lang(app_user), e.reason, **e.fields)
        return SubmitDynamicFormResponseTO(success=False, errormsg=msg)
    except SubmitFormException as e:
        return SubmitDynamicFormResponseTO(success=False, errormsg=e.message)
