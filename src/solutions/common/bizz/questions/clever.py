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

from rogerthat.to.messaging import AnswerTO

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

    if response.status_code != 200:
        logging.warn(response.status_code)
        logging.warn(response.content)
        return []
    messages = []
    r = json.loads(response.content)
    chat.params['context'] = r['data']['context']
    chat.put()

    output = r['data']['output']

    if output['type'] == 'TEXT':
        messages.append({'message': output['text'][0]})
        if output['buttonQuestion']:
            answers = []
            for i in range(1, len(output['text'])):
                t = output['text'][i]
                answer = AnswerTO()
                answer.action = None
                answer.caption = t['text']
                answer.id = t['text']
                answer.type = u'button'
                answer.ui_flags = 0
                answers.append(answer)
            messages.append({'message': output['buttonQuestion'], 'answers': answers})

    if output['type'] == 'BUTTON':
        answers = []
        for t in output['text']:
            answer = AnswerTO()
            answer.action = None
            answer.caption = t['text']
            answer.id = t['text']
            answer.type = u'button'
            answer.ui_flags = 0
            answers.append(answer)
        messages.append({'message': output['buttonQuestion'], 'answers': answers})
    return messages
