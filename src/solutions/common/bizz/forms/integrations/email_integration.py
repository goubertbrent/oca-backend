# -*- coding: utf-8 -*-
# Copyright 2020 Green Valley NV
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
# @@license_version:1.5@@
import logging
from collections import defaultdict
from email.MIMEText import MIMEText
from email.mime.multipart import MIMEMultipart
from os.path import join

from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from webapp2 import RequestHandler

from rogerthat.bizz.communities.communities import get_community
from rogerthat.dal.app import get_app_by_id
from rogerthat.models import ServiceProfile, App, ServiceIdentity
from rogerthat.models.settings import ServiceInfo
from rogerthat.rpc import users
from rogerthat.service.api.system import get_identity
from rogerthat.settings import get_server_settings, ServerSettings
from rogerthat.to import TO
from rogerthat.to.forms import DynamicFormTO, SingleSelectComponentValueTO, SingleSelectComponentTO, ValueTO, \
    NextActionURLTO
from rogerthat.to.service import UserDetailsTO
from rogerthat.utils import send_mail_via_mime
from solutions import translate
from solutions.common.bizz.forms.integrations import BaseFormIntegration
from solutions.common.dal import get_solution_settings
from solutions.common.handlers import JINJA_COMPRESSED_ENVIRONMENT
from solutions.common.models.forms import FormSubmission, EmailIntegrationFormConfigTO
from solutions.common.to.forms import FormSubmissionTO


class EmailFormIntegrationConfiguration(TO):
    pass


def _convert_mapping(config):
    # type: (EmailIntegrationFormConfigTO) -> Dict[str, Dict[str, Dict[str, int]]]
    section_mapping = {}
    for mapping in config.mapping:
        if mapping.section_id not in section_mapping:
            section_mapping[mapping.section_id] = {}
        if mapping.component_id not in section_mapping[mapping.section_id]:
            section_mapping[mapping.section_id][mapping.component_id] = {}
        section_mapping[mapping.section_id][mapping.component_id][mapping.component_value] = mapping.group_id
    return section_mapping


def _get_group_id_from_mapping(section_mapping, form_submission):
    # type: (Dict[str, Dict[str, Dict[str, int]]], FormSubmissionTO) -> Optional[int]
    for section in form_submission.sections:
        for component in section.components:
            if isinstance(component, SingleSelectComponentValueTO):
                group_id = section_mapping.get(section.id, {}).get(component.id, {}).get(component.value)
                if group_id is not None:
                    return group_id
    return None


def _should_send_email(form, submission_to):
    single_select_value_mapping = defaultdict(dict)  # type: Dict[str, Dict[str, Dict[str, ValueTO]]]
    for section in form.sections:
        for component in section.components:
            if isinstance(component, SingleSelectComponentTO):
                choices_mapping = {choice.value: choice for choice in component.choices}
                single_select_value_mapping[section.id][component.id] = choices_mapping
    last_section = submission_to.sections[-1]
    for component in reversed(last_section.components):
        if isinstance(component, SingleSelectComponentValueTO):
            choice = single_select_value_mapping[last_section.id][component.id][component.value]
            if isinstance(choice.next_action, NextActionURLTO):
                return False
    return True


class EmailFormIntegration(BaseFormIntegration):

    def __init__(self, configuration):
        self.configuration = EmailFormIntegrationConfiguration.from_dict(configuration or {})
        super(EmailFormIntegration, self).__init__(self.configuration)

    def update_configuration(self, form_id, configuration, service_profile):
        # Nothing special needs to happen
        pass

    def submit(self, form_configuration, submission, form, service_profile, user_details):
        # type: (dict, FormSubmission, DynamicFormTO, ServiceProfile, UserDetailsTO) -> None
        config = EmailIntegrationFormConfigTO.from_dict(form_configuration)
        submission_to = FormSubmissionTO.from_model(submission)
        if not _should_send_email(form, submission_to):
            logging.debug('Not sending form submission email because last submitted component has a NextActionURLTO')
            return
        section_mapping = _convert_mapping(config)
        group_id = _get_group_id_from_mapping(section_mapping, submission_to)
        if group_id is None:
            if config.default_group:
                group_id = config.default_group
            else:
                logging.debug('Not sending form submission email: there is no default group id assigned')
                return
        for group in config.email_groups:
            if group.id == group_id:
                break
        logging.debug('Sending form submission email to group %s(%d)', group, group_id)
        reply_to_email = user_details.email
        _send_form_submission_email(group.emails, service_profile, form, submission_to, reply_to_email)
        return None


def _get_form_submission_email_html(settings, service_name, app, language, form, submission):
    # type: (ServerSettings, str, App, str, DynamicFormTO, FormSubmissionTO) -> str
    signin_url = settings.get_signin_url()
    dashboard_url = '<a href="%s">%s</a>' % (signin_url, translate(language, 'dashboard').lower())
    footer_html = translate(language, 'forms_email_submission_footer', form_name=form.title, service_name=service_name,
                            dashboard_url=dashboard_url)

    mapping = form.to_mapping()
    sections = []

    for section_value in submission.sections:
        section_mapping = mapping.get(section_value.id)
        section_dict = {'section': section_mapping.section, 'components': []}
        for component_value in section_value.components:
            if component_value.id in section_mapping.components:
                section_dict['components'].append({
                    'component': section_mapping.components[component_value.id],
                    'value': component_value,
                })
        if section_dict['components']:
            sections.append(section_dict)
    html_params = {
        'logo_url': settings.baseUrl + '/static/images/public/logo.png',
        'form_title': form.title,
        'language': language,
        'sections': sections,
        'footer': footer_html.replace('\n', '<br>'),
    }
    return JINJA_COMPRESSED_ENVIRONMENT.get_template(join('emails', 'form-submission.tmpl')).render(html_params)


def _send_form_submission_email(emails, service_profile, form, submission, reply_to_email):
    # type: (List[str], ServiceProfile, DynamicFormTO, FormSubmissionTO, str) -> None
    settings = get_server_settings()

    community = get_community(service_profile.community_id)
    service_info = ServiceInfo.create_key(service_profile.service_user, ServiceIdentity.DEFAULT).get()
    app = get_app_by_id(community.default_app)
    lang = get_solution_settings(service_profile.service_user).main_language

    mime_root = MIMEMultipart('related')
    mime_root['Subject'] = '%s - %s ' % (translate(lang, 'our-city-app').title(), form.title)
    mime_root['From'] = '%s <%s>' % (community.name, app.dashboard_email_address)
    mime_root['To'] = ', '.join(emails)
    mime_root['Reply-To'] = reply_to_email

    mime = MIMEMultipart('alternative')
    mime_root.attach(mime)

    html_body = _get_form_submission_email_html(settings, service_info.name, app, lang, form, submission)
    body = BeautifulSoup(html_body, features='lxml').get_text('\n')

    mime.attach(MIMEText(body.encode('utf-8'), 'plain', 'utf-8'))
    mime.attach(MIMEText(html_body.encode('utf-8'), 'html', 'utf-8'))

    send_mail_via_mime(settings.senderEmail, emails, mime_root)


class TestFormSubmissionEmailHandler(RequestHandler):
    def get(self, form_id, submission_id):
        from rogerthat.bizz.forms import get_form
        version = self.request.GET.get('version', 'html')
        form = get_form(long(form_id))
        form_to = DynamicFormTO.from_model(form)
        submission = FormSubmission.create_key(long(submission_id)).get()
        submission_to = FormSubmissionTO.from_model(submission)
        service_user = users.User(form.service)
        lang = get_solution_settings(service_user).main_language
        with users.set_user(service_user):
            si = get_identity()
        app = get_app_by_id(si.app_ids[0])
        server_settings = get_server_settings()
        html = _get_form_submission_email_html(server_settings, si.name, app, lang, form_to, submission_to)
        if version == 'text':
            text_version = BeautifulSoup(html, features='lxml').get_text('\n')
            self.response.out.write('<pre>%s</pre>' % text_version)
        else:
            self.response.out.write(html)
