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

from rogerthat.bizz.job import run_job
from rogerthat.bizz.jobs.bizz import cleanup_jobs_data
from rogerthat.consts import JOBS_WORKER_QUEUE, JOBS_CONTROLLER_QUEUE
from rogerthat.models.jobs import JobMatchingCriteria


def cleanup_inactive_users():
    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    d = datetime.utcnow() - relativedelta(months=2)
    run_job(_qry_inactive_users, [d], _worker_inactive_users, [],
            worker_queue=JOBS_WORKER_QUEUE, controller_queue=JOBS_CONTROLLER_QUEUE)


def _qry_inactive_users(d):
    return JobMatchingCriteria.list_inactive_loads(d)


def _worker_inactive_users(job_criteria_key):
    job_criteria = job_criteria_key.get()
    if not job_criteria:
        return
    cleanup_jobs_data(job_criteria.app_user)
