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

from __future__ import unicode_literals
from google.appengine.ext import deferred, ndb
from mcfw.rpc import arguments, returns
from mcfw.properties import object_factory
from rogerthat.dal import parent_ndb_key
from rogerthat.models import Message
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from rogerthat.to.messaging.service_callback_results import MessageCallbackResultTypeTO, \
    FlowMemberResultCallbackResultTO
from rogerthat.to.messaging.flow import FLOW_STEP_MAPPING
from rogerthat.to.service import UserDetailsTO
from solutions import translate as common_translate
from solutions.common import SOLUTION_COMMON
from solutions.common.bizz import broadcast_updates_pending
from solutions.common import SOLUTION_COMMON
from solutions.common.dal import get_solution_main_branding, get_solution_settings
from solutions.common.models.polls import AnswerType, Poll, PollAnswer, PollStatus, Question, \
    QuestionChoicesException
from solutions.common.to.polls import FlowPollTO, PollTO


class PollNotFoundException(BusinessException):
    pass


class DuplicatePollAnswerException(BusinessException):
    pass


@returns(tuple)
@arguments(service_user=users.User, cursor=unicode, limit=int)
def get_polls(service_user, cursor=None, limit=20):
    parent_service = parent_ndb_key(service_user, SOLUTION_COMMON)
    qry = Poll.query(ancestor=parent_service)
    results, new_cursor, has_more = qry.fetch_page(limit, start_cursor=cursor)
    if new_cursor:
        new_cursor = unicode(new_cursor.urlsafe())
    return results, new_cursor, has_more


@returns(Poll)
@arguments(service_user=users.User, poll=PollTO)
def update_poll(service_user, poll):
    if poll.status != PollStatus.PENDING:
        raise BusinessException('poll_started_cannot_update')

    new_poll = None
    if poll.id:
        new_poll = Poll.create_key(service_user, poll.id).get()

    if not new_poll:
        new_poll = Poll.create(service_user)

    try:
        new_poll.name = poll.name
        new_poll.questions = [q.to_model() for q in poll.questions]
        new_poll.put()
    except QuestionChoicesException:
        raise BusinessException('add_2_choices_at_least')
    return new_poll


@returns()
@arguments(service_user=users.User)
def set_updates_pending(service_user):
    sln_settings = get_solution_settings(service_user)
    sln_settings.updates_pending = True
    sln_settings.put()
    broadcast_updates_pending(sln_settings)


@returns(Poll)
@arguments(service_user=users.User, poll_id=(int, long))
def start_poll(service_user, poll_id):
    poll = Poll.create_key(service_user, poll_id).get()
    if poll:
        if poll.status != PollStatus.PENDING:
            raise BusinessException('poll_started_or_completed')
        if not poll.questions:
            raise BusinessException('poll_has_no_questions')
        poll.status = PollStatus.RUNNING
        poll.put()
        set_updates_pending(service_user)
        return poll
    raise PollNotFoundException


@returns(Poll)
@arguments(service_user=users.User, poll_id=(int, long))
def stop_poll(service_user, poll_id):
    poll = Poll.create_key(service_user, poll_id).get()
    if poll:
        if poll.status != PollStatus.RUNNING:
            raise BusinessException('poll_pending_or_completed')
        poll.status = PollStatus.COMPLELTED
        poll.put()
        set_updates_pending(service_user)
        return poll
    raise PollNotFoundException


@ndb.transactional()
@returns()
@arguments(service_user=users.User, poll_id=(int, long))
def remove_poll(service_user, poll_id):
    key = Poll.create_key(service_user, poll_id)
    poll = key.get()
    if not poll:
        return

    if poll.status == PollStatus.RUNNING:
        raise BusinessException('poll_running_cannot_delete')
    elif poll.status == PollStatus.COMPLELTED:
        # TODO: remove all related answers, counters...etc
        pass

    key.delete()


@returns([Poll])
@arguments(service_user=users.User)
def get_running_polls(service_user):
    parent = parent_ndb_key(service_user, SOLUTION_COMMON)
    return list(Poll.query(ancestor=parent).filter(Poll.status == PollStatus.RUNNING))


def has_choices(answer_type):
    return answer_type == AnswerType.MULTIPLE_CHOICE or \
        answer_type == AnswerType.CHECKBOXES


def question_choice_counter_name(poll_id, question_id, choice):
    return 'poll_%d_question_%d_%s' % (poll_id, question_id, choice)


@ndb.transactional()
@returns()
@arguments(service_user=users.User, app_user=users.User, poll=Poll, answer_values=[unicode])
def register_answer(service_user, app_user, poll, answer_values):
    """
    Register an answer for a given poll

    Args:
        app_user (users.User)
        poll (Poll)
        answer_values (list of list): with all possible values for every question

    Raises:
        DuplicatePollAnswerException: in case of duplicate answer for the same app_user/poll
    """
    if PollAnswer.get_by_poll(app_user, poll.id):
        raise DuplicatePollAnswerException
    PollAnswer.create(app_user, poll.id, *answer_values).put()


@returns(FlowPollTO)
@arguments(poll=Poll)
def get_flow_poll(poll):
    flow_poll = FlowPollTO.from_model(poll)

    question_len = len(flow_poll.questions)
    for question_id in range(0, question_len - 1):
        flow_poll.flow_questions[question_id].next = flow_poll.flow_questions[question_id + 1]
    flow_poll.flow_questions[-1].next = None
    return flow_poll


@returns([FlowPollTO])
@arguments(service_user=users.User)
def get_running_polls_for_flow(service_user):
    return map(get_flow_poll, get_running_polls(service_user))


@returns(FlowMemberResultCallbackResultTO)
@arguments(
    service_user=users.User, message_flow_run_id=unicode, member=unicode,
    steps=[object_factory("step_type", FLOW_STEP_MAPPING)], end_id=unicode, end_message_flow_id=unicode,
    parent_message_key=unicode, tag=unicode, result_key=unicode, flush_id=unicode, flush_message_flow_id=unicode,
    service_identity=unicode, user_details=[UserDetailsTO])
def poll_answer_received(
    service_user, message_flow_run_id, member, steps, end_id, end_message_flow_id, parent_message_key,
    tag, result_key, flush_id, flush_message_flow_id, service_identity, user_details):

    from solutions.common.bizz.messaging import _get_step_with_id, POKE_TAG_POLLS
    user_detail = user_details[0]

    def result_message(message, **kwargs):
        result = FlowMemberResultCallbackResultTO()
        result.type = u'message'
        result.value = MessageCallbackResultTypeTO()
        result.value.message = unicode(
            common_translate(user_detail.language, SOLUTION_COMMON, message, **kwargs)
        )
        result.value.answers = []
        result.value.attachments = []
        result.value.flags = Message.FLAG_ALLOW_DISMISS
        result.value.alert_flags = 1
        result.value.branding = get_solution_main_branding(service_user).branding_key
        result.value.dismiss_button_ui_flags = 0
        result.value.step_id = u''
        result.value.tag = POKE_TAG_POLLS
        return result

    first_step = _get_step_with_id(steps, 'flow_start')
    if not first_step:
        return

    poll_id = int(first_step.answer_id)
    poll = Poll.create_key(service_user, poll_id).get()
    if not poll:
        return

    if poll.status != PollStatus.RUNNING:
        return

    def step_id_for_question(question_id):
        return '%d_question_%d' % (poll_id, question_id)

    answers = []
    for question_id in range(0, len(poll.questions)):
        question = poll.questions[question_id]
        step = _get_step_with_id(steps, step_id_for_question(question_id))
        if question.answer_type == AnswerType.CHECKBOXES:
            values = step.form_result.result.values
        elif step.form_result.result.value:
            values = [step.form_result.result.value]
        # all possible values of answers for this question
        answers.extend(values)

    try:
        register_answer(
            service_user, user_detail.toAppUser(), poll, answers)
        return result_message('poll_answer_registered', name=poll.name)
    except DuplicatePollAnswerException:
        return result_message('poll_duplicate_answer', name=poll.name)
