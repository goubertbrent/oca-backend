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

from google.appengine.api import urlfetch

from mcfw.properties import unicode_property, typed_property, long_property, object_factory
from mcfw.utils import Enum
from rogerthat.bizz.maps.reports import _do_request
from rogerthat.models import ServiceProfile
from rogerthat.to import TO
from rogerthat.to.forms import DynamicFormTO, FormSectionTO, SingleSelectComponentTO, RequiredValidatorTO, ValueTO, \
    NextActionSectionTO, TextInputComponentTO, KeyboardType, MaxLengthValidatorTO, LocationComponentTO, \
    FormComponentType, FileComponentTO
from solutions import translate
from solutions.common.bizz.forms.integrations.base import BaseFormIntegration
from solutions.common.models.forms import FormIntegrationProvider
from solutions.common.to.forms import FormSubmissionTO, OcaFormTO, FormSettingsTO, FormIntegrationTO, \
    CompletedFormStepTO


class TOPDeskConfiguration(TO):
    pass


class TopdeskPropertyName(Enum):
    BRIEF_DESCRIPTION = 'briefDescription'
    REQUEST = 'request'
    CALL_TYPE = 'callType'
    CATEGORY = 'category'
    SUB_CATEGORY = 'subcategory'
    BRANCH = 'branch'
    ENTRY_TYPE = 'entryType'
    LOCATION = 'location'
    OPERATOR = 'operator'
    OPERATOR_GROUP = 'operatorGroup'
    OPTIONAL_FIELDS_1 = 'optionalFields1'
    OPTIONAL_FIELDS_2 = 'optionalFields2'


class BaseComponent(TO):
    id = unicode_property('id')


class TOPDeskCategoryMapping(BaseComponent):
    type = unicode_property('type', default=TopdeskPropertyName.CATEGORY)
    categories = typed_property('categories', dict)  # mapping from component id -> topdesk category


class TOPDeskSubCategoryMapping(BaseComponent):
    type = unicode_property('type', default=TopdeskPropertyName.SUB_CATEGORY)
    subcategories = typed_property('subcategories', dict)  # mapping from component id -> topdesk subcategory


class TOPDeskBriefDescriptionMapping(BaseComponent):
    type = unicode_property('type', default=TopdeskPropertyName.BRIEF_DESCRIPTION)
    # No special options for now


class OptionalFieldLocationFormat(Enum):
    LATITUDE = 0  # only latitude
    LONGITUDE = 1  # only longitude
    LATITUDE_LONGITUDE = 2  # comma separated


class OptionalFieldLocationOptions(TO):
    type = unicode_property('type', default=FormComponentType.LOCATION)
    format = long_property('format')  # see OptionalFieldLocationFormat


OPTIONAL_FIELDS_OPTIONS = {
    FormComponentType.LOCATION: OptionalFieldLocationOptions,
}


class OptionalFieldsOptions(object_factory):

    def __init__(self):
        super(OptionalFieldsOptions, self).__init__('type', OPTIONAL_FIELDS_OPTIONS)


class OptionalFieldsMapping(BaseComponent):
    field = unicode_property('field')  # text1, number2, date5 etc
    # Options depend on the component type of the field.
    options = typed_property('options', OptionalFieldsOptions())


class TOPDeskOptionalFields1Mapping(OptionalFieldsMapping):
    type = unicode_property('type', default=TopdeskPropertyName.OPTIONAL_FIELDS_1)


class TOPDeskOptionalFields2Mapping(OptionalFieldsMapping):
    type = unicode_property('type', default=TopdeskPropertyName.OPTIONAL_FIELDS_1)


COMP_MAPPING = {
    TopdeskPropertyName.CATEGORY: TOPDeskCategoryMapping,
    TopdeskPropertyName.SUB_CATEGORY: TOPDeskSubCategoryMapping,
    TopdeskPropertyName.BRIEF_DESCRIPTION: TOPDeskBriefDescriptionMapping,
    TopdeskPropertyName.OPTIONAL_FIELDS_1: TOPDeskOptionalFields1Mapping,
    TopdeskPropertyName.OPTIONAL_FIELDS_2: TOPDeskOptionalFields2Mapping,
}


class TOPDeskComponentMapping(object_factory):
    type = unicode_property('type')

    def __init__(self):
        super(TOPDeskComponentMapping, self).__init__('type', COMP_MAPPING)


class TOPDeskSectionMapping(TO):
    id = unicode_property('id')
    components = typed_property('component', TOPDeskComponentMapping(), True)  # type: List[TOPDeskComponentMapping]


class TOPDeskFormConfiguration(TO):
    provider = unicode_property('provider', default=FormIntegrationProvider.TOPDESK)
    mapping = typed_property('mapping', TOPDeskSectionMapping, True)  # type: List[TOPDeskSectionMapping]


class TOPDeskFormIntegration(BaseFormIntegration):

    def __init__(self, configuration):
        self.configuration = TOPDeskConfiguration.from_dict(configuration)
        super(TOPDeskFormIntegration, self).__init__(self.configuration)

    def update_configuration(self, form_id, configuration, service_profile):
        configuration['provider'] = FormIntegrationProvider.TOPDESK
        payload = {'form_id': form_id, 'config': configuration}
        return _do_request('/incidents/integrations/form', urlfetch.PUT, payload, authorization=service_profile.sik)

    def get_categories(self, service_profile):
        return _do_request('/integrations/topdesk/categories', urlfetch.GET, authorization=service_profile.sik)

    def get_subcategories(self, service_profile):
        return _do_request('/integrations/topdesk/subcategories', urlfetch.GET, authorization=service_profile.sik)

    def create_standard_form(self, service_profile):
        # type: (ServiceProfile) -> OcaFormTO
        subcategories = self.get_subcategories(service_profile)
        oca_form = OcaFormTO()
        form = DynamicFormTO()
        # TODO translations
        form.title = 'Meldingskaart'
        sections = [
            FormSectionTO(
                id='choose_category',
                title='Meldingskaart',
                components=[
                    SingleSelectComponentTO(
                        id='category',
                        title='Wat is de categorie van uw melding?',
                        choices=[ValueTO(value=category['id'],
                                         label=category['name'],
                                         next_action=NextActionSectionTO(section='category_' + category['id']))
                                 for category in subcategories],
                        validators=[RequiredValidatorTO()]
                    )
                ])
        ]
        details_section_id = 'details'
        for category in subcategories:
            category_section = FormSectionTO(
                id='category_' + category['id'],
                title=category['name'],
                components=[
                    SingleSelectComponentTO(
                        id='subcategory',
                        title='Selecteer de optie die het best overeen komt met uw melding.',
                        choices=[ValueTO(value=subcategory['id'],
                                         label=subcategory['name'],
                                         next_action=NextActionSectionTO(section=details_section_id))
                                 for subcategory in category['subcategories']],
                        validators=[RequiredValidatorTO()]
                    )
                ]
            )
            sections.append(category_section)
        generic_section = FormSectionTO(
            id=details_section_id,
            title='Melding details',
            components=[
                TextInputComponentTO(
                    id='briefDescription',
                    title='Waarover gaat de melding, in het kort?',
                    keyboard_type=KeyboardType.DEFAULT,
                    multiline=False,
                    validators=[RequiredValidatorTO(), MaxLengthValidatorTO(maxlength=80)]
                ),
                LocationComponentTO(
                    id='location',
                    title='Indien relevant, duid een locatie aan.'
                ),
                TextInputComponentTO(
                    id='longDescription',
                    title='Beschrijf uw melding zo duidelijk mogelijk.',
                    keyboard_type=KeyboardType.DEFAULT,
                    multiline=True,
                    Validators=[RequiredValidatorTO()]
                ),
                FileComponentTO(
                    id='file',
                    title='Voeg een foto of bestand toe aan uw melding indien relevant.',
                )
            ]
        )
        sections.append(generic_section)

        form.sections = sections

        submission_section = FormSectionTO()
        submission_section.title = translate(service_profile.defaultLanguage, 'oca.thank_you')
        submission_section.description = 'We hebben uw melding goed ontvangen.'
        form.submission_section = submission_section

        form_settings = FormSettingsTO()
        form_settings.title = form.title
        form_settings.visible = False
        form_settings.steps = [
            CompletedFormStepTO(step_id=u'content'),
            CompletedFormStepTO(step_id=u'test'),
            CompletedFormStepTO(step_id=u'settings'),
            CompletedFormStepTO(step_id=u'action'),
            CompletedFormStepTO(step_id=u'integrations'),
        ]
        mapping = [
            TOPDeskSectionMapping(id='choose_category', components=[
                TOPDeskCategoryMapping(id='category',
                                       categories={category['id']: category['id'] for category in subcategories})
            ])
        ]
        for category in subcategories:
            mapping.append(TOPDeskSectionMapping(id='category_' + category['id'], components=[
                TOPDeskSubCategoryMapping(id='subcategory',
                                          categories={category['id']: category['id']
                                                      for category in category['subcategories']})
            ]))
        mapping.append(TOPDeskSectionMapping(id=details_section_id, components=[
            TOPDeskBriefDescriptionMapping(id='briefDescription'),
        ]))
        form_settings.integrations = [
            FormIntegrationTO(provider=FormIntegrationProvider.TOPDESK,
                              enabled=True,
                              configuration=TOPDeskFormConfiguration(mapping=mapping).to_dict())
        ]
        oca_form.settings = form_settings
        oca_form.form = form
        from solutions.common.bizz.forms import create_form
        return create_form(oca_form, service_profile.service_user)

    def submit(self, form_configuration, submission, form, service_profile, user_details):
        payload = {
            'form': form.to_dict(),
            'submission': FormSubmissionTO.from_model(submission).to_dict(),
            'user_details': user_details.to_dict()
        }
        result = _do_request('/callbacks/form/%d' % form.id, urlfetch.POST, payload, authorization=service_profile.sik)
        return result['external_reference']
