# -*- coding: utf-8 -*-
# Copyright 2018 Mobicage NV
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
# @@license_version:1.3@@
from google.appengine.ext import ndb

from rogerthat.models.common import NdbModel


class JoynMerchantMatch(NdbModel):
    date = ndb.DateTimeProperty(auto_now=True)
    customer_id = ndb.IntegerProperty()
    service = ndb.StringProperty()

    @classmethod
    def create_key(cls, joyn_id):
        return ndb.Key(cls._get_kind(), joyn_id)


class JoynMerchantMatches(NdbModel):
    date = ndb.DateTimeProperty(auto_now=True)
    app_id = ndb.StringProperty()
    zipcode = ndb.StringProperty()
    joyn_data = ndb.JsonProperty()
    matches = ndb.JsonProperty()

    @classmethod
    def create_key(cls, joyn_id):
        return ndb.Key(cls._get_kind(), joyn_id)
