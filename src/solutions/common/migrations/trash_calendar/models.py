# -*- coding: utf-8 -*-
# Copyright 2018 Mobicage NV
# NOTICE: THIS FILE HAS BEEN MODIFIED BY MOBICAGE NV IN ACCORDANCE WITH THE APACHE LICENSE VERSION 2.0
# Copyright 2018 GIG Technology NV
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

from google.appengine.ext import ndb

from rogerthat.dal import parent_ndb_key
from rogerthat.models.common import NdbModel
from rogerthat.rpc import users


class TrashCalendarTransferSettings(NdbModel):

    base_url = ndb.StringProperty(indexed=False)
    sik = ndb.StringProperty(indexed=False)

    branding = ndb.StringProperty(indexed=False)

    app_id = ndb.StringProperty(indexed=False)

    @property
    def service_user(self):
        return users.User(self.key.parent().id().decode('utf8'))

    @classmethod
    def create_key(cls, service_user):
        return ndb.Key(cls, service_user.email(), parent=parent_ndb_key(service_user, namespace=cls.NAMESPACE))


class TrashCalendarTransferUser(NdbModel):

    service_user = ndb.UserProperty(indexed=True)
    parent_message_key = ndb.StringProperty(indexed=False)
    answer_id = ndb.StringProperty(indexed=True)

    @property
    def app_user(self):
        return users.User(self.key.parent().id().decode('utf8'))

    @classmethod
    def create_key(cls, app_user):
        return ndb.Key(cls, app_user.email(), parent=parent_ndb_key(app_user, namespace=cls.NAMESPACE))
