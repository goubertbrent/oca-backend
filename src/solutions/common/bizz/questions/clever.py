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

import json
import logging

from google.appengine.api import urlfetch
from rogerthat.service.api import messaging
from rogerthat.to.messaging import AnswerTO, MemberTO


HEADERS = {
    'content-type': 'application/json',
    'accept': 'application/json'
}


def _do_post(settings, payload=None):
    payload = json.dumps(payload or {})
    response = urlfetch.fetch(
        settings.params['server_url'], payload=payload, method=urlfetch.POST, headers=HEADERS, deadline=10)
    return response


def start_chat(settings, app_user, tag, context, service_identity):
    members = [MemberTO.from_user(app_user)]
    flags = messaging.ChatFlags.ALLOW_ANSWER_BUTTONS

    logging.debug('Starting new clever chat...')
    response = _do_post(settings)
    result = json.loads(response.content)['data']
    messages = _parse_output(result['output'])

    parent_message_key = messaging.start_chat(members,
                                              settings.params['chat']['topic'],
                                              messages[0]['message'],
                                              answers=messages[0].get('answers', []),
                                              service_identity=service_identity,
                                              tag=tag,
                                              context=context,
                                              flags=flags)

    for m in messages[1:]:
        messaging.send_chat_message(parent_message_key, m['message'], answers=m.get('answers', []), tag=tag)

    return parent_message_key, {'context': result['context']}


def chat_deleted(settings, chat):
    pass


def new_question(settings, chat, message):
    response = _do_post(settings, {
        'context': chat.params['context'],
        'input': {
            'text': message
        }
    })
    if response.status_code != 200:
        logging.warn(response.status_code)
        logging.warn(response.content)
        return []

    r = json.loads(response.content)
    chat.params['context'] = r['data']['context']
    chat.put()

    return _parse_output(r['data']['output'])


def _parse_output(output):
    messages = []
    if output['type'] == 'TEXT':
        logging.debug(output['text'][0])
        messages.append({'message': output['text'][0]})
        if output['buttonQuestion']:
            logging.debug(output['buttonQuestion'])
            answers = _create_answers(output['text'][1:])
            messages.append({'message': output['buttonQuestion'], 'answers': answers})

    if output['type'] == 'BUTTON':
        logging.debug(output['buttonQuestion'])
        answers = _create_answers(output['text'])
        messages.append({'message': output['buttonQuestion'], 'answers': answers})

    return messages


def _create_answers(buttons):
    answers = []
    for btn in buttons:
        answer = AnswerTO()
        answer.action = None
        answer.caption = btn['text']
        answer.id = btn['text']
        answer.type = u'button'
        answer.ui_flags = 0
        answers.append(answer)
        logging.debug('    [%(title)s] %(text)s', btn)
    return answers
