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
from rogerthat.models import ServiceProfile
from rogerthat.to import TO
from rogerthat.to.forms import DynamicFormTO
from rogerthat.to.service import UserDetailsTO
from solutions.common.models.forms import FormSubmission


class BaseFormIntegration(object):
    CONFIGURATION_TYPE = TO

    def __init__(self, configuration):
        # type: (dict) -> None
        self.configuration = configuration

    def submit(self, form_configuration, submission_key, form, service_profile, user_details):
        # type: (dict, FormSubmission, DynamicFormTO, ServiceProfile, UserDetailsTO) -> str
        raise NotImplementedError()

    def update_configuration(self, form_id, configuration, service_profile):
        # type: (int, dict, ServiceProfile) -> None
        raise NotImplementedError()
