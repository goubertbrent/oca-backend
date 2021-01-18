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
from typing import List

from mcfw.utils import Enum
from rogerthat.dal import parent_ndb_key
from rogerthat.models import NdbModel


class VoucherProviderId(Enum):
    CIRKLO = 'cirklo'


class CirkloUserVouchers(NdbModel):
    voucher_ids = ndb.TextProperty(repeated=True)  # type: List[str]

    @classmethod
    def create_key(cls, app_user):
        return ndb.Key(cls, app_user.email(), parent=parent_ndb_key(app_user))


class SignupLanguageProperty(NdbModel):
    nl = ndb.TextProperty()
    fr = ndb.TextProperty()


class OldSignupMails(NdbModel):
    accepted = ndb.TextProperty(default=None)
    denied = ndb.TextProperty(default=None)


class SignupMails(NdbModel):
    accepted = ndb.StructuredProperty(SignupLanguageProperty)  # type: SignupLanguageProperty
    denied = ndb.StructuredProperty(SignupLanguageProperty)  # type: SignupLanguageProperty

    @classmethod
    def from_to(cls, signup_mail):
        model = cls()
        model.accepted = SignupLanguageProperty(**signup_mail.accepted.to_dict())
        model.denied = SignupLanguageProperty(**signup_mail.denied.to_dict())
        return model


class CirkloAppInfo(NdbModel):
    enabled = ndb.BooleanProperty(indexed=False)
    title = ndb.JsonProperty()
    buttons = ndb.JsonProperty()


class CirkloCity(NdbModel):
    service_user_email = ndb.StringProperty()
    logo_url = ndb.TextProperty()

    signup_enabled = ndb.BooleanProperty(default=False)
    signup_logo_url = ndb.TextProperty()
    signup_names = ndb.LocalStructuredProperty(SignupLanguageProperty)
    # TODO remove after migration
    signup_mails = ndb.LocalStructuredProperty(OldSignupMails)  # type: OldSignupMails
    signup_mail = ndb.StructuredProperty(SignupMails)  # type: SignupMails
    app_info = ndb.StructuredProperty(CirkloAppInfo)  # type: CirkloAppInfo

    @property
    def city_id(self):
        return self.key.id().decode('utf-8')

    def signup_name(self, language):
        if language == 'fr':
            return self.signup_names.fr
        return self.signup_names.nl

    @classmethod
    def create_key(cls, city_id):
        return ndb.Key(cls, city_id)

    @classmethod
    def get_by_service_email(cls, service_email):
        return cls.query(cls.service_user_email == service_email).get()

    @classmethod
    def list_signup_enabled(cls):
        return cls.query().filter(cls.signup_enabled == True)

    def get_signup_accepted_mail(self, language):
        return self.signup_mail and getattr(self.signup_mail.accepted, self.get_supported_language(language))

    def get_signup_denied_mail(self, language):
        return self.signup_mail and getattr(self.signup_mail.denied, self.get_supported_language(language))

    @staticmethod
    def get_supported_language(language):
        for lang in ['nl', 'fr']:
            if language.startswith(lang):
                return lang
        return 'nl'


class CirkloMerchant(NdbModel):
    creation_date = ndb.DateTimeProperty(indexed=False, auto_now_add=True)

    city_id = ndb.StringProperty()
    whitelisted = ndb.BooleanProperty(indexed=False)  # needed to be able to show in the app (search index)
    denied = ndb.BooleanProperty(indexed=False)

    service_user_email = ndb.StringProperty(indexed=False)  # oca only
    customer_id = ndb.IntegerProperty(indexed=False)  # oca only

    data = ndb.JsonProperty()  # cirklo only
    emails = ndb.StringProperty(repeated=True, indexed=True)  # cirklo only

    def get_language(self):
        return self.data.get('language')

    @classmethod
    def create_key(cls, service_user_email):
        # this is only used for normal customers that want to use cirklo
        return ndb.Key(cls, service_user_email)

    @classmethod
    def list_by_city_id(cls, city_id):
        return cls.query().filter(cls.city_id == city_id)

    @classmethod
    def get_by_city_id_and_email(cls, city_id, email):
        return cls.query().filter(cls.city_id == city_id).filter(cls.emails == email).get()
