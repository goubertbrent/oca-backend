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
from typing import List

from mcfw.properties import bool_property, unicode_property, typed_property, long_property
from rogerthat.to import TO, PaginatedResultTO
from rogerthat.to.forms import DynamicFormTO, FormSectionValueTO
from solutions.common.models.forms import OcaForm


class FormTombolaTO(TO):
    winner_message = unicode_property('winner_message')
    winner_count = long_property('winner_count', default=1)


class CompletedFormStepTO(TO):
    step_id = unicode_property('step_id')


class FormIntegrationTO(TO):
    provider = unicode_property('provider')
    enabled = bool_property('enabled', default=True)
    visible = bool_property('visible', default=True)
    configuration = typed_property('configuration', dict)


class FormSettingsTO(TO):
    id = long_property('id')
    title = unicode_property('title')
    icon = unicode_property('icon', default=OcaForm.icon._default)
    visible = bool_property('visible', default=False)
    visible_until = unicode_property('visible_until', default=None)
    tombola = typed_property('tombola', FormTombolaTO, default=None)
    finished = bool_property('finished')
    steps = typed_property('steps', CompletedFormStepTO, True)
    integrations = typed_property('integrations', FormIntegrationTO, True, default=[])  # type: List[FormIntegrationTO]

    @classmethod
    def from_model(cls, oca_form, can_edit_integrations):
        to = cls.from_dict(oca_form.to_dict())
        for integration in to.integrations:
            integration.visible = can_edit_integrations
            if not integration.visible:
                integration.configuration = {}
        return to


class OcaFormTO(TO):
    form = typed_property('form', DynamicFormTO)  # type: DynamicFormTO
    settings = typed_property('settings', FormSettingsTO)  # type: FormSettingsTO


class FormSubmissionTO(TO):
    id = long_property('id')
    sections = typed_property('sections', FormSectionValueTO, True)  # type: List[FormSectionValueTO]
    submitted_date = unicode_property('submitted_date')
    version = long_property('version')
    external_reference = unicode_property('external_reference')


class FormSubmissionListTO(PaginatedResultTO):
    results = typed_property('results', FormSubmissionTO, True)


class FormStatisticsTO(TO):
    submissions = long_property('submissions')
    statistics = typed_property('statistics', dict)


class GcsFileTO(TO):
    url = unicode_property('url')
    content_type = unicode_property('content_type')
    size = long_property('size')
