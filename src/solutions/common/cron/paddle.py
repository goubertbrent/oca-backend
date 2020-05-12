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

import logging

import webapp2 as webapp2

from mcfw.exceptions import HttpBadRequestException
from rogerthat.bizz.job import run_job
from rogerthat.consts import FAST_QUEUE
from rogerthat.utils.cloud_tasks import create_task, schedule_tasks
from solutions.common.bizz import common_provision
from solutions.common.bizz.paddle import populate_info_from_paddle, get_paddle_info
from solutions.common.models.cityapp import PaddleSettings


class SyncPaddleInfoHandler(webapp2.RequestHandler):
    def get(self):
        run_job(_get_settings, [], update_paddle_info, [])


def _get_settings():
    return PaddleSettings.query().filter(PaddleSettings.base_url > 'http')


def update_paddle_info(settings_key):
    settings = settings_key.get()  # type: PaddleSettings
    try:
        data = get_paddle_info(settings)
    except HttpBadRequestException:
        logging.error('Failed to update paddle info for %s with url %s', settings.service_user, settings.base_url,
                      _suppress=False)
        return
    data.put()
    updated_settings = populate_info_from_paddle(settings, data)
    logging.debug('Updated %d services with updated info from paddle', len(updated_settings))
    if updated_settings:
        tasks = [create_task(common_provision, s.service_user) for s in updated_settings]
        schedule_tasks(tasks, FAST_QUEUE)
