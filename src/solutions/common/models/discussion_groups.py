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

from google.appengine.ext import db, ndb
from typing import List

from rogerthat.dal import parent_key, parent_ndb_key
from rogerthat.models import KeyValueProperty, NdbModel
from solutions.common import SOLUTION_COMMON


# TODO: remove after migration
class SolutionDiscussionGroup(db.Model):
    topic = db.StringProperty()
    description = db.TextProperty()
    members = KeyValueProperty()
    message_key = db.StringProperty(indexed=False)
    creation_timestamp = db.IntegerProperty(indexed=False)

    @property
    def id(self):
        return self.key().id()

    @staticmethod
    def _create_parent_key(service_user):
        return parent_key(service_user, SOLUTION_COMMON)

    @classmethod
    def create_key(cls, service_user, discussion_group_id):
        return db.Key.from_path(cls.kind(), discussion_group_id, parent=cls._create_parent_key(service_user))

    @classmethod
    def list(cls, service_user, order_by=None):
        qry = cls.all().ancestor(cls._create_parent_key(service_user))
        if order_by:
            qry = qry.order(order_by)
        return qry


class DiscussionGroup(NdbModel):
    topic = ndb.StringProperty()
    description = ndb.TextProperty()
    members = ndb.StringProperty(repeated=True)  # type: List[str]
    message_key = ndb.StringProperty(indexed=False)
    creation_timestamp = ndb.IntegerProperty(indexed=False)

    @property
    def id(self):
        return self.key.id()

    @staticmethod
    def _create_parent_key(service_user):
        return parent_ndb_key(service_user, SOLUTION_COMMON)

    @classmethod
    def create_key(cls, service_user, discussion_group_id):
        return ndb.Key(cls, discussion_group_id, parent=cls._create_parent_key(service_user))

    @classmethod
    def list(cls, service_user):
        return cls.query(ancestor=cls._create_parent_key(service_user))

    @classmethod
    def list_ordered(cls, service_user):
        return cls.list(service_user).order(cls.topic)
