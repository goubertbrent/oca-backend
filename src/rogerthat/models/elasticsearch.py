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

from google.appengine.ext import ndb

from rogerthat.models.common import NdbModel


class ElasticsearchSettings(NdbModel):
    base_url = ndb.TextProperty()

    auth_username = ndb.TextProperty()
    auth_password = ndb.TextProperty()

    events_index = ndb.TextProperty()
    services_index = ndb.TextProperty()
    place_types_index = ndb.TextProperty()
    jobs_index = ndb.TextProperty()
    news_index = ndb.TextProperty()
    poi_index = ndb.TextProperty()

    shop_customers_index = ndb.TextProperty()

    @classmethod
    def create_key(cls):
        return ndb.Key(cls, u'ElasticsearchSettings')
