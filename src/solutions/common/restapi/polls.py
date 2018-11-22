from mcfw.restapi import rest
from mcfw.rpc import arguments, returns
from rogerthat.dal import parent_ndb_key
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from solutions.common import SOLUTION_COMMON
from solutions.common.bizz.polls import update_poll, start_poll, stop_poll
from solutions.common.models.polls import Poll, PollStatus
from solutions.common.to import ReturnStatusTO
from solutions.common.to.polls import PollTO, PollsListTO


@rest('/common/polls', 'get')
@returns(PollsListTO)
@arguments(status=int, cursor=unicode, limit=int)
def api_get_polls(status, cursor=None, limit=20):
    service_user = users.get_current_user()
    parent_service = parent_ndb_key(service_user, SOLUTION_COMMON)
    qry = Poll.query(ancestor=parent_service).filter(Poll.status == status)
    results, new_cursor, has_more = qry.fetch_page(limit, start_cursor=cursor)
    return PollsListTO(results, unicode(new_cursor.urlsafe()), has_more)


@rest('/common/polls', 'post')
@returns((PollTO, ReturnStatusTO))
@arguments(poll=PollTO)
def api_create_or_update_poll(poll):
    try:
        service_user = users.get_current_user()
        return update_poll(service_user, poll)
    except BusinessException as bex:
        return ReturnStatusTO.create(False, bex.message)



@rest('/common/polls/<poll_id:[^/]+>', 'post')
@returns((PollTO, ReturnStatusTO))
@arguments(poll_id=(int, long))
def api_start_poll(poll_id):
    try:
        service_user = users.get_current_user()
        return start_poll(service_user, poll_id)
    except BusinessException as bex:
        return ReturnStatusTO.create(False, bex.message)


@rest('/common/polls/<poll_id:[^/]+>', 'put')
@returns((PollTO, ReturnStatusTO))
@arguments(poll_id=(int, long))
def api_stop_poll(poll_id):
    try:
        service_user = users.get_current_user()
        return stop_poll(service_user, poll_id)
    except BusinessException as bex:
        return ReturnStatusTO.create(False, bex.message)
