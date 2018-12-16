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
from mcfw.utils import Enum
from rogerthat.dal import parent_ndb_key
from rogerthat.models.common import NdbModel
from solutions.common import SOLUTION_COMMON


class QuestionChoicesException(ValueError):
    pass


class AnswerType(Enum):
    MULTIPLE_CHOICE = 1
    CHECKBOXES = 2


class Choice(NdbModel):
    text = ndb.StringProperty(indexed=False)
    count = ndb.IntegerProperty(indexed=False)


class Question(NdbModel):
    answer_type = ndb.IntegerProperty(indexed=False, choices=AnswerType.all())
    text = ndb.StringProperty(indexed=False)
    choices = ndb.LocalStructuredProperty(Choice, repeated=True)
    optional = ndb.BooleanProperty(indexed=False, default=False)


class PollStatus(Enum):
    PENDING = 1
    RUNNING = 2
    COMPLELTED = 3


def validate_question_choices(prop, value):
    if not isinstance(value, Question):
        return
    if len(value.choices) < 2:
        raise QuestionChoicesException('a question should has at least two choices')


class Poll(NdbModel):
    name = ndb.StringProperty(indexed=False)
    questions = ndb.LocalStructuredProperty(Question, repeated=True, validator=validate_question_choices)
    status = ndb.IntegerProperty(choices=PollStatus.all(), default=PollStatus.PENDING, indexed=True)
    ends_on = ndb.DateTimeProperty()
    created_on = ndb.DateTimeProperty(auto_now_add=True)
    updated_on = ndb.DateTimeProperty(auto_now=True)

    @classmethod
    def create_key(cls, service_user, id_):
        parent = parent_ndb_key(service_user, SOLUTION_COMMON)
        return ndb.Key(cls, id_, parent=parent)

    @classmethod
    def create(cls, service_user):
        return cls(parent=parent_ndb_key(service_user, SOLUTION_COMMON))

    @property
    def id(self):
        return self.key.id()


class PollQuestionAnswer(NdbModel):
    question_id = ndb.IntegerProperty(indexed=False)
    values = ndb.StringProperty(repeated=True)


class PollAnswer(NdbModel):
    poll_id = ndb.IntegerProperty(indexed=True)
    question_answers = ndb.LocalStructuredProperty(PollQuestionAnswer, repeated=True)
    created_on = ndb.DateTimeProperty(auto_now_add=True)
    notify_result = ndb.BooleanProperty(default=False)

    @classmethod
    def create(cls, app_user, poll_id, values, notify_result=False):
        question_answers = []
        for i in range(0, len(values)):
            question_answers.append(PollQuestionAnswer(question_id=i, values=values[i]))

        return PollAnswer(
            parent=parent_ndb_key(app_user, SOLUTION_COMMON),
            poll_id=poll_id,
            question_answers=question_answers,
            notify_result=notify_result)

    @classmethod
    def get_by_poll(cls, app_user, poll_id):
        parent = parent_ndb_key(app_user, SOLUTION_COMMON)
        return cls.query(ancestor=parent).filter(cls.poll_id == poll_id).get()

    @classmethod
    def list_by_app_user(cls, app_user):
        parent = parent_ndb_key(app_user, SOLUTION_COMMON)
        return cls.query(ancestor=parent)

    @classmethod
    def list_by_poll(cls, poll_id):
        return cls.query().filter(cls.poll_id == poll_id)
