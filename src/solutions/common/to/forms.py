# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
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

from mcfw.properties import bool_property, unicode_property, typed_property, long_property
from rogerthat.to import TO, PaginatedResultTO
from rogerthat.to.forms import DynamicFormTO, FormSectionValueTO
from solutions.common.bizz.forms import get_form_integration
from solutions.common.bizz.forms.integrations import GreenValleyFormIntegration
from solutions.common.models.forms import OcaForm, FormSubmission, FormIntegrationConfiguration


class FormTombolaTO(TO):
    winner_message = unicode_property('winner_message')
    winner_count = long_property('winner_count', default=1)


class CompletedFormStepTO(TO):
    step_id = unicode_property('step_id')


class FormIntegrationTO(TO):
    provider = unicode_property('provider')
    enabled = bool_property('enabled', default=True)
    configuration = typed_property('configuration', dict)


class FormSettingsTO(TO):
    id = long_property('id')
    title = unicode_property('title')
    icon = unicode_property('icon', default=OcaForm.icon._default)
    visible = bool_property('visible')
    visible_until = unicode_property('visible_until')
    tombola = typed_property('tombola', FormTombolaTO)
    finished = bool_property('finished')
    steps = typed_property('steps', CompletedFormStepTO, True)
    readonly_ids = bool_property('readonly_ids', default=OcaForm.readonly_ids._default)
    integrations = typed_property('integrations', FormIntegrationTO, True, default=[])

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
    external_reference = typed_property('external_reference', dict)

    @classmethod
    def from_model(cls, model, integration_config=None):
        # type: (FormSubmission, FormIntegrationConfiguration) -> FormSubmissionTO
        d = model.to_dict(exclude=['external_reference'])
        if model.external_reference:
            integration = get_form_integration(integration_config)
            if isinstance(integration, GreenValleyFormIntegration):
                d['external_reference'] = {
                    'id': model.external_reference,
                    'url': '%s/do/overview' % integration.configuration.base_url,
                }
        return cls.from_dict(d)


class FormSubmissionListTO(PaginatedResultTO):
    results = typed_property('results', FormSubmissionTO, True)


class FormStatisticsTO(TO):
    submissions = long_property('submissions')
    statistics = typed_property('statistics', dict)


class GcsFileTO(TO):
    url = unicode_property('url')
    content_type = unicode_property('content_type')
    size = long_property('size')
