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

from rogerthat.bizz.job import run_job, MODE_BATCH
from rogerthat.consts import MIGRATION_QUEUE
from rogerthat.models import Message, FormMessage


def job():
    run_job(_query_m, [], _worker, [], worker_queue=MIGRATION_QUEUE, mode=MODE_BATCH, batch_size=25)
    run_job(_query_fm, [], _worker, [], worker_queue=MIGRATION_QUEUE, mode=MODE_BATCH, batch_size=25)


def _query_m():
    return Message.all(keys_only=True)

def _query_fm():
    return FormMessage.all(keys_only=True)


def _worker(messasge_keys):
    messages = db.get(messasge_keys)  # type: Message
    to_put = []
    for message in messages:
        should_save = False
        if not message.buttons_json:
            data_buttons = {}
            for button in message.buttons.values():
                data_buttons[button.id] = button
            message.save_buttons(data_buttons)
            message.buttons = None
            should_save = True
        
        if not message.embedded_app_json:
            data_embedded_app = None
            if message.embedded_app:
                data_embedded_app = message.embedded_app
            message.save_embedded_app(data_embedded_app) 
            message.embedded_app = None
            should_save = True
            
        if not message.attachments_json:
            data_attachments = {}
            for attachment in message.attachments.values():
                data_attachments[attachment.index] = attachment
            message.save_attachments(data_attachments)
            message.attachments = None
            should_save = True
            
        if not message.member_statuses_json:
            data_member_statuses = {}
            for ms in message.memberStatusses.values():
                data_member_statuses[ms.index] = ms
            message.save_member_statuses(data_member_statuses)
            message.memberStatusses = None
            should_save = True
        
        if isinstance(message, FormMessage) and not message.form_json:
            data_form = None
            if message.form:
                data_form = message.form
            message.save_form(data_form)
            message.form = None
            should_save = True
        
        if should_save:
            to_put.append(message)
    if to_put:
        db.put(to_put)