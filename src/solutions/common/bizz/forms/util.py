# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley NV
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

from rogerthat.to.forms import FieldComponentTO


# Removes questions marked with containing sensitive information from the form results
def remove_sensitive_answers(form_sections, form_section_results):
    # type: (list[FormSectionTO], list[FormSectionValueTO]) -> list[FormSectionValueTO]
    section_mapping = {section.id: section for section in form_sections}
    for form_section_result in form_section_results:
        form_section = section_mapping.get(form_section_result.id)
        if not form_section:
            continue
        component_mapping = {c.id: c for c in form_section.components if isinstance(c, FieldComponentTO)}
        new_components = []
        for component_value in form_section_result.components:
            component = component_mapping.get(component_value.id)
            if component:
                if not component.sensitive:
                    new_components.append(component_value)
            else:
                new_components.append(component_value)
        form_section_result.components = new_components
    return form_section_results
