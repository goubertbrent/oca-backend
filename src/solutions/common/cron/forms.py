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
import logging
from datetime import datetime

import webapp2
from google.appengine.api.taskqueue import taskqueue

from dateutil.relativedelta import relativedelta
from rogerthat.consts import SCHEDULED_QUEUE
from rogerthat.utils.cloud_tasks import create_task, schedule_tasks
from solutions.common.bizz.forms import finish_form, get_finish_form_task_name
from solutions.common.models.forms import OcaForm


class FinishFormsCron(webapp2.RequestHandler):
    def get(self):
        now = datetime.now()
        one_hour_from_now = now + relativedelta(hours=1)
        for form in OcaForm.list_between_dates(now, one_hour_from_now):  # type: OcaForm
            task_name = get_finish_form_task_name(form)
            seconds_left = (form.visible_until - now).total_seconds()
            task = create_task(finish_form, form.id, form.service_user, _task_name=task_name, _countdown=seconds_left)
            try:
                schedule_tasks([task], SCHEDULED_QUEUE)
            except (taskqueue.TaskAlreadyExistsError, taskqueue.TombstonedTaskError):
                # This only happens in case a form gets updated an hour before the end time of the form
                # In that case the task gets scheduled when saving it, so we can ignore this error.
                logging.info('Task to finish form %d already scheduled', form.id)
