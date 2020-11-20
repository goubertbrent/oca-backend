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

from google.appengine.ext import ndb
from typing import List

from rogerthat.dal import parent_ndb_key
from rogerthat.models import NdbModel
from rogerthat.rpc import users
from solutions.common import SOLUTION_COMMON


class SolutionHint(NdbModel):
    tag = ndb.StringProperty(indexed=False)
    language = ndb.StringProperty(indexed=False)
    text = ndb.TextProperty()
    modules = ndb.StringProperty(repeated=True, indexed=False)  # type: List[str]

    @property
    def id(self):
        return self.key.id()

    @classmethod
    def create_key(cls, hint_id):
        return ndb.Key(cls, hint_id)


class SolutionHints(NdbModel):
    hint_ids = ndb.IntegerProperty(repeated=True, indexed=False)  # type: List[int]

    @classmethod
    def create_key(cls):
        return ndb.Key(cls, 'SolutionHints')


class SolutionHintSettings(NdbModel):
    do_not_show_again = ndb.IntegerProperty(repeated=True, indexed=False)  # type: List[int]

    @classmethod
    def create_key(cls, service_user):
        return ndb.Key(cls, service_user.email(), parent=parent_ndb_key(service_user, SOLUTION_COMMON))

    @property
    def service_user(self):
        return users.User(self.key.parent().id())
