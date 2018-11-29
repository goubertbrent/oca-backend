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
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from rogerthat.to.messaging.service_callback_results import FlowMemberResultCallbackResultTO
from rogerthat.to.messaging.flow import FLOW_STEP_MAPPING
from rogerthat.to.service import UserDetailsTO
from solutions.common import SOLUTION_COMMON
from solutions.common.bizz.general_counter import increment, get_count
from solutions.common.models.polls import Answer, Poll, PollRegister, PollStatus, Vote, Question, \
    QuestionType, QuestionTypeException
from solutions.common.to.polls import PollTO, FlowPollTO


class PollNotFoundException(BusinessException):
    pass


class DuplicatePollAnswerException(BusinessException):
    pass


@returns(tuple)
@arguments(service_user=users.User, status=int, cursor=unicode, limit=int)
def get_polls(service_user, status, cursor=None, limit=20):
    parent_service = parent_ndb_key(service_user, SOLUTION_COMMON)
    qry = Poll.query(ancestor=parent_service).filter(Poll.status == status)
    results, new_cursor, has_more = qry.fetch_page(limit, start_cursor=cursor)
    if new_cursor:
        new_cursor = unicode(new_cursor.urlsafe())
    return results, new_cursor, has_more


@returns(Poll)
@arguments(service_user=users.User, poll=PollTO)
def update_poll(service_user, poll):
    if poll.status != PollStatus.PENDING:
        raise BusinessException('poll_started_cannot_update')

    type_ = Poll
    if poll.is_vote:
        type_ = Vote

    key = type_.create_key(service_user, poll.id)
    new_poll = key.get()
    if not new_poll:
        new_poll = type_(key=key)

    try:
        new_poll.name = poll.name
        new_poll.questions = [q.to_model() for q in poll.questions]
        new_poll.put()
    except QuestionTypeException:
        raise BusinessException('vote_question_types_error')
    return new_poll


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
        pass

    key.delete()


@returns([Poll])
@arguments(service_user=users.User)
def get_running_polls(service_user):
    parent = parent_ndb_key(service_user, SOLUTION_COMMON)
    return list(Poll.query(ancestor=parent).filter(Poll.status == PollStatus.RUNNING))


@returns(Answer)
@arguments(service_user=users.User, poll_id=(int, long), question=Question, values=[unicode])
def create_answer(service_user, poll_id, question, values):
    answer = Answer.create(service_user, poll_id, question, values)
    answer.put()
    return answer


@ndb.transactional()
@returns()
@arguments(service_user=users.User, app_user=users.User, poll_id=(int, long), values=[unicode])
def register_answer(service_user, app_user, poll_id, values):
    if PollRegister.exists(app_user, poll_id):
        raise DuplicatePollAnswerException


    def question_choice_counter_name(question_id, choice):
        return 'poll_%d_question_%d_%s' % (poll_id, question_id, choice)

    PollRegister.create(app_user, poll_id)
    poll = Poll.create_key(service_user, poll_id).get()
    if not poll:
        raise PollNotFoundException

    for i in range(0, poll.questions):
        question = poll.questions[i]
        if question.TYPE == QuestionType.MULTIPLE_CHOICE or \
            question.TYPE == QuestionType.CHECKBOXES:
            choice = values[i]
            if choice:
                increment(question_choice_counter_name(i, choice))
        else:
            create_answer(service_user, poll_id, question, values)


@returns(FlowPollTO)
@arguments(poll=Poll)
def get_flow_poll(poll):
    flow_poll = FlowPollTO.from_model(poll)

    question_len = len(flow_poll.questions)
    for i in range(0, question_len - 1):
        flow_poll.flow_questions[i].next = flow_poll.flow_questions[i + 1]
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
    pass
