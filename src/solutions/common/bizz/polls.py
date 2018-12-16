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

import json
from google.appengine.ext import deferred, ndb
from mcfw.rpc import arguments, returns, serialize_complex_value
from rogerthat.dal import parent_ndb_key
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from rogerthat.to.service import SendApiCallCallbackResultTO, UserDetailsTO
from solutions import translate as common_translate
from solutions.common import SOLUTION_COMMON
from solutions.common.bizz import put_branding
from solutions.common.bizz.branding import HTMLBranding, Resources, Javascript, Stylesheet
from solutions.common import SOLUTION_COMMON
from solutions.common.dal import get_solution_main_branding, get_solution_settings
from solutions.common.models.polls import AnswerType, Poll, PollAnswer, PollStatus, Question, \
    QuestionChoicesException
from solutions.common.to.polls import PollTO, UserPollTO


API_METHOD_SOLUTION_LOAD_POLLS = 'solutions.polls.load'
API_METHOD_SOLUTION_SUBMIT_POLL = 'solutions.polls.submit'


BRANDING_TEMPLATES = [
    'poll_item',
    'poll_page',
    'poll_questions',
    'poll_popup',
]

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
@arguments(service_user=users.User, app_user=users.User, poll=Poll, answer_values=[list], notify_result=bool)
def register_answer(service_user, app_user, poll, answer_values, notify_result=False):
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
    PollAnswer.create(app_user, poll.id, answer_values, notify_result).put()


@returns([UserPollTO])
@arguments(service_user=users.User, app_user=users.User)
def get_user_polls(service_user, app_user):
    # first get the polls user
    polls = {
        poll.id: UserPollTO.from_model(poll) for poll in get_running_polls(service_user)
    }

    user_answers = PollAnswer.list_by_app_user(app_user)
    answered_poll_keys = [
        Poll.create_key(service_user, answer.poll_id) for answer in user_answers]

    for poll in ndb.get_multi(answered_poll_keys):
        if polls.get(poll.id):
            polls[poll.id].answered = True
        else:
            polls[poll.id] = UserPollTO.from_model(poll, answered=True)

    return polls.values()


@returns(SendApiCallCallbackResultTO)
@arguments(
    service_user=users.User, email=unicode, method=unicode, params=unicode, tag=unicode,
    service_identity=unicode, user_details=[UserDetailsTO])
def api_load_polls(service_user, email, method, params, tag, service_identity, user_details):
    app_user = user_details[0].toAppUser()
    polls = get_user_polls(service_user, app_user)

    r = SendApiCallCallbackResultTO()
    r.result = json.dumps(
        serialize_complex_value(polls, UserPollTO, True)
    ).decode('utf-8')
    r.error = None
    return r


@returns(SendApiCallCallbackResultTO)
@arguments(
    service_user=users.User, email=unicode, method=unicode, params=unicode, tag=unicode,
    service_identity=unicode, user_details=[UserDetailsTO])
def api_submit_poll(service_user, email, method, params, tag, service_identity, user_details):
    app_user = user_details[0].toAppUser()
    answer = json.loads(params)
    poll_id = answer['poll_id']
    poll = Poll.create_key(service_user, poll_id).get()
    if not poll:
        return

    r = SendApiCallCallbackResultTO()

    try:
        register_answer(service_user, app_user, poll, answer['values'], answer['notify'])
        r.result = json.dumps(
            serialize_complex_value(UserPollTO.from_model(poll, answered=True), UserPollTO, False)
        ).decode('utf-8')
        r.error = None
    except DuplicatePollAnswerException:
        r.result = None
        r.error = 'duplicate_answer'

    return r



def provision_polls_branding(solution_settings, main_branding, language):
    """
    Args:
        solution_settings (SolutionSettings)
        main_branding (solutions.common.models.SolutionMainBranding)
        language (unicode)
    """
    if not solution_settings.polls_branding_hash:
        with HTMLBranding(main_branding, 'polls', *Resources.all()) as html_branding:
            templates = json.dumps({
                name: html_branding.render_template('%s.html' % name) for name in BRANDING_TEMPLATES
            })
            html_branding.add_resource(Javascript('app', minified=False))
            html_branding.add_resource(
                Javascript('app_templates', minified=False, is_template=True),
                templates=templates)
            html_branding.add_resource(
                Javascript('app_translations', minified=False, is_template=True),
                language=language)
            polls_template = html_branding.render_template('polls.tmpl', language=language)
            branding_content = html_branding.compressed(polls_template)
            solution_settings.polls_branding_hash = put_branding('Polls App', branding_content).id
            solution_settings.put()
