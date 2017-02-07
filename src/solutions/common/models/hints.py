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

import logging

from rogerthat.dal import parent_key
from rogerthat.rpc import users
from google.appengine.ext import db
from mcfw.cache import CachedModelMixIn, invalidate_cache
from mcfw.serialization import deserializer, ds_model, serializer, s_model, register
from solutions.common import SOLUTION_COMMON


class SolutionHint(db.Model):
    tag = db.StringProperty(indexed=False)
    language = db.StringProperty(indexed=False)
    text = db.TextProperty()
    modules = db.StringListProperty(indexed=False)

    @property
    def id(self):
        return self.key().id()

class SolutionHints(CachedModelMixIn, db.Model):
    hint_ids = db.ListProperty(int, indexed=False)

    def invalidateCache(self):
        from solutions.common.dal.hints import get_solution_hints
        logging.info("SolutionHints removed from cache.")
        invalidate_cache(get_solution_hints)

class SolutionHintSettings(db.Model):
    do_not_show_again = db.ListProperty(int, indexed=False)

    @classmethod
    def create_key(cls, service_user):
        return db.Key.from_path(cls.kind(), service_user.email(),
                                parent=parent_key(service_user, SOLUTION_COMMON))

    @property
    def service_user(self):
        return users.User(self.parent_key().name())




@deserializer
def ds_solution_hints(stream):
    return ds_model(stream, SolutionHints)

@serializer
def s_solution_hints(stream, app):
    s_model(stream, app, SolutionHints)

register(SolutionHints, s_solution_hints, ds_solution_hints)
