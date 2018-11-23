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

    @classmethod
    def from_model(cls, question):
        to = cls.from_dict(question.to_dict())
        to.type = question.TYPE
        return to

    def to_model(self):
        cls = QUESTION_TYPE_MAPPING[self.type]
        data = self.to_dict()
        data.pop('type')
        return cls(**data)


class MultipleChoiceQuestionTO(QuestionTO):
    choices = unicode_list_property('3')


class CheckboxesQuestionTO(MultipleChoiceQuestionTO):
    pass


class ShortTextQuestionTO(QuestionTO):
    pass


class LongTextQuestionTO(QuestionTO):
    pass


QUESTION_TYPE_TO_MAPPING = {
    QuestionType.MULTIPLE_CHOICE: MultipleChoiceQuestionTO,
    QuestionType.CHECKBOXES: CheckboxesQuestionTO,
    QuestionType.SHORT_TEXT: ShortTextQuestionTO,
    QuestionType.LONG_TEXT: LongTextQuestionTO,
}


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
        to.questions = [QUESTION_TYPE_TO_MAPPING[q.TYPE].from_model(q) for q in poll.questions]
        to.created_on = get_epoch_from_datetime(poll.created_on)
        to.updated_on = get_epoch_from_datetime(poll.updated_on)
        to.is_vote = isinstance(poll, Vote)
        return to


class PollsListTO(PaginatedResultTO):
    results = typed_property('results', PollTO, True)

    def __init__(self, polls, cursor, has_more):
        super(PollsListTO, self).__init__(cursor=cursor, more=has_more)
        self.results = map(PollTO.from_model, polls)
