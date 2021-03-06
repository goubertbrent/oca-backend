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

from rogerthat.models import NdbModel


class FirebaseProjectSettings(NdbModel):
    service_account_key = ndb.JsonProperty()

    @property
    def project_id(self):
        return self.key.id().decode('utf8')

    @classmethod
    def create_key(cls, project_id):
        return ndb.Key(cls, project_id)
