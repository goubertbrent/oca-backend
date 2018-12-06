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

from mcfw.consts import REST_FLAVOR_TO
from mcfw.exceptions import HttpBadRequestException, HttpNotFoundException
from mcfw.restapi import rest
from mcfw.rpc import arguments, returns
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from solutions.common.bizz.polls import get_polls, update_poll, start_poll, stop_poll, remove_poll, \
    PollNotFoundException
from solutions.common.models.polls import Poll, PollStatus
from solutions.common.to.polls import PollTO, PollsListTO, QuestionTO


HTTP_POLL_NOT_FOUND = HttpNotFoundException('poll_not_found')


@rest('/common/polls', 'get')
@returns(PollsListTO)
@arguments(cursor=unicode, limit=int)
def api_get_polls(cursor=None, limit=20):
    service_user = users.get_current_user()
    results, new_cursor, has_more = get_polls(service_user, cursor, limit)
    return PollsListTO(results, new_cursor, has_more)


@rest('/common/polls', 'post', flavor=REST_FLAVOR_TO)
@returns(PollTO)
@arguments(data=PollTO)
def api_create_poll(data):
    try:
        service_user = users.get_current_user()
        PollTO.from_model(update_poll(service_user, poll=data))
    except BusinessException as bex:
        raise HttpBadRequestException(bex.message)


@rest('/common/polls/<poll_id:[^/]+>', 'get')
@returns(PollTO)
@arguments(poll_id=(int, long))
def api_get_poll(poll_id):
    service_user = users.get_current_user()
    poll = Poll.create_key(service_user, poll_id).get()
    if not poll:
        raise HTTP_POLL_NOT_FOUND
    return PollTO.from_model(poll)


@rest('/common/polls/<poll_id:[^/]+>', 'post', flavor=REST_FLAVOR_TO)
@returns(PollTO)
@arguments(poll_id=(int, long), data=PollTO)
def api_update_poll(poll_id, data):
    data.id = poll_id
    return api_create_poll(data)


@rest('/common/polls/<poll_id:[^/]+>', 'put')
@returns(PollTO)
@arguments(poll_id=(int, long), data=PollTO)
def api_start_or_stop_poll(poll_id, data):
    try:
        service_user = users.get_current_user()
        if data.status == PollStatus.RUNNING:
            poll = start_poll(service_user, poll_id)
        elif data.status == PollStatus.COMPLELTED:
            poll = stop_poll(service_user, poll_id)
        else:
            raise BusinessException('poll_invalid_status')
        return PollTO.from_model(poll)
    except PollNotFoundException:
        raise HTTP_POLL_NOT_FOUND
    except BusinessException as bex:
        raise HttpBadRequestException(bex.message)


@rest('/common/polls/<poll_id:[^/]+>', 'delete')
@returns()
@arguments(poll_id=(int, long))
def api_remove_poll(poll_id):
    try:
        service_user = users.get_current_user()
        remove_poll(service_user, poll_id)
    except BusinessException as bex:
        raise HttpBadRequestException(bex.message)


@rest('/common/polls/result/<poll_id:[^/]+>', 'get')
@returns([QuestionTO])
@arguments(poll_id=(int, long))
def api_get_poll_result(poll_id):
    return api_get_poll(poll_id).questions
