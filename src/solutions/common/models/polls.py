from google.appengine.ext import ndb
from google.appengine.ext.ndb import polymodel
from mcfw.utils import Enum
from rogerthat.dal import parent_ndb_key
from rogerthat.models.common import NdbModel
from solutions.common import SOLUTION_COMMON


class QuestionTypeException(ValueError):
    pass


class QuestionType(Enum):
    MULTIPLE_CHOICE = 1
    CHECKBOXES = 2
    SHORT_TEXT = 3
    LONG_TEXT = 4


class Question(polymodel.PolyModel):
    TYPE = None
    text = ndb.StringProperty(indexed=False)


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


class Poll(polymodel.PolyModel):
    name = ndb.StringProperty(indexed=False)
    questions = ndb.LocalStructuredProperty(Question, repeated=True)
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


class Vote(Poll):
    questions = ndb.LocalStructuredProperty(Question, repeated=True, validator=validate_vote_question)


class Answer(NdbModel):
    values = ndb.StringProperty(repeated=True)

    @classmethod
    def create_key(cls, question_id):
        parent = ndb.Key(Question, question_id)
        return ndb.Key(cls, cls.allocate_ids(1)[0], parent=parent)

    @classmethod
    def create(cls, question_id, *values):
        return Answer(key=cls.create_key(question_id), values=values)
