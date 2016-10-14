# -*- coding: utf-8 -*-
# Copyright 2016 Mobicage NV
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
# @@license_version:1.1@@

from google.appengine.ext import db

from rogerthat.dal import parent_key
from rogerthat.rpc import users
from solutions import SOLUTION_COMMON


class SolutionStaticContent(db.Model):

    TYPE_OWN = 1
    TYPE_PDF = 2

    sc_type = db.IntegerProperty(indexed=True, default=1)

    icon_label = db.StringProperty(indexed=False)
    icon_name = db.StringProperty(indexed=False)
    text_color = db.StringProperty(indexed=False)
    background_color = db.StringProperty(indexed=False)
    html_content = db.TextProperty()
    branding_hash = db.StringProperty(indexed=False)
    visible = db.BooleanProperty(default=True)
    provisioned = db.BooleanProperty(default=True)
    coords = db.ListProperty(int, indexed=False)
    old_coords = db.ListProperty(int, indexed=False)
    deleted = db.BooleanProperty(default=False)

    @property
    def service_user(self):
        return users.User(self.parent_key().name())

    @staticmethod
    def create_key(service_user, static_content_id):
        return db.Key.from_path(SolutionStaticContent.kind(), static_content_id,
                                parent=parent_key(service_user, SOLUTION_COMMON))

    @classmethod
    def get_all_keys(cls):
        return db.Query(cls, keys_only=True)

    @classmethod
    def list(cls, service_user):
        return cls.all().ancestor(parent_key(service_user, SOLUTION_COMMON))

    @classmethod
    def list_changed(cls, service_user):
        return cls.list(service_user).filter('provisioned', False)

    @classmethod
    def list_non_deleted(cls, service_user):
        return cls.list(service_user).filter('deleted', False)
