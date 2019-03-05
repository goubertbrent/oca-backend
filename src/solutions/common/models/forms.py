# -*- coding: utf-8 -*-
# Copyright 2019 Mobicage NV
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
# @@license_version:1.4@@
from __future__ import unicode_literals

from google.appengine.ext import ndb

from rogerthat.dal import parent_ndb_key
from rogerthat.models import NdbModel
from rogerthat.rpc import users
from solutions import SOLUTION_COMMON


class FormTombola(NdbModel):
    winner_message = ndb.StringProperty(indexed=False)
    winner_count = ndb.IntegerProperty(default=1)


class OcaForm(NdbModel):
    title = ndb.StringProperty(indexed=False)  # Copy from Form.title
    icon = ndb.StringProperty(indexed=False, default='fa-list')
    visible = ndb.BooleanProperty(default=False)
    visible_until = ndb.DateTimeProperty()
    version = ndb.IntegerProperty()
    finished = ndb.BooleanProperty(default=False)
    tombola = ndb.StructuredProperty(FormTombola, default=None)  # type: FormTombola

    @property
    def id(self):
        return self.key.id()

    @property
    def service_user(self):
        return users.User(self.key.parent().id())

    @classmethod
    def create_key(cls, form_id, service_user):
        return ndb.Key(cls, form_id, parent=parent_ndb_key(service_user, SOLUTION_COMMON))

    @classmethod
    def list_by_user(cls, service_user):
        return cls.query(ancestor=parent_ndb_key(service_user, SOLUTION_COMMON))

    @classmethod
    def list_between_dates(cls, start_date, end_date):
        return cls.query(cls.visible_until < end_date).filter(cls.visible_until > start_date)


class TombolaWinner(NdbModel):
    form_id = ndb.IntegerProperty()
    user = ndb.StringProperty()

    @property
    def id(self):
        return self.key.id()

    @property
    def service_user(self):
        return users.User(self.key.parent().id())

    @classmethod
    def create_key(cls, id, service_user):
        return ndb.Key(cls, id, parent=parent_ndb_key(service_user, SOLUTION_COMMON))

    @classmethod
    def list_by_form_id(cls, form_id):
        return cls.query(cls.form_id == form_id)
