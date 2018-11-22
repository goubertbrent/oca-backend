from mcfw.rpc import arguments, returns
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from solutions.common.models.polls import Poll, PollStatus, Vote, QuestionTypeException
from solutions.common.to.polls import PollTO, MultipleChoiceQuestionTO


@returns(PollTO)
@arguments(service_user=users.User, poll=PollTO)
def update_poll(service_user, poll):
    if poll.status != PollStatus.PENDING:
        raise BusinessException('poll_started_cannot_update')

    type_ = Poll
    if poll.is_vote:
        type_ = Vote

    key = type_.create_key(service_user)
    new_poll = key.get()
    if not new_poll:
        new_poll = type_(key=key)

    try:
        new_poll.questions = [q.to_model() for q in poll.questions]
        new_poll.put()
        poll.id = new_poll.id
    except QuestionTypeException:
        raise BusinessException('vote_question_types_error')
    return poll


@returns(PollTO)
@arguments(service_user=users.User, poll_id=(int, long))
def start_poll(service_user, poll_id):
    poll = Poll.create_key(service_user, poll_id).get()
    if poll:
        if poll.status != PollStatus.PENDING:
            raise BusinessException('poll_started_or_completed')
        poll.status = PollStatus.RUNNING
        poll.put()
    return PollTO.from_model(poll)


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
