# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
# NOTICE: THIS FILE HAS BEEN MODIFIED BY GREEN VALLEY BELGIUM NV IN ACCORDANCE WITH THE APACHE LICENSE VERSION 2.0
# Copyright 2018 GIG Technology NV
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

from mcfw.rpc import returns, arguments
from rogerthat.models import ServiceProfile
from rogerthat.rpc.models import ServiceAPICallback
from rogerthat.rpc.rpc import mapping
from rogerthat.rpc.service import service_api_callback
from rogerthat.to.forms import FormSubmittedCallbackResultTO, SubmitDynamicFormRequestTO
from rogerthat.to.service import UserDetailsTO


@service_api_callback(function='forms.submitted', code=ServiceProfile.CALLBACK_FORM_SUBMITTED)
@returns(FormSubmittedCallbackResultTO)
@arguments(form=SubmitDynamicFormRequestTO, user_details=[UserDetailsTO])
def form_submitted(form, user_details):
    # type: (SubmitDynamicFormRequestTO, list[UserDetailsTO]) -> FormSubmittedCallbackResultTO
    pass


@mapping('forms.form_submitted.response_handler')
@returns()
@arguments(context=ServiceAPICallback, result=FormSubmittedCallbackResultTO)
def form_submitted_response_handler(context, result):
    pass
