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

from google.appengine.ext import ndb

from rogerthat.consts import DAY
from rogerthat.models import NdbModel

SESSION_EXPIRE_TIME = DAY * 180
COOKIE_KEY = 'oca-web'


class WebClientSession(NdbModel):
    create_date = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    last_use_date = ndb.DateTimeProperty()
    language = ndb.StringProperty(indexed=False)

    @property
    def id(self):
        return self.key.id()

    @classmethod
    def create_key(cls, session_id):
        return ndb.Key(cls, session_id)

    @classmethod
    def list_timed_out(cls, oldest_date):
        return cls.query().filter(cls.last_use_date < oldest_date)
