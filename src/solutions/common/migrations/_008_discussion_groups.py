# -*- coding: utf-8 -*-
# Copyright 2020 Green Valley NV
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
# @@license_version:1.5@@

from google.appengine.ext import db, ndb

from rogerthat.dal import parent_key
from rogerthat.models import KeyValueProperty
from solutions.common import SOLUTION_COMMON
from solutions.common.models.discussion_groups import DiscussionGroup


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


def migrate(dry_run=True):
    to_put = []
    to_delete = []
    for discussion_group in SolutionDiscussionGroup.all():  # type: SolutionDiscussionGroup
        ndb_discussion_group = DiscussionGroup(key=ndb.Key.from_old_key(discussion_group.key))
        ndb_discussion_group.topic = discussion_group.topic
        ndb_discussion_group.description = discussion_group.description
        ndb_discussion_group.message_key = discussion_group.message_key
        ndb_discussion_group.creation_timestamp = discussion_group.creation_timestamp
        ndb_discussion_group.members = list(discussion_group.members['members'])
        if not dry_run:
            discussion_group.members.clear()  # clears the buckets
        to_put.append(ndb_discussion_group)
        to_delete.append(discussion_group.key())
    if dry_run:
        return {'to put': to_put, 'to delete': to_delete}
    ndb.put_multi(to_put)
    db.delete(to_delete)
