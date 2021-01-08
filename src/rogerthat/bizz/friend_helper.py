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

import StringIO
import collections
from contextlib import closing
import json
import logging

from google.appengine.api import memcache
from google.appengine.ext import db

import cloudstorage
from mcfw.consts import MISSING
from mcfw.properties import azzert
from mcfw.serialization import s_any, ds_any
from rogerthat.consts import FRIEND_HELPER_BUCKET
from rogerthat.dal.profile import get_service_profile
from rogerthat.dal.roles import list_service_roles, get_service_role_by_id
from rogerthat.dal.service import get_service_menu_items, get_service_identity
from rogerthat.models import ServiceTranslation, ServiceInteractionDef, UserProfile, Branding
from rogerthat.to.friends import FriendTO
from rogerthat.utils import guid, today
from rogerthat.utils.service import get_service_user_from_service_identity_user, add_slash_default
from rogerthat.utils.transactions import run_in_transaction


class FriendHelper(object):
    """Helper class for creating a FriendTO. There are 2 types.
    - One which gets the data from the datastore
    - One which gets the data from cloud storage cache
    """

    def __repr__(self):
        return '%(class)s(user=\'%(user)s\', friend_type=%(friend_type)s)' % {
            'class': self.__class__.__name__,
            'user': self.user,
            'friend_type': self.friend_type
        }

    __str__ = __repr__

    def __init__(self, user, friend_type):
        self.user = user
        self.friend_type = friend_type
        self.brandings = {}
        self._translator = None

    @staticmethod
    def from_data_store(user, friend_type):
        return _FriendDatastoreHelper(user, friend_type)

    @staticmethod
    def from_cloud_storage(user, friend_type, cloud_storage_path):
        return FriendCloudStorageHelper(user, friend_type, cloud_storage_path)

    def add_to_memcache(self, cloud_storage_path, value):
        if len(value) < memcache.MAX_VALUE_SIZE:
            memcache.set(cloud_storage_path, value, time=3600)  # @UndefinedVariable

    @classmethod
    def serialize(cls, user, friend_type):
        # type: (users.User, int) -> FriendCloudStorageHelper
        if friend_type == FriendTO.TYPE_SERVICE:
            assert '/' in user.email()
        datastore_helper = FriendHelper.from_data_store(user, friend_type)

        def trans():
            data = {}
            flow_keys = []
            for method in ('get_service_profile', 'get_profile_info', 'list_service_menu_items', 'list_roles',
                           'get_share_sid', '_get_all_translations', 'get_service_data', 'get_brandings'):
                logging.debug('Serializing result of %s', method)
                f = getattr(datastore_helper, method)
                obj = f()
                if obj:
                    if isinstance(obj, dict) or not isinstance(obj, collections.Iterable):
                        data[method] = obj
                    else:
                        is_menu_items_method = method == 'list_service_menu_items'
                        for i, model in enumerate(obj):
                            data['%s-%s' % (method, i)] = model
                            if is_menu_items_method and model.staticFlowKey:
                                flow_keys.append(model.staticFlowKey)
            if flow_keys:
                flows = db.get(flow_keys)
                for flow in flows:
                    data['flow-%s' % flow.key()] = flow

            return data

        # TODO: Change xg to False once ServiceTranslationSet uses same parent key as other service data
        data = run_in_transaction(trans, xg=True)
        with closing(StringIO.StringIO()) as stream:
            s_any(stream, data)
            serialized_value = stream.getvalue()
        serialized_length = len(serialized_value)
        logging.info('Size of serialized FriendHelper for %s: %d', user, serialized_length)
        cloud_storage_path = FriendCloudStorageHelper.create_cloudstorage_path(user.email())
        with cloudstorage.open(cloud_storage_path, 'w') as f:
            f.write(serialized_value)
        datastore_helper.add_to_memcache(cloud_storage_path, serialized_value)
        return FriendCloudStorageHelper.from_cloud_storage(user, friend_type, cloud_storage_path)

    @property
    def is_service(self):
        # type: () -> bool
        return self.friend_type == FriendTO.TYPE_SERVICE

    @property
    def service_user(self):
        # type: () -> users.User
        return get_service_user_from_service_identity_user(self.user)

    @property
    def service_identity_user(self):
        # type: () -> users.User
        return add_slash_default(self.user)

    @property
    def profile_info_user(self):
        # type: () -> users.User
        return self.service_identity_user if self.is_service else self.user

    def get_service_profile(self):
        # type: () -> ServiceProfile
        raise NotImplementedError()

    def get_service_data(self):
        # type: () -> dict
        raise NotImplementedError()

    def get_profile_info(self):
        raise NotImplementedError()

    def list_service_menu_items(self):
        raise NotImplementedError()

    def list_roles(self):
        # type: () -> list[ServiceRole]
        raise NotImplementedError()

    def get_role(self, role_id):
        raise NotImplementedError()

    def get_message_flow(self, key):
        raise NotImplementedError()

    def get_share_sid(self):
        raise NotImplementedError()

    def set_service_identity_user(self):
        raise NotImplementedError()

    def get_brandings(self):
        raise NotImplementedError()

    def get_branding(self, branding_hash):
        raise NotImplementedError()

    def _get_all_translations(self):
        raise NotImplementedError()

    def get_translator(self):
        from rogerthat.bizz.i18n import DummyTranslator, Translator
        if self.is_service:
            if not self._translator:
                translations = self._get_all_translations()
                service_profile = self.get_service_profile()
                if translations:
                    self._translator = Translator(translations, service_profile.supportedLanguages)
                else:
                    self._translator = DummyTranslator(service_profile.defaultLanguage)
            return self._translator


class _FriendDatastoreHelper(FriendHelper):

    def __init__(self, user, friend_type):
        super(_FriendDatastoreHelper, self).__init__(user, friend_type)
        self.has_data = False
        self._service_profile = None
        self._profile_info = None
        self._brandings = {}

    def __getattribute__(self, item):
        if item.startswith('get'):
            self._ensure_data()
        return super(_FriendDatastoreHelper, self).__getattribute__(item)

    def _ensure_data(self):
        if self.has_data:
            return
        else:
            if self.is_service:
                self._service_profile = get_service_profile(self.service_user)
                self._profile_info = get_service_identity(self.service_identity_user)
            else:
                self._profile_info = db.get(UserProfile.createKey(self.user))
            self.has_data = True

    def get_service_profile(self):
        # type: () -> ServiceProfile
        if self.is_service:
            return self._service_profile

    def get_profile_info(self):
        # type: () -> ServiceIdentity
        azzert(self._profile_info)
        return self._profile_info

    def get_service_data(self):
        if self.is_service:
            service_identity = self.get_profile_info()
            return service_identity.appData and json.loads(service_identity.appData)

    def list_service_menu_items(self):
        return get_service_menu_items(self.user) if self.is_service else []

    def list_roles(self):
        return list_service_roles(self.service_user)

    def get_role(self, role_id):
        if self.is_service:
            return get_service_role_by_id(self.service_user, role_id)

    def get_message_flow(self, key):
        if self.is_service:
            return db.get(key)

    def _get_all_translations(self):
        if self.is_service:
            from rogerthat.bizz.i18n import get_all_translations, get_active_translation_set
            s = get_active_translation_set(self.get_service_profile())
            if s:
                translation_types = ServiceTranslation.HOME_TYPES + ServiceTranslation.IDENTITY_TYPES
                translations = get_all_translations(s, translation_types)
                return translations

    def get_share_sid(self):
        if self.is_service:
            service_identity = self.get_profile_info()
            if service_identity.shareEnabled:
                return ServiceInteractionDef.get(service_identity.shareSIDKey)

    def set_service_identity_user(self, service_identity_user):
        azzert(add_slash_default(self.user) == service_identity_user)

    def get_brandings(self):
        if not self.is_service:
            return {}
        if self._brandings:
            return self._brandings
        brandings_to_get = []
        profile_info = self.get_profile_info()
        translator = self.get_translator()
        for language in translator.supported_languages:
            if profile_info.menuBranding and profile_info.menuBranding not in brandings_to_get:
                brandings_to_get.append(translator.translate(ServiceTranslation.HOME_BRANDING,
                                                             profile_info.menuBranding, language))
        keys = [Branding.create_key(b_hash) for b_hash in brandings_to_get]
        self._brandings = {branding.hash: branding for branding in db.get(keys)} if keys else {}
        return self._brandings

    def get_branding(self, branding_hash):
        return self.get_brandings()[branding_hash]


class FriendCloudStorageHelper(FriendHelper):

    def __init__(self, user, friend_type, cloud_storage_path):
        FriendHelper.__init__(self, user, friend_type)
        self.cloud_storage_path = cloud_storage_path

    @staticmethod
    def create_cloudstorage_path(user):
        # type: (str) -> str
        return '/'.join([FRIEND_HELPER_BUCKET, str(today()), user, guid()])

    @property
    def _data(self):
        if not hasattr(self, '_internal_data'):
            data_from_memcache = memcache.get(self.cloud_storage_path)  # @UndefinedVariable
            if data_from_memcache:
                with closing(StringIO.StringIO()) as stream:
                    stream.write(data_from_memcache)
                    stream.seek(0)
                    self._internal_data = ds_any(stream)
            else:
                with cloudstorage.open(self.cloud_storage_path, 'r') as f:
                    self.add_to_memcache(self.cloud_storage_path, f.read())
                    f.seek(0)
                    self._internal_data = ds_any(f)
        return self._internal_data

    def _get(self, method):
        model = self._data.get(method, MISSING)
        if model is not MISSING:
            return model

        if '%s-0' % method in self._data:
            x = 0
            models = []
            while True:
                model = self._data.get('%s-%s' % (method, x))
                if not model:
                    break
                models.append(model)
                x += 1
            return models

        return None

    def get_service_profile(self):
        # type: () -> ServiceProfile
        if self.is_service:
            return self._get('get_service_profile')

    def get_profile_info(self):
        return self._get('get_profile_info')

    def get_service_data(self):
        return self._get('get_service_data')

    def list_service_menu_items(self):
        return self._get('list_service_menu_items') or []

    def list_roles(self):
        # type: () -> list[ServiceRole]
        return self._get('list_roles') or []

    def get_role(self, role_id):
        if self.is_service:
            for role in self.list_roles():
                if role.role_id == role_id:
                    return role

    def get_message_flow(self, key):
        if self.is_service:
            return self._data.get('flow-%s' % key)

    def _get_all_translations(self):
        if self.is_service:
            return self._get('_get_all_translations')

    def get_share_sid(self):
        if self.is_service:
            return self._get('get_share_sid')

    def set_service_identity_user(self, service_identity_user):
        if add_slash_default(self.user) != service_identity_user:
            # this can happen when a helper is created with supplying a service user
            self.user = service_identity_user
            for m in ('get_profile_info', 'get_share_sid', 'get_service_data'):
                self._data[m] = MISSING

    def get_brandings(self):
        return self._get('get_brandings')

    def get_branding(self, branding_hash):
        return self.get_brandings()[branding_hash]
