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

from collections import defaultdict

from google.appengine.ext.deferred import deferred

import cloudstorage
import xlwt
from rogerthat.bizz.gcs import get_serving_url
from rogerthat.consts import DAY, SCHEDULED_QUEUE
from rogerthat.rpc import users
from rogerthat.service.api.forms import service_api
from rogerthat.to.forms import FormSectionValueTO, FieldComponentTO, DatetimeComponentValueTO, FormSectionTO, \
    DynamicFormTO
from rogerthat.utils.app import get_human_user_from_app_user
from solutions import translate
from solutions.common.consts import OCA_FILES_BUCKET
from solutions.common.dal import get_solution_settings
from solutions.common.models.forms import FormSubmission, OcaForm
from xlwt import XFStyle


def _delete_file(path):
    try:
        cloudstorage.delete(path)
    except cloudstorage.NotFoundError:
        pass


def export_submissions(service_user, form_id):
    # type: (users.User, int) -> str
    with users.set_user(service_user):
        form = service_api.get_form(form_id)
    submissions = FormSubmission.list(form_id)
    language = get_solution_settings(service_user).main_language
    oca_form = OcaForm.create_key(form.id, service_user).get()  # type: OcaForm
    extension = 'xlsx'
    content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    path = '/%s/tmp/forms/%d/exports/%s.%s' % (OCA_FILES_BUCKET, form.id, form.title, extension)
    with cloudstorage.open(path, 'w', content_type=content_type) as f:
        _export_to_xlsx(form, oca_form, language, submissions, f)
    deferred.defer(_delete_file, path, _countdown=DAY, _queue=SCHEDULED_QUEUE)
    return get_serving_url(path)


def _export_to_xlsx(form, oca_form, language, submissions, file_handle):
    # type: (DynamicFormTO, OcaForm, str, list[FormSubmission], file) -> object
    book = xlwt.Workbook(encoding="utf-8")
    # Write headers
    component_mapping = defaultdict(dict)
    sheet = book.add_sheet(form.title)  # type: xlwt.Worksheet
    row = 0
    column = 0
    sheet.write(row, column, translate(language, 'User'))
    column += 1
    sheet.write(row, column, translate(language, 'Date'))
    column += 1
    form_mapping = form.to_mapping()
    if oca_form.has_integration:
        sheet.write(row, column, translate(language, 'oca.external_reference'))
        column += 1
    for section in form.sections:  # type: FormSectionTO
        for component in section.components:  # type: ParagraphComponentTO
            if isinstance(component, FieldComponentTO):
                sheet.write(row, column, component.title)
                component_mapping[section.id][component.id] = column
                column += 1
    row += 1
    date_format = XFStyle()
    date_format.num_format_str = 'dd/MM/yyyy HH:mm'

    for submission in submissions:
        column = 0
        sheet.write(row, column, get_human_user_from_app_user(users.User(submission.user)).email())
        column += 1
        sheet.write(row, column, submission.submitted_date, date_format)
        column += 1
        if oca_form.has_integration:
            sheet.write(row, column, submission.external_reference)
            column += 1
        section_values = FormSectionValueTO.from_list(submission.sections)
        for section_value in section_values:
            if section_value.id in component_mapping:
                for component_value in section_value.components:
                    if component_value.id in component_mapping[section_value.id]:
                        column = component_mapping[section_value.id][component_value.id]
                        component = form_mapping.get(section_value.id, {}).get(component_value.id)
                        if isinstance(component_value, DatetimeComponentValueTO):
                            sheet.write(row, column, component_value.get_date(), date_format)
                        else:
                            sheet.write(row, column, component_value.get_string_value(component))
        row += 1
    book.save(file_handle)
