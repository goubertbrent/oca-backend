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
from solutions.common.models.polls import Choice, Question, PollStatus


class ChoiceTO(TO):
    text = unicode_property('1')
    count = long_property('2', default=0)

    def to_model(self):
        return Choice(text=self.text, count=self.count)


class QuestionTO(TO):
    answer_type = long_property('1')
    text = unicode_property('2')
    choices = typed_property('3', ChoiceTO, True)
    optional = bool_property('4')

    @classmethod
    def from_model(cls, question):
        to = cls()
        to.answer_type = question.answer_type
        to.text = question.text
        to.choices = [ChoiceTO.from_dict(choice.to_dict()) for choice in question.choices]
        to.optional = question.optional
        return to

    def to_model(self):
        return Question(
            answer_type=self.answer_type,
            text=self.text,
            optional=self.optional,
            choices=[choice.to_model() for choice in self.choices]
        )


class PollTO(TO):
    id = long_property('1')
    name = unicode_property('2')
    questions = typed_property('3', QuestionTO, True)
    status = long_property('4', default=PollStatus.PENDING)
    ends_on = long_property('5')
    created_on = long_property('6')
    updated_on = long_property('7')

    @classmethod
    def from_model(cls, poll):
        to = cls()
        to.id = poll.id
        to.name = poll.name
        to.status = poll.status
        if poll.questions is MISSING:
            poll.questions = []
        to.questions = [QuestionTO.from_model(q) for q in poll.questions]
        to.ends_on = get_epoch_from_datetime(poll.created_on)
        to.created_on = get_epoch_from_datetime(poll.created_on)
        to.updated_on = get_epoch_from_datetime(poll.updated_on)
        return to


class PollsListTO(PaginatedResultTO):
    results = typed_property('results', PollTO, True)

    def __init__(self, polls, cursor, has_more):
        super(PollsListTO, self).__init__(cursor=cursor, more=has_more)
        self.results = map(PollTO.from_model, polls)


class UserPollTO(PollTO):
    answered = bool_property('answered')

    @classmethod
    def from_model(cls, poll, answered=False):
        to = super(UserPollTO, cls).from_model(poll)
        to.answered = answered
        return to
