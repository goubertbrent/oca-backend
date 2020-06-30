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
from datetime import datetime

from google.appengine.ext import ndb

from rogerthat.models import NdbModel
from rogerthat.utils import parse_date


class HoplrUser(NdbModel):
    token = ndb.JsonProperty()
    user_id = ndb.IntegerProperty()
    neighbourhood_id = ndb.IntegerProperty()

    # token properties:
    # access_token
    # token_type
    # expires_in
    # UserId
    # NeighbourhoodId
    # .issued
    # .expires

    @property
    def is_token_expired(self):
        return not self.token or parse_date(self.token['.expires']) < datetime.utcnow()

    def get_access_token(self):
        return self.token and self.token['access_token']

    def get_refresh_token(self):
        return self.token and self.token['refresh_token']

    def set_token(self, token):
        self.token = token
        self.user_id = int(token['UserId'])
        self.neighbourhood_id = int(token['NeighbourhoodId'])

    @classmethod
    def create_key(cls, app_user):
        return ndb.Key(cls, app_user.email())
