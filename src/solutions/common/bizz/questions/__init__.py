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

from mcfw.rpc import returns, arguments
from rogerthat.rpc import users
from rogerthat.service.api import messaging
from rogerthat.to.messaging import MemberTO, AnswerTO, AttachmentTO
from rogerthat.to.messaging.service_callback_results import PokeCallbackResultTO
from rogerthat.to.service import UserDetailsTO
from rogerthat.utils import try_or_defer
from rogerthat.utils.app import create_app_user_by_email
from solutions.common.bizz.questions import clever
from solutions.common.dal.questions import get_chat_question_settings
from solutions.common.models.questions import ChatQuestionSettings, ChatQuestion


@returns(PokeCallbackResultTO)
@arguments(service_user=users.User, email=unicode, tag=unicode, result_key=unicode, context=unicode,
           service_identity=unicode, user_details=[UserDetailsTO])
def chat_question_poke(service_user, email, tag, result_key, context, service_identity, user_details):
    settings = get_chat_question_settings(service_user)
    if not settings:
        return

    user_detail = user_details[0]
    app_user = create_app_user_by_email(user_detail.email, app_id=user_detail.app_id)

    params = None
    if settings.integration == ChatQuestionSettings.INT_CLEVER:
        message_key, params = clever.start_chat(settings, app_user, tag, context, service_identity)

    try_or_defer(_create_chat_model, message_key, settings.integration, service_user, params or {})


def _create_chat_model(message_key, integration, service_user, params):
    chat = ChatQuestion(key=ChatQuestion.create_key(message_key))
    chat.integration = integration
    chat.service_user = service_user
    chat.params = params
    chat.put()


@returns()
@arguments(service_user=users.User, status=int, answer_id=unicode, received_timestamp=int, member=unicode,
           message_key=unicode, tag=unicode, acked_timestamp=int, parent_message_key=unicode, result_key=unicode,
           service_identity=unicode, user_details=[UserDetailsTO])
def chat_question_pressed(service_user, status, answer_id, received_timestamp, member, message_key, tag,
                          acked_timestamp, parent_message_key, result_key, service_identity, user_details):
    if not answer_id:
        return
    _process_new_message(service_user, parent_message_key, answer_id, tag)


@returns()
@arguments(service_user=users.User, parent_message_key=unicode, member=UserDetailsTO, timestamp=int, service_identity=unicode, tag=unicode)
def chat_question_deleted(service_user, parent_message_key, member, timestamp, service_identity, tag):
    chat = ChatQuestion.create_key(parent_message_key).get()
    if not chat:
        return
    settings = get_chat_question_settings(service_user)
    if not settings:
        return
    if chat.integration != settings.integration:
        return
    if settings.integration == ChatQuestionSettings.INT_CLEVER:
        clever.chat_deleted(settings, chat)


@returns()
@arguments(service_user=users.User, parent_message_key=unicode, message_key=unicode, sender=UserDetailsTO, message=unicode, answers=[AnswerTO],
           timestamp=int, tag=unicode, service_identity=unicode, attachments=[AttachmentTO])
def chat_question_new_message(service_user, parent_message_key, message_key, sender, message, answers,
                              timestamp, tag, service_identity, attachments):
    _process_new_message(service_user, parent_message_key, message, tag)


def _process_new_message(service_user, parent_message_key, message, tag):
    chat = ChatQuestion.create_key(parent_message_key).get()
    if not chat:
        return
    settings = get_chat_question_settings(service_user)
    if not settings:
        return
    if chat.integration != settings.integration:
        return

    messages = []
    if settings.integration == ChatQuestionSettings.INT_CLEVER:
        messages = clever.new_question(settings, chat, message)

    for m in messages:
        messaging.send_chat_message(parent_message_key, m['message'], answers=m.get('answers', []), tag=tag)
