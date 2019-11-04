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

import logging
import re
from base64 import b64encode
from collections import OrderedDict
from mimetypes import guess_extension

from google.appengine.api import urlfetch

from lxml import etree
from mcfw.properties import unicode_property, typed_property, object_factory
from rogerthat.consts import DEBUG
from rogerthat.to import TO
from rogerthat.to.forms import FormSectionValueTO, TextInputComponentValueTO, SingleSelectComponentValueTO, \
    LocationComponentValueTO, MultiSelectComponentValueTO, DynamicFormTO, FieldComponentTO, MultiSelectComponentTO, \
    ValueTO, FileComponentValueTO
from solutions.common.bizz.forms.integrations.attachments import get_attachment_content
from solutions.common.bizz.forms.integrations.base import BaseFormIntegration
from solutions.common.models.forms import FormSubmission

ATTR_PREFIX = '__'


class GvFieldType(object):
    FLEX = 'flex'
    CONST = 'const'
    PERSON = 'person'
    LOCATION = 'location'
    FIELD = 'field'
    ATTACHMENT = 'attachment'


class GvMappingFlex(TO):
    type = unicode_property('type', default=GvFieldType.FLEX)
    id = unicode_property('id')
    field_def_id = unicode_property('field_def_id')


class GvMappingField(TO):
    # maps to a direct property of a case
    type = unicode_property('type', default=GvFieldType.FIELD)
    id = unicode_property('id')
    # One of the following 2 properties needs to be set
    field = unicode_property('field', default=None)
    value = unicode_property('value', default=None)


class GvMappingPerson(TO):
    type = unicode_property('type', default=GvFieldType.PERSON)
    id = unicode_property('id')
    field = unicode_property('field')
    sub_field = unicode_property('sub_field', default=None)


class GvMappingConst(TO):
    # A flex field of which its value is always the same
    type = unicode_property('type', default=GvFieldType.CONST)
    field = unicode_property('field')
    value = unicode_property('value')
    display_value = unicode_property('display_value', default=None)


class GvMappingLocation(TO):
    # Maps a location field to multiple flex fields
    type = unicode_property('type', default=GvFieldType.LOCATION)
    id = unicode_property('id')
    coordinates = unicode_property('coordinates', default=None)
    address = unicode_property('address', default=None)


class GvMappingAttachment(GvMappingFlex):
    # Maps a file upload component to a flex with an attachment_value
    type = unicode_property('type', default=GvFieldType.ATTACHMENT)
    name = unicode_property('name')


GV_MAPPING = {
    GvFieldType.FLEX: GvMappingFlex,
    GvFieldType.CONST: GvMappingConst,
    GvFieldType.PERSON: GvMappingPerson,
    GvFieldType.LOCATION: GvMappingLocation,
    GvFieldType.FIELD: GvMappingField,
    GvFieldType.ATTACHMENT: GvMappingAttachment,
}


class GvComponentMapping(object_factory):
    type = unicode_property('type')

    def __init__(self):
        super(GvComponentMapping, self).__init__('type', GV_MAPPING)


class GreenValleySectionMapping(TO):
    id = unicode_property('id')
    components = typed_property('component', GvComponentMapping(), True)  # type: list[GvComponentMapping]


class GreenValleyFormConfiguration(TO):
    type_id = unicode_property('type_id', default=None)
    mapping = typed_property('mapping', GreenValleySectionMapping, True)  # type: list[GreenValleySectionMapping]


class GreenValleyConfiguration(TO):
    username = unicode_property('username')
    password = unicode_property('password')
    base_url = unicode_property('base_url')


def _add_flex(flexes, field_def_id, value, display_value=None):
    flex = {'field_def_id': field_def_id}
    if value:
        flex['string_value'] = value
    if display_value:
        flex['display_value'] = display_value
    flexes.append({'flex': flex})


def _get_extension(content_type):
    ext = guess_extension(content_type)
    if ext == '.jpe':
        ext = '.jpg'
    return ext


class GreenValleyFormIntegration(BaseFormIntegration):

    def __init__(self, configuration):
        self.configuration = GreenValleyConfiguration.from_dict(configuration)
        super(GreenValleyFormIntegration, self).__init__(self.configuration)

    def _get_auth_header(self):
        return 'Basic %s' % b64encode('%s:%s' % (self.configuration.username, self.configuration.password))

    def _execute_request(self, path, method=urlfetch.GET, body=None):
        url = u'%s/suite-webservice/ws/rest%s' % (self.configuration.base_url, path)
        headers = {
            'Authorization': self._get_auth_header(),
            'Content-Type': 'application/xml',
        }
        result = urlfetch.fetch(url, body, method, headers=headers, deadline=30)  # type: urlfetch._URLFetchResult
        if DEBUG:
            logging.debug(result.content)
        if result.status_code not in (200, 201):
            logging.debug(result.content)
            additional = ''
            if result.status_code == 500:
                additional = 'Did you configure the correct type_id?'
            raise Exception(u'Error while executing request to %s: %s %s' % (url, result.status_code, additional))
        return result.content

    def submit(self, form_configuration, submission, form):
        # type: (dict, FormSubmission, DynamicFormTO) -> str
        original_form_mapping = {section.id: {component.id: component for component in section.components if
                                              isinstance(component, FieldComponentTO)}
                                 for section in form.sections}
        form_configuration = GreenValleyFormConfiguration.from_dict(form_configuration)
        if submission:
            pass
        section_values = FormSectionValueTO.from_list(submission.sections)
        gv_mapping = {section.id: section.components for section in form_configuration.mapping}
        flexes = []
        person = {}
        request = {
            'type_id': form_configuration.type_id,
            'reference': submission.id,
        }

        for section_value in section_values:
            gv_components = gv_mapping.get(section_value.id, [])
            if not gv_components:
                continue
            component_mapping = {component.id: component for component in section_value.components}
            for gv_comp in gv_components:
                if isinstance(gv_comp, GvMappingConst):
                    _add_flex(flexes, gv_comp.field, gv_comp.value, gv_comp.display_value)
                    continue
                elif isinstance(gv_comp, GvMappingField):
                    if gv_comp.value:
                        request[gv_comp.field] = gv_comp.value
                        continue
                comp_val = component_mapping.get(gv_comp.id)
                if not comp_val:
                    logging.debug('Skipping component %s: not found in form result', gv_comp)
                    continue
                component = original_form_mapping.get(section_value.id, {}).get(gv_comp.id)
                if not component:
                    logging.debug('Skipping component %s: not found in form definition', gv_comp)
                    continue
                if isinstance(gv_comp, GvMappingField):
                    value = None
                    if isinstance(comp_val, TextInputComponentValueTO):
                        value = comp_val.value
                    if isinstance(comp_val, MultiSelectComponentValueTO):
                        value = '\n'.join([c.label for c in component.choices if c.value in comp_val.values])
                    if value:
                        request[gv_comp.field] = value
                elif isinstance(gv_comp, GvMappingPerson):
                    if isinstance(comp_val, (TextInputComponentValueTO, SingleSelectComponentValueTO)):
                        if gv_comp.sub_field:
                            if gv_comp.field not in person:
                                person[gv_comp.field] = {}
                            person[gv_comp.field][gv_comp.sub_field] = comp_val.value
                        else:
                            person[gv_comp.field] = comp_val.value
                elif isinstance(gv_comp, GvMappingLocation):
                    if isinstance(comp_val, LocationComponentValueTO):
                        _add_flex(flexes, gv_comp.address, ', '.join(comp_val.address.address_lines))
                        _add_flex(flexes, gv_comp.coordinates, '%s,%s' % (comp_val.latitude, comp_val.longitude))
                elif isinstance(gv_comp, GvMappingAttachment):
                    if isinstance(comp_val, FileComponentValueTO):
                        content, content_type = get_attachment_content(comp_val.value)
                        name = '%s%s' % (gv_comp.name, _get_extension(content_type))
                        flex = {
                            'flex': {
                                'field_def_id': gv_comp.field_def_id,
                                'attachment_value': {'name': name, 'content': content}
                            }
                        }
                        flexes.append(flex)
                elif isinstance(gv_comp, GvMappingFlex):
                    if isinstance(comp_val, (TextInputComponentValueTO, SingleSelectComponentValueTO)):
                        _add_flex(flexes, gv_comp.field_def_id, comp_val.value)
                    elif isinstance(comp_val, MultiSelectComponentValueTO):
                        if component and isinstance(component, MultiSelectComponentTO):
                            if isinstance(gv_comp, GvMappingFlex):
                                choice_mapping = {c.value: c for c in component.choices}  # type: dict[str, ValueTO]
                                for value in comp_val.values:
                                    chosen_value = choice_mapping.get(value)
                                    if chosen_value:
                                        _add_flex(flexes, gv_comp.field_def_id, value, chosen_value.label)
                else:
                    raise Exception('Unknown component type: %s' % gv_comp)
        if flexes:
            request['flexes'] = flexes
        if person:
            person[ATTR_PREFIX + 'sequence'] = '1'
            person[ATTR_PREFIX + 'group_type'] = 'REQUESTER'
            request['agents'] = {'person': person}

        if not request.get('description') and not person:
            logging.debug('Not creating case: not enough information')
            return
        property_order = [
            'type_id',
            'subject',
            'description',
            ('flexes', [
                ('flex', [
                    'field_def_id',
                    'string_value',
                    'display_value',
                    ('attachment_value', ['name', 'content']),
                ])
            ]),
            'documents',
            ('agents', [
                ('person', [
                    ('contact', ['title', 'nickname', 'phone_number', 'mobile_number', 'email', 'website', 'fax']),
                    ('address', ['street_name', 'house_number', 'zip_code', 'city', 'country']),
                    'flexes',
                    'identity_number',
                    'function',
                    'first_name',
                    'family_name',
                    'gender',
                    'date_of_birth',
                    'place_of_birth',
                    'nationality'
                ])
            ])
        ]
        ordered_request = _order_dict(request, property_order)
        body = dict2xml(ordered_request, name='create_case_request')
        logging.debug('Submitting case request:\n%s',
                      re.sub(r'<content>.*?</content>', r'<content>(content omitted)</content>', body))
        result = self._execute_request('/cases', urlfetch.POST, body)
        return etree.XML(result).get('id')


def dict2xml(d, name='data'):
    # type: (dict, str) -> str
    r = etree.Element(name)
    return etree.tostring(buildxml(r, d), pretty_print=DEBUG)


def buildxml(r, d):
    # Properties starting with ATTR_PREFIX will be converted to attributes of the parent
    if isinstance(d, dict):
        for k, v in d.iteritems():
            if k.startswith(ATTR_PREFIX):
                r.set(k.lstrip(ATTR_PREFIX), v)
            else:
                s = etree.SubElement(r, k)
                buildxml(s, v)
    elif isinstance(d, tuple) or isinstance(d, list):
        for v in d:
            for key, val in v.iteritems():
                s = etree.SubElement(r, key)
                buildxml(s, val)
    elif isinstance(d, basestring):
        r.text = d
    else:
        r.text = str(d)
    return r


def _order_dict(dictionary, order):
    # type: (dict, list) -> OrderedDict
    """ For some strange reason the values must be present in a specific order or an error like this will be thrown:
AXBException occurred : cvc-complex-type.2.4.a: Invalid content was found starting with element 'address'.
One of '{gender, date_of_birth, place_of_birth, nationality}' is expected.."""
    result = OrderedDict({k: dictionary[k] for k in dictionary
                          if isinstance(k, basestring) and k.startswith(ATTR_PREFIX)})
    for key in order:
        if isinstance(key, tuple):
            parent, children = key
            if parent not in dictionary:
                continue
            if parent not in result:
                result[parent] = OrderedDict()
            if isinstance(dictionary[parent], list):
                result[parent] = [_order_dict(item, children) for item in dictionary[parent]]
            else:
                result[parent] = _order_dict(dictionary[parent], children)
        elif key in dictionary:
            result[key] = dictionary[key]
    return result
