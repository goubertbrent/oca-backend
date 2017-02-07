# -*- coding: utf-8 -*-
# Copyright 2017 Mobicage NV
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
# @@license_version:1.2@@

from google.appengine.ext import db

from rogerthat.dal import parent_key
from rogerthat.rpc import users
from rogerthat.utils.service import create_service_identity_user, get_service_identity_tuple
from solutions.common import SOLUTION_COMMON


class AppBroadcastStatistics(db.Model):
    tags = db.StringListProperty(indexed=False)
    messages = db.StringListProperty(indexed=False)

    @property
    def service_identity(self):
        return self.parent_key().name()

    @property
    def service_user(self):
        return users.User(self.parent_key().parent().name())

    @property
    def service_identity_user(self):
        return create_service_identity_user(self.service_user, self.service_identity)

    @classmethod
    def create_parent_key(cls, service_identity_user):
        service_user, service_identity = get_service_identity_tuple(service_identity_user)
        service_parent_key = parent_key(service_user, SOLUTION_COMMON)
        return db.Key.from_path(service_parent_key.kind(), service_identity, parent=service_parent_key)

    @classmethod
    def create_key(cls, service_identity_user):
        return db.Key.from_path(cls.kind(), service_identity_user.email(),
                                parent=cls.create_parent_key(service_identity_user))

    @classmethod
    def get_by_service_identity_user(cls, service_identity_user):
        return cls.get(cls.create_key(service_identity_user))
