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

from green_valley import GreenValleyFormIntegration
from solutions.common.bizz.forms.integrations.base import BaseFormIntegration
from solutions.common.bizz.forms.integrations.email_integration import EmailFormIntegration
from solutions.common.models.forms import FormIntegrationConfiguration, FormIntegrationProvider

mapping = {
    FormIntegrationProvider.GREEN_VALLEY: GreenValleyFormIntegration,
    FormIntegrationProvider.EMAIL: EmailFormIntegration,
}


def get_form_integration(provider, configuration):
    # type: (str, FormIntegrationConfiguration) -> BaseFormIntegration
    if provider in mapping:
        return mapping[provider](configuration and configuration.configuration)
