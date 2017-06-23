# -*- coding: utf-8 -*-
# Copyright 2017 Mobicage NV
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
# @@license_version:1.2@@

from datetime import datetime
import pytz

from rogerthat.rpc import users
from rogerthat.to import ReturnStatusTO
from rogerthat.utils import today
from mcfw.properties import unicode_property, long_property, typed_property, bool_property
from solutions.common.bizz import _format_time, _format_date
from solutions.common.dal import get_solution_settings
from solutions.common.models.qanda import QuestionReply


class QuestionReplyTO(object):
    id = long_property('1')
    author_email = unicode_property('2')
    author_name = unicode_property('3')
    author_role = long_property('4')
    timestamp = long_property('5')
    timestamp_str = unicode_property('6')
    description = unicode_property('7')
    visible = bool_property('8')

    @staticmethod
    def fromModel(model, author_name, sln_settings):
        to = QuestionReplyTO()
        to.id = model.id
        to.author_email = model.author.email()
        to.author_name = author_name
        to.author_role = model.author_role
        to.timestamp = model.timestamp

        today_ = today()
        timestamp_day = model.timestamp - (model.timestamp % (3600 * 24))
        date_sent = datetime.fromtimestamp(model.timestamp, pytz.timezone(sln_settings.timezone))
        time_ = _format_time(sln_settings.main_language, date_sent)
        if today_ == timestamp_day:
            to.timestamp_str = unicode(time_)
        else:
            to.timestamp_str = unicode("%s %s" % (_format_date(sln_settings.main_language, date_sent), time_))

        to.description = model.description
        to.visible = model.visible
        return to

class ModuleTO(object):
    key = unicode_property('1')
    label = unicode_property('2')
    is_default = bool_property('3', default=False)

    @staticmethod
    def fromArray(obj):
        m = ModuleTO()
        m.key = obj[0]
        m.label = obj[1]
        return m

class QuestionTO(object):
    id = long_property('1')
    author_email = unicode_property('2')
    author_name = unicode_property('3')
    author_role = long_property('4')
    timestamp = long_property('5')
    timestamp_str = unicode_property('6')
    title = unicode_property('7')
    description = unicode_property('8')
    answers = typed_property('9', QuestionReplyTO, True)
    modules = typed_property('10', ModuleTO, True)
    visible = bool_property('11')

    @staticmethod
    def fromModel(model, incude_invisible, sln_settings):
        to = QuestionTO()
        to.id = model.id
        to.author_email = model.author.email()
        to.author_role = model.author_role
        to.timestamp = model.timestamp

        today_ = today()
        timestamp_day = model.timestamp - (model.timestamp % (3600 * 24))
        date_sent = datetime.fromtimestamp(model.timestamp, pytz.timezone(sln_settings.timezone))
        time_ = _format_time(sln_settings.main_language, date_sent)
        if today_ == timestamp_day:
            to.timestamp_str = unicode(time_)
        else:
            to.timestamp_str = unicode("%s %s" % (_format_date(sln_settings.main_language, date_sent), time_))

        to.title = model.title
        to.description = model.description

        emails = set()
        emails.add(to.author_email)
        replies = []
        name_dict = {}
        for r in model.replies(incude_invisible):
            replies.append(r)
            if r.author_role == QuestionReply.ROLE_USER:
                emails.add(r.author.email())

        for email in emails:
            tmp_sln_settings = get_solution_settings(users.User(email))
            if tmp_sln_settings:
                name_dict[email] = tmp_sln_settings.name
            else:
                name_dict[email] = email

        to.author_name = name_dict[to.author_email]

        to.answers = list()
        for r in replies:
            if r.author_role == QuestionReply.ROLE_USER:
                to.answers.append(QuestionReplyTO.fromModel(r, name_dict[r.author.email()], sln_settings))
            else:
                to.answers.append(QuestionReplyTO.fromModel(r, r.author_name, sln_settings))
        to.modules = list()
        for ml in model.modules_labels:
            to.modules.append(ModuleTO.fromArray(ml))
        to.visible = model.visible
        return to


class QuestionsWithCursorReturnStatusTO(ReturnStatusTO):
    questions = typed_property('51', QuestionTO, True)
    cursor = unicode_property('52')

    @classmethod
    def create(cls, success=True, errormsg=None, questions=[], cursor=None):
        r = super(QuestionsWithCursorReturnStatusTO, cls).create(success, errormsg)
        r.questions = questions
        r.cursor = cursor
        return r
