# -*- coding: utf-8 -*-
# Copyright 2018 Mobicage NV
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
# @@license_version:1.3@@

import datetime
import logging

from google.appengine.ext import ndb, webapp

from rogerthat.bizz.job import run_job
from rogerthat.models import Message
from rogerthat.rpc import users
from rogerthat.service.api import messaging
from rogerthat.to.messaging import MemberTO
from solutions import SOLUTION_COMMON, translate as common_translate
from solutions.common.dal import get_solution_main_branding, get_solution_settings
from solutions.common.models.polls import PollAnswer, PollStatus


def poll_answers_query(poll_id):
    return PollAnswer.query(
        PollAnswer.poll_id == poll_id,
        PollAnswer.notify_result == True
    )


def notify_poll_answer_user(
    poll_answer_key, poll_name, service_user, language, main_branding_key, dry_run=False):
    poll_answer = poll_answer_key.get()
    if not poll_answer:
        return

    logging.debug(
        'Sending notification to %s for poll id: %d', poll_answer.app_user.email(), poll_answer.poll_id)

    if not dry_run:
        message = common_translate(
            language, SOLUTION_COMMON, u'polls_results_available', name=poll_name)
        with users.set_user(service_user):
            messaging.send(
                parent_key=None,
                parent_message_key=None,
                message=message,
                answers=[],
                flags=Message.FLAG_ALLOW_DISMISS,
                members=[MemberTO.from_user(poll_answer.app_user)],
                branding=main_branding_key,
                tag=None,
                service_identity=None)


def notify_poll_results(poll, dry_run=False):
    if poll.status != PollStatus.COMPLELTED or not poll.answers_collected:
        logging.warning('Poll (%d) is not completed or answers are collected', poll.id)
        return

    service_user = poll.service_user
    sln_settings = get_solution_settings(service_user)
    main_branding_key = get_solution_main_branding(service_user).branding_key
    run_job(
        poll_answers_query, [poll.id],
        notify_poll_answer_user, [
            poll.name, service_user, sln_settings.main_language, main_branding_key, dry_run])
