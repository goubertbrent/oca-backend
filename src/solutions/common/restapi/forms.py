# -*- coding: utf-8 -*-
# Copyright 2019 Mobicage NV
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
# @@license_version:1.4@@
from mcfw.consts import REST_TYPE_TO
from mcfw.exceptions import HttpBadRequestException
from mcfw.restapi import rest, GenericRESTRequestHandler
from mcfw.rpc import returns, arguments
from rogerthat.rpc import users
from rogerthat.rpc.service import ServiceApiException
from rogerthat.service.api.forms import service_api
from rogerthat.to.service import UserDetailsTO
from solutions.common.bizz.forms import create_form, get_form, update_form, get_tombola_winners, list_forms, \
    get_statistics, list_responses, delete_submissions, upload_form_image, delete_form, delete_submission
from solutions.common.to.forms import OcaFormTO, FormSettingsTO, FormStatisticsTO, FormSubmissionListTO, \
    FormSubmissionTO, FormImageTO


@rest('/common/forms', 'get', read_only_access=True, silent_result=True)
@returns([FormSettingsTO])
@arguments()
def rest_list_forms():
    return [FormSettingsTO.from_model(form) for form in list_forms(users.get_current_user())]


@rest('/common/forms/<form_id:[^/]+>', 'get', read_only_access=True, silent_result=True)
@returns(OcaFormTO)
@arguments(form_id=(int, long))
def rest_get_form(form_id):
    return get_form(form_id, users.get_current_user())


@rest('/common/forms', 'post', type=REST_TYPE_TO, silent_result=True)
@returns(OcaFormTO)
@arguments(data=OcaFormTO)
def rest_create_form(data):
    try:
        return create_form(data, users.get_current_user())
    except ServiceApiException as e:
        raise HttpBadRequestException(e.message, e.fields)


@rest('/common/forms/<form_id:[^/]+>', 'put', type=REST_TYPE_TO, silent_result=True)
@returns(OcaFormTO)
@arguments(form_id=(int, long), data=OcaFormTO)
def rest_put_form(form_id, data):
    try:
        return update_form(form_id, data, users.get_current_user())
    except ServiceApiException as e:
        raise HttpBadRequestException(e.message, e.fields)


@rest('/common/forms/<form_id:[^/]+>', 'delete', silent_result=True)
@returns()
@arguments(form_id=(int, long))
def rest_delete_form(form_id):
    try:
        return delete_form(form_id, users.get_current_user())
    except ServiceApiException as e:
        raise HttpBadRequestException(e.message, e.fields)


@rest('/common/forms/<form_id:[^/]+>/submissions', 'get', read_only_access=True, silent_result=True)
@returns(FormSubmissionListTO)
@arguments(form_id=(int, long), cursor=unicode, page_size=int)
def rest_list_responses(form_id, cursor=None, page_size=50):
    service_user = users.get_current_user()
    responses, cursor, more = list_responses(service_user, form_id, cursor, page_size)
    return FormSubmissionListTO(cursor=cursor and cursor.to_websafe_string(),
                                more=more,
                                results=[FormSubmissionTO.from_dict(model.to_dict()) for model in responses])


@rest('/common/forms/<form_id:[^/]+>/submissions/<submission_id:[^/]+>', 'delete')
@returns()
@arguments(form_id=(int, long), submission_id=(int, long))
def rest_delete_submission(form_id, submission_id):
    delete_submission(users.get_current_user(), form_id, submission_id)


@rest('/common/forms/<form_id:[^/]+>/submissions', 'delete')
@returns()
@arguments(form_id=(int, long))
def rest_delete_submissions(form_id):
    return delete_submissions(users.get_current_user(), form_id)


@rest('/common/forms/<form_id:[^/]+>/statistics', 'get', read_only_access=True, silent_result=True)
@returns(FormStatisticsTO)
@arguments(form_id=(int, long))
def rest_get_form_statistics(form_id):
    service_user = users.get_current_user()
    return get_statistics(service_user, form_id)


@rest('/common/forms/<form_id:[^/]+>/test', 'post', read_only_access=True, silent_result=True)
@returns()
@arguments(form_id=(int, long), testers=[unicode])
def rest_test_form(form_id, testers):
    return service_api.test_form(form_id, testers)


@rest('/common/forms/<form_id:[^/]+>/tombola/winners', 'get', read_only_access=True, silent_result=True)
@returns([UserDetailsTO])
@arguments(form_id=(int, long))
def rest_get_tombola_winners(form_id):
    return get_tombola_winners(form_id)


@rest('/common/forms/<form_id:[^/]+>/image', 'post')
@returns(FormImageTO)
@arguments(form_id=(int, long))
def rest_upload_form_image(form_id):
    request = GenericRESTRequestHandler.getCurrentRequest()
    uploaded_file = request.POST.get('file')
    result = upload_form_image(users.get_current_user(), form_id, uploaded_file)
    return FormImageTO.from_dict(result.to_dict(extra_properties=['url']))
