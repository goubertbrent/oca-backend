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

from google.appengine.api import urlfetch

from rogerthat.bizz.maps.reports import _do_request
from rogerthat.to import TO
from solutions.common.bizz.forms.integrations.base import BaseFormIntegration
from solutions.common.models.forms import FormIntegrationProvider
from solutions.common.to.forms import FormSubmissionTO


class GreenValleyConfiguration(TO):
    pass


class GreenValleyFormIntegration(BaseFormIntegration):

    def __init__(self, configuration):
        self.configuration = GreenValleyConfiguration.from_dict(configuration)
        super(GreenValleyFormIntegration, self).__init__(self.configuration)

    def update_configuration(self, form_id, configuration, service_profile):
        configuration['provider'] = FormIntegrationProvider.GREEN_VALLEY
        payload = {'form_id': form_id, 'config': configuration}
        return _do_request('/incidents/integrations/form', urlfetch.PUT, payload, authorization=service_profile.sik)

    def submit(self, form_configuration, submission, form, service_profile, user_details):
        payload = {
            'form': form.to_dict(),
            'submission': FormSubmissionTO.from_model(submission).to_dict(),
            'user_details': user_details.to_dict()
        }
        result = _do_request('/callbacks/form/%d' % form.id, urlfetch.POST, payload, authorization=service_profile.sik)
        return result['external_reference']
