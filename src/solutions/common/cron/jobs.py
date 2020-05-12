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

from datetime import datetime

import webapp2
from dateutil.relativedelta import relativedelta

from rogerthat.bizz.job import run_job
from solutions.common.jobs.models import JobsSettings
from solutions.common.jobs.notifications import send_job_notifications_for_service


def _get_job_settings():
    return JobsSettings.list_with_hourly_summary_enabled()


class JobsNotificationsHandler(webapp2.RequestHandler):
    def get(self):
        current_date = datetime.now()
        one_hour_ago = current_date - relativedelta(hours=1)
        run_job(_get_job_settings, [], send_job_notifications_for_service, [one_hour_ago, current_date])
