# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
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
# @@license_version:1.5@@

import json
import logging

from google.appengine.api import urlfetch

HEADERS = {
    'content-type': 'application/json',
    'accept': 'application/json'
}


def chat_started(settings, message_key):
    params = json.dumps({})
    response = urlfetch.fetch(settings.params['server_url'], payload=params, method=urlfetch.POST, headers=HEADERS, deadline=10)
    context = json.loads(response.content)['data']['context']
    return {'context': context}


def chat_deleted(settings, chat):
    pass


def new_question(settings, chat, message):
    params = json.dumps({
        'context': chat.params['context'],
        'input': {
            'text': message
        }
    })
    response = urlfetch.fetch(settings.params['server_url'], payload=params, method=urlfetch.POST, headers=HEADERS, deadline=10)
    logging.debug(response.status_code)
    logging.debug(response.content)
    if response.status_code == 200:
        return json.loads(response.content)['data']['output']['text'][0]
