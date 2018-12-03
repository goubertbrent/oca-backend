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

from mcfw.consts import MISSING
from mcfw.properties import bool_property, long_property, unicode_property, unicode_list_property, typed_property
from rogerthat.to import PaginatedResultTO, TO
from rogerthat.utils import get_epoch_from_datetime
from solutions.common.models.polls import Vote, PollStatus, MultipleChoiceQuestion, QuestionType, \
    QUESTION_TYPE_MAPPING


class QuestionTO(TO):
    type = long_property('1')
    text = unicode_property('2')
    choices = unicode_list_property('3')
    required = bool_property('4')

    @classmethod
    def from_model(cls, question):
        to = cls.from_dict(question.to_dict())
        to.type = question.TYPE
        return to

    def to_model(self):
        cls = QUESTION_TYPE_MAPPING[self.type]
        data = self.to_dict()
        for prop in data.keys():
            if not hasattr(cls, prop):
                del data[prop]
        return cls(**data)


class PollTO(TO):
    id = long_property('1')
    name = unicode_property('2')
    questions = typed_property('3', QuestionTO, True)
    status = long_property('4', default=PollStatus.PENDING)
    created_on = long_property('5')
    updated_on = long_property('6')
    is_vote = bool_property('7', default=False)

    @classmethod
    def from_model(cls, poll):
        to = cls()
        to.id = poll.id
        to.name = poll.name
        to.status = poll.status
        if poll.questions is MISSING:
            poll.questions = []
        to.questions = [QuestionTO.from_model(q) for q in poll.questions]
        to.created_on = get_epoch_from_datetime(poll.created_on)
        to.updated_on = get_epoch_from_datetime(poll.updated_on)
        to.is_vote = isinstance(poll, Vote)
        return to


class PollsListTO(PaginatedResultTO):
    results = typed_property('results', PollTO, True)

    def __init__(self, polls, cursor, has_more):
        super(PollsListTO, self).__init__(cursor=cursor, more=has_more)
        self.results = map(PollTO.from_model, polls)


class QuestionAnswerTO(TO):
    question_id = long_property('1')
    value = unicode_property('2')

    @classmethod
    def from_model(cls, question_answer):
        return cls(question_id=question_answer.question_id, value=question_answer.value)


class PollAnswerTO(TO):
    question_answers = typed_property('1', QuestionAnswerTO, True)

    @classmethod
    def from_model(cls, poll_answer):
        return cls(
            question_answers=map(QuestionAnswerTO.from_model, poll_answer.question_answers)
        )


class PollAnswerResultTO(PaginatedResultTO):
    results = typed_property('results', PollAnswerTO, True)


class ChoiceCountTO(TO):
    choice = unicode_property('1')
    count = long_property('2')


class QuestionCountResultTO(TO):
    question_id = long_property('1')
    counts = typed_property('2', ChoiceCountTO, True)


class FlowQuestionTO(QuestionTO):
    id = long_property('id')
    next = typed_property('next', QuestionTO, False)

    @property
    def is_first(self):
        return id == 0


class FlowPollTO(PollTO):
    flow_questions = typed_property('3', FlowQuestionTO, True)

    @classmethod
    def from_model(cls, poll):
        to = super(FlowPollTO, cls).from_model(poll)
        to.flow_questions = []
        for i in range(0, len(poll.questions)):
            flow_question_to = FlowQuestionTO.from_model(poll.questions[i])
            flow_question_to.id = i
            to.flow_questions.append(flow_question_to)
        return to
