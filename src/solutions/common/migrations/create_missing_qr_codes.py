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
from rogerthat.consts import MIGRATION_QUEUE
from rogerthat.rpc import users
from solutions.common.bizz import SolutionModule
from solutions.common.bizz.messaging import POKE_TAG_BROADCAST_CREATE_NEWS
from solutions.common.bizz.provisioning import _configure_inbox_qr_code_if_needed, _configure_broadcast_create_news
from solutions.common.dal import get_solution_main_branding
from solutions.common.models import SolutionSettings


def job():
    run_job(_qry, [], _worker, [], worker_queue=MIGRATION_QUEUE)


def _qry():
    return SolutionSettings.all()


def _worker(sln_settings):
    if SolutionModule.BROADCAST in sln_settings.modules or not sln_settings.inbox_connector_qrcode:
        with users.set_user(sln_settings.service_user):
            main_branding = get_solution_main_branding(sln_settings.service_user)
            if SolutionModule.BROADCAST in sln_settings.modules:
                _configure_broadcast_create_news(sln_settings, main_branding, sln_settings.main_language,
                                                 POKE_TAG_BROADCAST_CREATE_NEWS)
            if not sln_settings.inbox_connector_qrcode:
                _configure_inbox_qr_code_if_needed(sln_settings, main_branding)
