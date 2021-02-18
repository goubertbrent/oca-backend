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

from rogerthat.models.common import NdbModel
from google.appengine.ext import ndb

# DOCS https://authenticatie.vlaanderen.be/docs/beveiligen-van-toepassingen/integratie-methoden/oidc/
# T&I https://authenticatie-ti.vlaanderen.be/op/.well-known/openid-configuration
# PROD https://authenticatie.vlaanderen.be/op/.well-known/openid-configuration

class ACMSettings(NdbModel):
    client_id = ndb.TextProperty()
    client_secret = ndb.TextProperty()
    
    openid_config_uri = ndb.TextProperty()

    auth_redirect_uri = ndb.TextProperty()
    logout_redirect_uri = ndb.TextProperty()

    @classmethod
    def create_key(cls, app_id):
        return ndb.Key(cls, app_id)


class ACMLoginState(NdbModel):
    creation_time = ndb.DateTimeProperty(auto_now_add=True)
    app_id = ndb.TextProperty()
    scope = ndb.TextProperty()
    code_challenge = ndb.TextProperty()
    token = ndb.JsonProperty()
    id_token = ndb.JsonProperty()

    @property
    def state(self):
        return self.key.id()

    @classmethod
    def create_key(cls, state):
        return ndb.Key(cls, state)

    @classmethod
    def list_before_date(cls, date):
        return cls.query(cls.creation_time < date)


class ACMLogoutState(NdbModel):
    creation_time = ndb.DateTimeProperty(auto_now_add=True)
    app_id = ndb.TextProperty()

    @property
    def state(self):
        return self.key.id()

    @classmethod
    def create_key(cls, state):
        return ndb.Key(cls, state)

    @classmethod
    def list_before_date(cls, date):
        return cls.query(cls.creation_time < date)