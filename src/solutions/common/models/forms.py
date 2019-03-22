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

from random import randint

from google.appengine.ext import ndb

from rogerthat.bizz.gcs import get_serving_url
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


# TODO: delete when deleting service

class FormSubmission(NdbModel):
    form_id = ndb.IntegerProperty()
    user = ndb.StringProperty()
    sections = ndb.JsonProperty()
    submitted_date = ndb.DateTimeProperty(auto_now_add=True)
    version = ndb.IntegerProperty(default=0)

    @classmethod
    def list(cls, form_id):
        return cls.query(cls.form_id == form_id).order(-cls.submitted_date)

    @classmethod
    def list_by_user(cls, form_id, user):
        return cls.query(cls.form_id == form_id).filter(cls.user == user)


class UploadedFile(NdbModel):
    reference = ndb.KeyProperty()
    content_type = ndb.StringProperty(indexed=False)
    cloudstorage_path = ndb.StringProperty(indexed=False)
    created_on = ndb.DateTimeProperty(auto_now_add=True)

    @property
    def id(self):
        return self.key.id()

    @property
    def url(self):
        return get_serving_url(self.cloudstorage_path)

    @classmethod
    def create_key(cls, service_user, form_id):
        return ndb.Key(cls, form_id, parent=parent_ndb_key(service_user, SOLUTION_COMMON))

    @classmethod
    def list_by_reference(cls, key):
        # type: (ndb.Key) -> list[UploadedFile]
        return cls.query(cls.reference == key)

    @classmethod
    def list_by_user(cls, service_user):
        return cls.query(ancestor=parent_ndb_key(service_user, SOLUTION_COMMON))


class FormStatisticsShard(NdbModel):
    SHARD_KEY_TEMPLATE = '%d-%d'
    count = ndb.IntegerProperty(default=0)
    data = ndb.JsonProperty(compressed=True)

    @classmethod
    def create_key(cls, shard_key):
        return ndb.Key(cls, shard_key)


class FormStatisticsShardConfig(NdbModel):
    shard_count = ndb.IntegerProperty(default=5)  # increase as needed. 5 => ~5 writes (form submissions) / sec

    # add a 'full_shards' (list of shard indexes) property should the problem of a shard being > 1MB ever arise

    def get_random_shard(self):
        return randint(0, self.shard_count - 1)

    @classmethod
    def create_key(cls, form_id):
        return ndb.Key(cls, form_id)

    @classmethod
    def get_all_keys(cls, form_id):
        key = cls.create_key(form_id)
        config = key.get()
        if not config:
            config = cls(key=key)
            config.put()
        shard_key_strings = [FormStatisticsShard.SHARD_KEY_TEMPLATE % (form_id, i) for i in range(config.shard_count)]
        return [FormStatisticsShard.create_key(shard_key) for shard_key in shard_key_strings]
