# -*- coding: utf-8 -*-
# Copyright 2019 Mobicage NV
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
# @@license_version:1.4@@
from datetime import datetime

import webapp2

from dateutil.relativedelta import relativedelta
from rogerthat.consts import SCHEDULED_QUEUE
from rogerthat.utils.cloud_tasks import create_task, schedule_tasks
from solutions.common.bizz.forms import finish_form, get_finish_form_task_name
from solutions.common.models.forms import OcaForm


class FinishFormsCron(webapp2.RequestHandler):
    def get(self):
        tasks = []
        now = datetime.now()
        one_hour_from_now = now + relativedelta(hours=1)
        for form in OcaForm.list_between_dates(now, one_hour_from_now):  # type: OcaForm
            task_name = get_finish_form_task_name(form)
            seconds_left = (form.visible_until - now).total_seconds()
            tasks.append(create_task(finish_form, form.id, form.service_user, _task_name=task_name,
                                     _countdown=seconds_left))
        schedule_tasks(tasks, SCHEDULED_QUEUE)
