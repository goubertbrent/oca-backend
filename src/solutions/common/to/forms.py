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
from mcfw.properties import bool_property, unicode_property, typed_property, long_property
from rogerthat.to import TO, PaginatedResultTO
from rogerthat.to.forms import DynamicFormTO, FormSectionValueTO
from solutions.common.models.forms import OcaForm


class FormTombolaTO(TO):
    winner_message = unicode_property('winner_message')
    winner_count = long_property('winner_count', default=1)


class CompletedFormStepTO(TO):
    step_id = unicode_property('step_id')


class FormSettingsTO(TO):
    id = long_property('id')
    title = unicode_property('title')
    icon = unicode_property('icon', default=OcaForm.icon._default)
    visible = bool_property('visible')
    visible_until = unicode_property('visible_until')
    tombola = typed_property('tombola', FormTombolaTO)
    finished = bool_property('finished')
    steps = typed_property('steps', CompletedFormStepTO, True)

    @classmethod
    def from_model(cls, oca_form):
        return cls.from_dict(oca_form.to_dict())


class OcaFormTO(TO):
    form = typed_property('form', DynamicFormTO)  # type: DynamicFormTO
    settings = typed_property('settings', FormSettingsTO)  # type: FormSettingsTO


class FormSubmissionTO(TO):
    id = long_property('id')
    sections = typed_property('sections', FormSectionValueTO, True)
    submitted_date = unicode_property('submitted_date')
    version = long_property('version')


class FormSubmissionListTO(PaginatedResultTO):
    results = typed_property('results', FormSubmissionTO, True)


class FormStatisticsTO(TO):
    submissions = long_property('submissions')
    statistics = typed_property('statistics', dict)


class FormImageTO(TO):
    id = long_property('id')
    form_id = long_property('form_id')
    content_type = unicode_property('content_type')
    size = long_property('size')
    url = unicode_property('url')


class GcsFileTO(TO):
    url = unicode_property('url')
    content_type = unicode_property('content_type')
    size = long_property('size')
