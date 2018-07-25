# -*- coding: utf-8 -*-
# Copyright 2018 Mobicage NV
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
# @@license_version:1.3@@

from rogerthat.bizz.job import run_job
from rogerthat.rpc import users
from rogerthat.service.api import system
from rogerthat.utils import now
from solutions.common.bizz.provisioning import get_and_store_main_branding
from solutions.common.models import SolutionBrandingSettings


def job():
    run_job(_qry, [], _worker, [])
    

def _qry():
    return SolutionBrandingSettings.all()


def _worker(branding_settings):
    if not branding_settings.show_identity_name:
        branding_settings.modification_time = now()
        branding_settings.put()
        
        service_user = branding_settings.service_user
        with users.set_user(service_user):
            get_and_store_main_branding(service_user)
            system.publish_changes()
