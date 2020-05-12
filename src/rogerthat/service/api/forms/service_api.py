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
from rogerthat.bizz import forms
from rogerthat.rpc import users
from rogerthat.rpc.service import service_api
from rogerthat.to.forms import FormSectionTO, DynamicFormTO


@service_api(function='forms.create', silent=True, silent_result=True)
@returns(DynamicFormTO)
@arguments(title=unicode, sections=[FormSectionTO], submission_section=FormSectionTO,
           max_submissions=(int, long))
def create_form(title, sections, submission_section=None, max_submissions=0):
    service_user = users.get_current_user()
    form = DynamicFormTO(title=title, sections=sections, submission_section=submission_section,
                         max_submissions=max_submissions)
    return DynamicFormTO.from_model(forms.create_form(service_user, form))


@service_api(function='forms.update', silent=True, silent_result=True)
@returns(DynamicFormTO)
@arguments(id=(int, long), title=unicode, sections=[FormSectionTO], submission_section=FormSectionTO,
           max_submissions=(int, long))
def update_form(id, title, sections, submission_section=None, max_submissions=0):  # @ReservedAssignment
    service_user = users.get_current_user()
    form = DynamicFormTO(id=id, title=title, sections=sections, submission_section=submission_section,
                         max_submissions=max_submissions)
    return DynamicFormTO.from_model(forms.update_form(service_user, form))


@service_api(function='forms.delete')
@returns()
@arguments(id=(int, long))
def delete_form(id):  # @ReservedAssignment
    service_user = users.get_current_user()
    forms.delete_form(service_user, id)


@service_api(function='forms.delete_submission')
@returns()
@arguments(form_id=(int, long), app_user=unicode)
def delete_form_submission(form_id, app_user):
    forms.delete_form_submission(users.get_current_user(), form_id, users.User(app_user))


@service_api(function='forms.delete_submissions')
@returns()
@arguments(id=(int, long))
def delete_form_submissions(id):  # @ReservedAssignment
    service_user = users.get_current_user()
    forms.delete_form_submissions(service_user, id)


@service_api(function='forms.get', cache_result=False, silent_result=True)
@returns(DynamicFormTO)
@arguments(id=(int, long))
def get_form(id):  # @ReservedAssignment
    service_user = users.get_current_user()
    return DynamicFormTO.from_model(forms.get_form(id, service_user))


@service_api(function='forms.list', cache_result=False, silent_result=True)
@returns([DynamicFormTO])
@arguments()
def list_forms():
    return [DynamicFormTO.from_model(form) for form in forms.list_forms(users.get_current_user())]


@service_api(function='forms.test', cache_result=False)
@returns()
@arguments(form_id=(int, long), testers=[unicode])
def test_form(form_id, testers):
    service_user = users.get_current_user()
    return forms.test_form(service_user, form_id, map(users.User, testers))
