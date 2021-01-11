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

from google.appengine.ext import ndb
from typing import List, Tuple

from mcfw.utils import Enum
from rogerthat.models import NdbModel, ServiceIdentity
from rogerthat.models.settings import ServiceInfo
from rogerthat.rpc import users


class QuestionStatus(Enum):
    NEW = 0
    REACTION_RECEIVED = 3
    WAITING_FOR_REPLY = 7
    RESOLVED = 10


class Question(NdbModel):
    author = ndb.UserProperty()
    timestamp = ndb.IntegerProperty()
    update_date = ndb.DateTimeProperty(auto_now=True)
    # date when the user who asked the question last sent a reply
    last_reply_date = ndb.DateTimeProperty(auto_now_add=True)
    title = ndb.StringProperty()
    description = ndb.TextProperty()
    modules = ndb.StringProperty(repeated=True)  # type: List[str]
    status = ndb.IntegerProperty(choices=QuestionStatus.all(), default=QuestionStatus.NEW)
    language = ndb.StringProperty()

    STATUS_STRINGS = {
        QuestionStatus.NEW: 'New',
        QuestionStatus.WAITING_FOR_REPLY: 'Waiting for reply',
        QuestionStatus.REACTION_RECEIVED: 'Reaction received',
        QuestionStatus.RESOLVED: 'Resolved',
    }

    @property
    def id(self):
        return self.key.id()

    @property
    def module_list(self):
        return ','.join(self.modules)

    @property
    def full_date_str(self):
        return time.strftime('%d %b %Y %H:%M:%S', time.gmtime(self.timestamp))

    @property
    def status_str(self):
        return self.STATUS_STRINGS.get(self.status, self.status)

    @classmethod
    def create_key(cls, question_id):
        return ndb.Key(cls, question_id)

    @classmethod
    def list_latest(cls):
        return cls.query().order(-cls.last_reply_date)

    @classmethod
    def get_my_questions(cls, author, count, cursor):
        # type: (users.User, int, ndb.Cursor) -> Tuple[List[Question], ndb.Cursor, bool]
        return cls.query() \
            .filter(cls.author == author) \
            .order(-cls.last_reply_date) \
            .fetch_page(count, start_cursor=cursor)

    @staticmethod
    def label(module):
        return ' '.join([x.capitalize() for x in module.split('_')])

    @property
    def modules_labels(self):
        return sorted([(k, self.label(k)) for k in self.modules])

    @property
    def author_role(self):
        return QuestionReply.ROLE_USER

    def get_author_name(self):
        info = ServiceInfo.create_key(self.author, ServiceIdentity.DEFAULT).get()
        return info.name if info else self.author.email()


class QuestionReply(NdbModel):
    ROLE_USER = 0
    ROLE_STAFF = 1

    author = ndb.UserProperty()
    author_role = ndb.IntegerProperty(default=0)
    author_name = ndb.StringProperty(default="")
    timestamp = ndb.IntegerProperty()
    description = ndb.TextProperty()

    @property
    def id(self):
        return self.key.id()

    @property
    def full_date_str(self):
        return time.strftime('%d %b %Y %H:%M:%S', time.gmtime(self.timestamp))

    @classmethod
    def create_key(cls, reply_id, question_key):
        return ndb.Key(cls, reply_id, parent=question_key)

    def get_author_name(self):
        if self.author_role == self.ROLE_USER:
            info = ServiceInfo.create_key(self.author, ServiceIdentity.DEFAULT).get()
            return info.name if info else self.author.email()
        else:
            return self.author_name

    @classmethod
    def list_by_question(cls, question_key):
        return cls.query(ancestor=question_key).order(cls.timestamp)
