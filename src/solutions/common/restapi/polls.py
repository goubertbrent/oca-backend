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
from rogerthat.dal import parent_ndb_key
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from solutions.common import SOLUTION_COMMON
from solutions.common.bizz.polls import update_poll, start_poll, stop_poll, PollNotFoundException
from solutions.common.models.polls import Poll, PollStatus
from solutions.common.to.polls import PollTO, PollsListTO


@rest('/common/polls', 'get')
@returns(PollsListTO)
@arguments(status=int, cursor=unicode, limit=int)
def api_get_polls(status, cursor=None, limit=20):
    service_user = users.get_current_user()
    parent_service = parent_ndb_key(service_user, SOLUTION_COMMON)
    qry = Poll.query(ancestor=parent_service).filter(Poll.status == status)
    results, new_cursor, has_more = qry.fetch_page(limit, start_cursor=cursor)
    if new_cursor:
        new_cursor = unicode(new_cursor.urlsafe())
    return PollsListTO(results, new_cursor, has_more)


@rest('/common/polls', 'post', flavor=REST_FLAVOR_TO)
@returns(PollTO)
@arguments(data=PollTO)
def api_create_poll(data):
    try:
        service_user = users.get_current_user()
        return update_poll(service_user, poll=data)
    except BusinessException as bex:
        raise HttpBadRequestException(bex.message)


@rest('/common/polls/<poll_id:[^/]+>', 'get')
@returns(PollTO)
@arguments(poll_id=(int, long))
def api_get_poll(poll_id):
    service_user = users.get_current_user()
    poll = Poll.create_key(service_user, poll_id).get()
    if not poll:
        raise HttpNotFoundException('poll_not_found')
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
            return start_poll(service_user, poll_id)
        elif data.status == PollStatus.COMPLELTED:
            return stop_poll(service_user, poll_id)
        else:
            raise BusinessException('poll_invalid_status')
    except PollNotFoundException:
        raise HttpNotFoundException('poll_not_found')
    except BusinessException as bex:
        raise HttpBadRequestException(bex.message)


@rest('/common/polls/<poll_id:[^/]+>', 'delete')
@returns(PollTO)
@arguments(poll_id=(int, long))
def api_remove_poll(poll_id):
    try:
        service_user = users.get_current_user()
        # TODO: remove poll and all related records
    except PollNotFoundException:
        raise HttpNotFoundException('poll_not_found')
    except BusinessException as bex:
        raise HttpBadRequestException(bex.message)
