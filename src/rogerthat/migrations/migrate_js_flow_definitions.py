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

from google.appengine.ext import db

from rogerthat.bizz.job import run_job
from rogerthat.consts import MIGRATION_QUEUE
from rogerthat.models import MessageFlowDesign


def job():
    run_job(_query, [], _worker, [], worker_queue=MIGRATION_QUEUE)


def _query():
    return MessageFlowDesign.all(keys_only=True)


def _worker(mfd_key):
    message_flow_design = db.get(mfd_key)  # type: MessageFlowDesign
    if message_flow_design.js_flow_definitions_json:
        return
    data = {}
    if message_flow_design.js_flow_definitions:
        for jfd in message_flow_design.js_flow_definitions:
            data[jfd.language] = jfd
    message_flow_design.save_js_flow_definitions(data)
    message_flow_design.js_flow_definitions = None
    message_flow_design.put() 