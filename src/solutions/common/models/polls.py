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
from google.appengine.ext.ndb import polymodel
from mcfw.utils import Enum
from rogerthat.dal import parent_ndb_key
from rogerthat.models.common import NdbModel
from solutions.common import SOLUTION_COMMON


class QuestionTypeException(ValueError):
    pass


class QuestionChoicesException(ValueError):
    pass


class QuestionType(Enum):
    MULTIPLE_CHOICE = 1
    CHECKBOXES = 2
    SHORT_TEXT = 3
    LONG_TEXT = 4


class Question(polymodel.PolyModel):
    TYPE = None
    text = ndb.StringProperty(indexed=False)
    required = ndb.BooleanProperty(indexed=False, default=False)


class MultipleChoiceQuestion(Question):
    TYPE = QuestionType.MULTIPLE_CHOICE
    choices = ndb.StringProperty(repeated=True)


class CheckboxesQuestion(MultipleChoiceQuestion):
    TYPE = QuestionType.CHECKBOXES


class ShortTextQuestion(Question):
    TYPE = QuestionType.LONG_TEXT


class LongTextQuestion(Question):
    TYPE = QuestionType.LONG_TEXT


QUESTION_TYPE_MAPPING = {
    QuestionType.MULTIPLE_CHOICE: MultipleChoiceQuestion,
    QuestionType.CHECKBOXES: CheckboxesQuestion,
    QuestionType.SHORT_TEXT: ShortTextQuestion,
    QuestionType.LONG_TEXT: LongTextQuestion,
}


class PollStatus(Enum):
    PENDING = 1
    RUNNING = 2
    COMPLELTED = 3


def validate_question_choices(prop, value):
    if not isinstance(value, MultipleChoiceQuestion):
        return
    if len(value.choices) < 2:
        raise QuestionChoicesException('a qeustion should has at least two choices')


class Poll(polymodel.PolyModel):
    name = ndb.StringProperty(indexed=False)
    questions = ndb.LocalStructuredProperty(Question, repeated=True, validator=validate_question_choices)
    status = ndb.IntegerProperty(choices=PollStatus.all(), default=PollStatus.PENDING, indexed=True)
    created_on = ndb.DateTimeProperty(auto_now_add=True)
    updated_on = ndb.DateTimeProperty(auto_now=True)

    @classmethod
    def create_key(cls, service_user, id_=None):
        parent = parent_ndb_key(service_user, SOLUTION_COMMON)
        id_ = id_ or cls.allocate_ids(1)[0]
        return ndb.Key(cls, id_, parent=parent)

    @property
    def id(self):
        return self.key.id()


def validate_vote_question(prop, value):
    if not isinstance(value, MultipleChoiceQuestion):
        raise QuestionTypeException('a vote poll should only contain choice question type')
    validate_question_choices(prop, value)


class Vote(Poll):
    questions = ndb.LocalStructuredProperty(Question, repeated=True, validator=validate_vote_question)


class QuestionAnswer(NdbModel):
    question_id = ndb.IntegerProperty()
    value = ndb.StringProperty(indexed=False)


class PollAnswer(NdbModel):
    question_answers = ndb.StructuredProperty(QuestionAnswer, repeated=True)

    @classmethod
    def create_key(cls, service_user, poll_id):
        parent = Poll.create_key(service_user, poll_id)
        return ndb.Key(cls, cls.allocate_ids(1)[0], parent=parent)

    @classmethod
    def create(cls, service_user, poll_id, *question_answers):
        return PollAnswer(
            key=cls.create_key(service_user, poll_id),
            question_answers=question_answers)

    @classmethod
    def list_by_poll(cls, service_user, poll_id):
        parent = Poll.create_key(service_user, poll_id)
        return cls.query(ancestor=parent)


class PollRegister(NdbModel):
    created_on = ndb.DateTimeProperty(auto_now_add=True)
    updated_on = ndb.DateTimeProperty(auto_now=True)

    @classmethod
    def create_key(cls, app_user, poll_id):
        return ndb.Key(cls, app_user.email(), cls, poll_id)

    @classmethod
    def create(cls, app_user, poll_id):
        return cls(key=cls.create_key(app_user, poll_id)).put()

    @classmethod
    def exists(cls, app_user, poll_id):
        return bool(cls.create_key(app_user, poll_id).get())
