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

from mcfw.consts import REST_TYPE_TO
from mcfw.exceptions import HttpBadRequestException, HttpForbiddenException
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.dal.profile import get_service_profile
from rogerthat.rpc import users
from rogerthat.rpc.service import ServiceApiException
from rogerthat.rpc.users import get_current_session
from rogerthat.service.api.forms import service_api
from rogerthat.to.service import UserDetailsTO
from solutions.common.bizz.forms import create_form, get_form, update_form, get_tombola_winners, list_forms, \
    get_statistics, list_responses, delete_submissions, delete_form, delete_submission, \
    get_form_integrations, update_form_integration, get_form_integration
from solutions.common.bizz.forms.export import export_submissions
from solutions.common.bizz.forms.integrations import TOPDeskFormIntegration
from solutions.common.models.forms import FormIntegrationProvider, FormIntegrationConfiguration
from solutions.common.to.forms import OcaFormTO, FormSettingsTO, FormStatisticsTO, FormSubmissionListTO, \
    FormSubmissionTO


def can_edit_integration_config():
    from google.appengine.api import users as gusers
    return gusers.is_current_user_admin() or get_current_session().shop


@rest('/common/forms', 'get', read_only_access=True, silent_result=True)
@returns([FormSettingsTO])
@arguments()
def rest_list_forms():
    return [FormSettingsTO.from_model(form) for form in list_forms(users.get_current_user())]


@rest('/common/forms/integrations', 'get')
@returns([dict])
@arguments()
def rest_get_integrations():
    results = []
    can_edit = can_edit_integration_config()
    for integration in get_form_integrations(users.get_current_user()):
        d = integration.to_dict()
        d['can_edit'] = can_edit or integration.provider == FormIntegrationProvider.EMAIL
        results.append(d)
    return results


@rest('/common/forms/integrations/<provider:[^/]+>', 'put', type=REST_TYPE_TO)
@returns(dict)
@arguments(provider=unicode, data=dict)
def rest_update_integration(provider, data):
    if not can_edit_integration_config() and provider != FormIntegrationProvider.EMAIL:
        raise HttpForbiddenException()
    return update_form_integration(users.get_current_user(), provider, data).to_dict()


@rest('/common/forms/<form_id:\d+>', 'get', read_only_access=True, silent_result=True)
@returns(OcaFormTO)
@arguments(form_id=(int, long))
def rest_get_form(form_id):
    return get_form(form_id, users.get_current_user())


@rest('/common/forms', 'post', type=REST_TYPE_TO, silent=True, silent_result=True)
@returns(OcaFormTO)
@arguments(data=OcaFormTO)
def rest_create_form(data):
    try:
        return create_form(data, users.get_current_user())
    except ServiceApiException as e:
        raise HttpBadRequestException(e.message, e.fields)


@rest('/common/forms/<form_id:\d+>', 'put', type=REST_TYPE_TO, silent=True, silent_result=True)
@returns(OcaFormTO)
@arguments(form_id=(int, long), data=OcaFormTO)
def rest_put_form(form_id, data):
    try:
        return update_form(form_id, data, users.get_current_user())
    except ServiceApiException as e:
        raise HttpBadRequestException(e.message, e.fields)


@rest('/common/forms/<form_id:\d+>', 'delete', silent_result=True)
@returns()
@arguments(form_id=(int, long))
def rest_delete_form(form_id):
    try:
        return delete_form(form_id, users.get_current_user())
    except ServiceApiException as e:
        raise HttpBadRequestException(e.message, e.fields)


@rest('/common/forms/<form_id:\d+>/submissions', 'get', read_only_access=True, silent_result=True)
@returns(FormSubmissionListTO)
@arguments(form_id=(int, long), cursor=unicode, page_size=int)
def rest_list_responses(form_id, cursor=None, page_size=50):
    service_user = users.get_current_user()
    responses, cursor, more = list_responses(service_user, form_id, cursor, page_size)
    return FormSubmissionListTO(cursor=cursor and cursor.to_websafe_string(),
                                more=more,
                                results=[FormSubmissionTO.from_model(model) for model in responses])


@rest('/common/forms/<form_id:\d+>/submissions/<submission_id:[^/]+>', 'delete')
@returns()
@arguments(form_id=(int, long), submission_id=(int, long))
def rest_delete_submission(form_id, submission_id):
    delete_submission(users.get_current_user(), form_id, submission_id)


@rest('/common/forms/<form_id:\d+>/submissions', 'delete')
@returns()
@arguments(form_id=(int, long))
def rest_delete_submissions(form_id):
    return delete_submissions(users.get_current_user(), form_id)


@rest('/common/forms/<form_id:\d+>/statistics', 'get', read_only_access=True, silent_result=True)
@returns(FormStatisticsTO)
@arguments(form_id=(int, long))
def rest_get_form_statistics(form_id):
    service_user = users.get_current_user()
    return get_statistics(service_user, form_id)


@rest('/common/forms/<form_id:\d+>/test', 'post', read_only_access=True, silent_result=True)
@returns()
@arguments(form_id=(int, long), testers=[unicode])
def rest_test_form(form_id, testers):
    return service_api.test_form(form_id, testers)


@rest('/common/forms/<form_id:\d+>/tombola/winners', 'get', read_only_access=True, silent_result=True)
@returns([UserDetailsTO])
@arguments(form_id=(int, long))
def rest_get_tombola_winners(form_id):
    return get_tombola_winners(form_id)


@rest('/common/forms/<form_id:\d+>/export', 'get', read_only_access=True, silent_result=True)
@returns(dict)
@arguments(form_id=(int, long))
def rest_export_form_submissions(form_id):
    return {'url': export_submissions(users.get_current_user(), form_id)}


@rest('/common/forms/integrations/topdesk/categories', 'get', type=REST_TYPE_TO, silent=True, silent_result=True)
@returns([dict])
@arguments()
def rest_get_topdesk_categories():
    service_user = users.get_current_user()
    config = FormIntegrationConfiguration.create_key(service_user,FormIntegrationProvider.TOPDESK).get()
    integration = get_form_integration(FormIntegrationProvider.TOPDESK, config)
    assert isinstance(integration, TOPDeskFormIntegration)
    return integration.get_categories(get_service_profile(service_user))


@rest('/common/forms/integrations/topdesk/subcategories', 'get', type=REST_TYPE_TO, silent=True, silent_result=True)
@returns([dict])
@arguments()
def rest_get_topdesk_subcategories():
    service_user = users.get_current_user()
    config = FormIntegrationConfiguration.create_key(service_user, FormIntegrationProvider.TOPDESK).get()
    integration = get_form_integration(FormIntegrationProvider.TOPDESK, config)
    assert isinstance(integration, TOPDeskFormIntegration)
    return integration.get_subcategories(get_service_profile(service_user))
