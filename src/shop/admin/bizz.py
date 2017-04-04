# -*- coding: utf-8 -*-
# Copyright 2017 Mobicage NV
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
# @@license_version:1.2@@

from rogerthat.models import RogerthatBackendErrors
from rogerthat.rpc.models import ClientError
from rogerthat.utils import now
from google.appengine.api import taskqueue, logservice
from google.appengine.ext import db
from shop.admin.dal import get_monitored_services_in_trouble_qry


def analyze_status():
    LOG_LIMIT = 30  # to prevent 'InvalidArgumentError: Too many request ids specified.'
    # Asynchronously fetch troubled services
    services_in_trouble = get_monitored_services_in_trouble_qry().run()

    # Asynchronously fetch rogerthat backend status
    rbe_rpc = db.get_async(RogerthatBackendErrors.get_key())

    # Fetch queue statusses
    default, controller, worker, fast, broadcast = taskqueue.QueueStatistics.fetch(
            ["default", "highload-controller-queue", "highload-worker-queue", 'fast', 'broadcast-queue'])
    rbe = rbe_rpc.get_result()
    logs = logservice.fetch(request_ids=rbe.requestIds[:LOG_LIMIT]) if rbe else None
    total_error_count = len(rbe.requestIds) if rbe else 0
    skipped_error_count = max(0, total_error_count - LOG_LIMIT)
    services = list(services_in_trouble)
    five_min_ago = (now() - 300) * 1000000

    client_errors = ClientError.all().order("-timestamp").fetch(20)
    result = dict(queues=dict(default=default, controller=controller, worker=worker, fast=fast, broadcast=broadcast),
                  rogerthatBackendStatus=logs,
                  errorCount=total_error_count,
                  skippedCount=skipped_error_count,
                  services=services,
                  five_min_ago=five_min_ago,
                  client_errors=client_errors)
    return result
