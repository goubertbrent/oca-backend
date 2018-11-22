from mcfw.consts import MISSING
from mcfw.properties import bool_property, long_property, unicode_property, unicode_list_property, typed_property
from rogerthat.to import PaginatedResultTO, TO
from rogerthat.utils import get_epoch_from_datetime
from solutions.common.models.polls import Vote, PollStatus, MultipleChoiceQuestion, QUESTION_TYPE_MAPPING


class QuestionTO(TO):
    type = long_property('1')
    text = unicode_property('2')

    @classmethod
    def from_model(cls, question):
        return cls.from_dict(question.to_dict())

    def to_model(self):
        cls = QUESTION_TYPE_MAPPING[self.type]
        return cls(**self.to_dict())


class MultipleChoiceQuestionTO(QuestionTO):
    choices = unicode_list_property('3')


class PollTO(TO):
    id = long_property('1')
    name = unicode_property('2')
    questions = typed_property('3', QuestionTO, True)
    status = long_property('4')
    created_on = long_property('5')
    updated_on = long_property('6')
    is_vote = bool_property('7')

    @classmethod
    def from_model(cls, poll):
        to = cls()
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
