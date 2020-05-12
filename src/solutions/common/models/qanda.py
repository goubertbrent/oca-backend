# -*- coding: utf-8 -*-
# Copyright 2020 Green Valley Belgium NV
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
# @@license_version:1.7@@

import time

from google.appengine.ext import db

from solutions.common.dal import get_solution_settings


class Question(db.Model):
    author = db.UserProperty()
    timestamp = db.IntegerProperty()
    title = db.StringProperty()
    description = db.TextProperty()
    modules = db.StringListProperty()
    visible = db.BooleanProperty(default=False)
    answered = db.BooleanProperty(default=False)
    language = db.StringProperty()
    team_id = db.IntegerProperty(indexed=True)

    @property
    def id(self):
        return self.key().id()

    @property
    def module_list(self):
        return ",".join(self.modules)

    @property
    def full_date_str(self):
        return time.strftime('%d %b %Y %H:%M:%S', time.gmtime(self.timestamp))

    def all_replies(self):
        return QuestionReply.all().ancestor(self).order('timestamp')

    def replies(self, include_invisible):
        if include_invisible:
            return self.all_replies()
        else:
            return QuestionReply.all().ancestor(self).filter('visible =', True).order('timestamp')

    @staticmethod
    def get_recent(count, cursor, language=None):
        qry = Question.all().with_cursor(cursor).filter('visible =', True).order('-timestamp')
        if language:
            qry.filter('language', language)
        questions = qry.fetch(count)
        return unicode(qry.cursor()), questions

    @staticmethod
    def get_my_questions(author, count, cursor):
        qry = Question.all().with_cursor(cursor).filter("author =", author).order('-timestamp')
        questions = qry.fetch(count)
        return unicode(qry.cursor()), questions

    @staticmethod
    def label(module):
        return ' '.join([x.capitalize() for x in module.split('_')])

    @property
    def modules_labels(self):
        return sorted([(k, Question.label(k)) for k in self.modules])

    @property
    def author_role(self):
        return QuestionReply.ROLE_USER

    def get_author_name(self):
        sln_settings = get_solution_settings(self.author)
        if sln_settings:
            return sln_settings.name
        else:
            return self.author.email()


class QuestionReply(db.Model):
    ROLE_USER = 0
    ROLE_STAFF = 1

    author = db.UserProperty()
    author_role = db.IntegerProperty(default=0)
    author_name = db.StringProperty(default="")
    timestamp = db.IntegerProperty()
    description = db.TextProperty()
    visible = db.BooleanProperty(default=False)

    @property
    def id(self):
        return self.key().id()

    @property
    def full_date_str(self):
        return time.strftime('%d %b %Y %H:%M:%S', time.gmtime(self.timestamp))

    @property
    def question_key(self):
        return self.parent_key()

    def question(self):
        return Question.get(self.parent_key())

    def get_author_name(self):
        if self.author_role == QuestionReply.ROLE_USER:
            sln_settings = get_solution_settings(self.author)
            if sln_settings:
                return sln_settings.name
            else:
                return self.author.email()
        else:
            return self.author_name
