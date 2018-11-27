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

from google.appengine.ext import ndb
from mcfw.rpc import arguments, returns
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from solutions.common.models.polls import Poll, PollStatus, Vote, QuestionTypeException
from solutions.common.to.polls import PollTO


class PollNotFoundException(BusinessException):
    pass


@returns(PollTO)
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
    return PollTO.from_model(new_poll)


@returns(PollTO)
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
        return PollTO.from_model(poll)
    raise PollNotFoundException


@returns(PollTO)
@arguments(service_user=users.User, poll_id=(int, long))
def stop_poll(service_user, poll_id):
    poll = Poll.create_key(service_user, poll_id).get()
    if poll:
        if poll.status != PollStatus.RUNNING:
            raise BusinessException('poll_pending_or_completed')
        poll.status = PollStatus.COMPLELTED
        poll.put()
        return PollTO.from_model(poll)
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
