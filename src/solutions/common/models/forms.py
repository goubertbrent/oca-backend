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

from __future__ import unicode_literals

from random import randint

import cloudstorage
from cloudstorage.storage_api import _StorageApi
from google.appengine.ext import ndb
from typing import List

from mcfw.properties import typed_property, long_property, unicode_property, unicode_list_property
from mcfw.utils import Enum
from rogerthat.bizz.gcs import get_serving_url
from rogerthat.dal import parent_ndb_key
from rogerthat.models import NdbModel
from rogerthat.models.news import MediaType
from rogerthat.rpc import users
from rogerthat.to import TO
from solutions.common import SOLUTION_COMMON


class FormTombola(NdbModel):
    winner_message = ndb.StringProperty(indexed=False)
    winner_count = ndb.IntegerProperty(default=1)


class CompletedFormStepType(Enum):
    CONTENT = 'content'
    TEST = 'test'
    SETTINGS = 'settings'
    ACTION = 'action'
    LAUNCH = 'launch'
    INTEGRATIONS = 'integrations'


class CompletedFormStep(NdbModel):
    step_id = ndb.StringProperty(choices=CompletedFormStepType.all())


class FormIntegrationProvider(Enum):
    EMAIL = 'email'
    GREEN_VALLEY = 'green_valley'
    TOPDESK = 'topdesk'


ALL_FORM_INTEGRATION_PROVIDERS = FormIntegrationProvider.all()


class FormIntegration(NdbModel):
    provider = ndb.StringProperty(choices=FormIntegrationProvider.all())
    enabled = ndb.BooleanProperty(default=True)
    # Stores a mapping between component sections/fields and integration its fields
    configuration = ndb.JsonProperty()


class EmailGroupTO(TO):
    id = long_property('id')
    name = unicode_property('name')
    emails = unicode_list_property('emails')


class EmailComponentMappingTO(TO):
    section_id = unicode_property('section_id')
    component_id = unicode_property('component_id')
    component_value = unicode_property('component_value')
    group_id = long_property('group_id')


class EmailIntegrationFormConfigTO(TO):
    email_groups = typed_property('email_groups', EmailGroupTO, True)  # type: List[EmailGroupTO]
    default_group = long_property('default_group', default=-1)
    mapping = typed_property('mapping', EmailComponentMappingTO, True)  # type: List[EmailComponentMappingTO]


class OcaForm(NdbModel):
    title = ndb.StringProperty(indexed=False)  # Copy from Form.title
    icon = ndb.StringProperty(indexed=False, default='fa-list')
    visible = ndb.BooleanProperty(default=False)
    visible_until = ndb.DateTimeProperty()
    version = ndb.IntegerProperty()
    finished = ndb.BooleanProperty(default=False)
    tombola = ndb.StructuredProperty(FormTombola, default=None)  # type: FormTombola
    steps = ndb.LocalStructuredProperty(CompletedFormStep, repeated=True)
    integrations = ndb.StructuredProperty(FormIntegration, repeated=True)  # type: List[FormIntegration]

    @property
    def id(self):
        return self.key.id()

    @property
    def service_user(self):
        return users.User(self.key.parent().id())

    @property
    def has_integration(self):
        return any(integration.enabled for integration in self.integrations)

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
    def create_key(cls, id, service_user):  # @ReservedAssignment
        return ndb.Key(cls, id, parent=parent_ndb_key(service_user, SOLUTION_COMMON))

    @classmethod
    def list_by_form_id(cls, form_id):
        return cls.query(cls.form_id == form_id)


# TODO: delete when deleting service

class FormSubmission(NdbModel):
    form_id = ndb.IntegerProperty()
    user = ndb.StringProperty(indexed=False)
    sections = ndb.JsonProperty()
    submitted_date = ndb.DateTimeProperty(auto_now_add=True)
    version = ndb.IntegerProperty(default=0, indexed=False)
    statistics_shard_id = ndb.StringProperty(indexed=False)
    test = ndb.BooleanProperty(default=False)
    external_reference = ndb.StringProperty()
    pending_integration_submits = ndb.StringProperty(repeated=True, indexed=False)

    @property
    def id(self):
        return self.key.id()

    @classmethod
    def create_key(cls, submission_id):
        return ndb.Key(cls, submission_id)

    @classmethod
    def list(cls, form_id):
        return cls.query(cls.form_id == form_id).order(-cls.submitted_date)

    @classmethod
    def list_by_user(cls, form_id, user):
        return cls.query(cls.form_id == form_id).filter(cls.user == user)


class ScaledImage(NdbModel):
    cloudstorage_path = ndb.TextProperty(required=True)
    width = ndb.IntegerProperty(required=True, indexed=False)
    height = ndb.IntegerProperty(required=True, indexed=False)
    size = ndb.IntegerProperty(required=True, indexed=False)
    content_type = ndb.TextProperty(required=True)

    @property
    def url(self):
        return _StorageApi.api_url + self.cloudstorage_path


class UploadedFile(NdbModel):
    reference = ndb.KeyProperty()
    content_type = ndb.StringProperty(indexed=False)
    title = ndb.StringProperty(indexed=False)  # optional user-provided file title
    cloudstorage_path = ndb.StringProperty()
    created_on = ndb.DateTimeProperty(auto_now_add=True)
    size = ndb.IntegerProperty(indexed=False)
    type = ndb.StringProperty(choices=MediaType.all())
    # contains scaled down versions of an image file, and thumbnails
    scaled_images = ndb.StructuredProperty(ScaledImage, repeated=True, indexed=False)  # type: List[ScaledImage]

    @property
    def id(self):
        return self.key.id()

    @property
    def original_url(self):
        return get_serving_url(self.cloudstorage_path)

    @property
    def url(self):
        for scaled in self.scaled_images:
            if scaled.width >= 1500 or scaled.height >= 1500:
                return scaled.url
        return self.original_url

    @property
    def thumbnail_url(self):
        for scaled in self.scaled_images:
            if scaled.width <= 500 and scaled.width <= 500:
                return scaled.url

    @classmethod
    def create_key_service(cls, service_user, file_id):
        return ndb.Key(cls, file_id, parent=parent_ndb_key(service_user, SOLUTION_COMMON))

    @classmethod
    def create_key_poi(cls, poi_key, file_id):
        # type: (ndb.Key, int) -> ndb.Key
        return ndb.Key(cls, file_id, parent=poi_key)

    @classmethod
    def list_by_reference(cls, key):
        # type: (ndb.Key) -> List[UploadedFile]
        return cls.query(cls.reference == key)

    @classmethod
    def list_by_poi(cls, poi_key):
        # type: (ndb.Key) -> List[UploadedFile]
        return cls.query(ancestor=poi_key)

    @classmethod
    def list_by_user(cls, service_user):
        return cls.query(ancestor=parent_ndb_key(service_user, SOLUTION_COMMON))

    @classmethod
    def list_by_user_and_path(cls, service_user, path):
        return cls.list_by_user(service_user) \
            .filter(cls.cloudstorage_path > path) \
            .filter(cls.cloudstorage_path < path + u'\ufffd')  # 'starts with' query


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


class FormIntegrationConfiguration(NdbModel):
    # Stores credentials / basic configuration
    enabled = ndb.BooleanProperty(default=True)
    configuration = ndb.JsonProperty()

    @property
    def provider(self):
        return self.key.id()

    @classmethod
    def create_key(cls, service_user, provider):
        if provider not in ALL_FORM_INTEGRATION_PROVIDERS:
            raise Exception('Invalid provider %s' % provider)
        return ndb.Key(cls, provider, parent=parent_ndb_key(service_user, SOLUTION_COMMON))

    @classmethod
    def list_by_user(cls, service_user):
        return cls.query(ancestor=parent_ndb_key(service_user, SOLUTION_COMMON))

    def to_dict(self, extra_properties=None, include=None, exclude=None):
        extra_properties = ['provider'] or extra_properties
        return super(FormIntegrationConfiguration, self).to_dict(extra_properties, include, exclude)
