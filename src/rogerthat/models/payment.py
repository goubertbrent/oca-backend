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

from mcfw.properties import azzert
from mcfw.utils import Enum
from rogerthat.models import Image
from rogerthat.models.apps import EmbeddedApplication
from rogerthat.models.common import NdbModel
from rogerthat.rpc import users


class AssetTypes(Enum):
    BANK = u'bank'
    ACCOUNT = u'account'
    CREDITCARD = u'creditcard'
    CRYPTOCURRENCY_WALLET = u'cryptocurrency_wallet'


class RequiredAction(Enum):
    FOLLOW_URL = u'follow_url'
    ENTER_CODE = u'enter_code'


class PaymentOAuthSettings(ndb.Model):
    client_id = ndb.StringProperty(indexed=False)
    secret = ndb.StringProperty(indexed=False)
    base_url = ndb.StringProperty(indexed=False)
    authorize_path = ndb.StringProperty(indexed=False)
    token_path = ndb.StringProperty(indexed=False)
    scope = ndb.StringProperty(indexed=False, default='')

    @property
    def authorize_url(self):
        return self.base_url + self.authorize_path

    @property
    def token_url(self):
        return self.base_url + self.token_path


class ConversionRatioValue(NdbModel):
    currency = ndb.StringProperty()
    rate = ndb.FloatProperty()


class ConversionRatio(NdbModel):
    base = ndb.StringProperty()
    values = ndb.LocalStructuredProperty(ConversionRatioValue, repeated=True)  # type: list[ConversionRatioValue]


class PaymentProvider(NdbModel):
    """
    Attributes:
        version (long): Implementation version, to check if the app supports this payment provider
        description (unicode): String containing markdown with an explanation on how to authorize this payment provider,
         used when clicking 'add payment provider' 
    """
    name = ndb.StringProperty(indexed=False)
    logo_id = ndb.IntegerProperty(indexed=False)
    version = ndb.IntegerProperty(indexed=False)
    description = ndb.TextProperty()
    oauth_settings = ndb.LocalStructuredProperty(PaymentOAuthSettings)  # type: PaymentOAuthSettings
    background_color = ndb.StringProperty(indexed=False)
    text_color = ndb.StringProperty(indexed=False)
    button_color = ndb.StringProperty(indexed=False, choices=('light', 'primary', 'secondary', 'danger', 'dark'))
    black_white_logo_id = ndb.IntegerProperty(indexed=False)
    asset_types = ndb.StringProperty(indexed=False, repeated=True, choices=AssetTypes.all())
    currencies = ndb.StringProperty(indexed=False, repeated=True)
    settings = ndb.JsonProperty()
    embedded_application = ndb.KeyProperty(EmbeddedApplication)  # type: ndb.Key
    app_ids = ndb.StringProperty(repeated=True)
    conversion_ratio = ndb.LocalStructuredProperty(ConversionRatio)  # type: ConversionRatio

    @property
    def id(self):
        return self.key.string_id().decode('utf8')

    def logo_url(self, base_url):
        # todo refactor to use gcs instead of abusing the datastore
        return Image.url(base_url, self.logo_id)

    def black_white_logo_url(self, base_url):
        # todo refactor to use gcs instead of abusing the datastore
        return Image.url(base_url, self.black_white_logo_id)

    @classmethod
    def create_key(cls, provider_id):
        return ndb.Key(cls, provider_id)

    @classmethod
    def list_by_app(cls, app_id):
        return cls.query().filter(cls.app_ids == app_id)

    def redirect_url(self, base_url):
        return '%s/payments/callbacks/%s/oauth' % (base_url, self.id)

    def get_setting(self, setting):
        if not self.settings:
            raise ValueError('PaymentProvider %s settings is not set' % self.id)
        value = self.settings.get(setting)
        if not value:
            raise ValueError('PaymentProvider %s setting %s is not set' % (self.id, setting))
        return value

    def get_currency_rate(self, source_currency, target_currency):
        # type: (unicode, unicode) -> float
        source_rate = target_rate = 0
        if source_currency == self.conversion_ratio.base:
            source_rate = 1.0
        if target_currency == self.conversion_ratio.base:
            target_rate = 1.0
        for rate in self.conversion_ratio.values:
            if rate.currency == source_currency:
                source_rate = rate.rate
            if rate.currency == target_currency:
                target_rate = rate.rate
        if not source_rate or not target_rate:
            raise Exception('Cannot calculate currency rate from %s to %s' % (source_currency, target_currency))
        return source_rate / target_rate


class PaymentOauthLoginState(ndb.Model):
    timestamp = ndb.IntegerProperty(indexed=False)
    provider_id = ndb.StringProperty(indexed=False)
    app_user = ndb.UserProperty(indexed=False)
    code = ndb.StringProperty(indexed=False)
    completed = ndb.BooleanProperty(indexed=False)

    @property
    def state(self):
        return self.key.id().decode('utf8')

    @property
    def app_id(self):
        from rogerthat.utils.app import get_app_id_from_app_user
        return get_app_id_from_app_user(self.app_user)

    @classmethod
    def create_key(cls, state):
        return ndb.Key(cls, state)


class PaymentUserProvider(ndb.Model):
    provider_id = ndb.StringProperty()
    token = ndb.JsonProperty()


class PaymentRequiredAction(ndb.Model):
    action = ndb.StringProperty()  # One of payment.consts.RequiredAction
    description = ndb.StringProperty(indexed=False)
    data = ndb.JsonProperty()


class PaymentUserAsset(ndb.Model):
    provider_id = ndb.StringProperty()
    asset_id = ndb.StringProperty()
    currency = ndb.StringProperty()
    type = ndb.StringProperty(choices=AssetTypes.all())
    required_action = ndb.StructuredProperty(PaymentRequiredAction)  # type: PaymentRequiredAction


class PaymentUser(ndb.Model):
    providers = ndb.StructuredProperty(PaymentUserProvider, repeated=True)  # type: list[PaymentUserProvider]
    assets = ndb.StructuredProperty(PaymentUserAsset, repeated=True)  # type: list[PaymentUserAsset]

    @property
    def user(self):
        return users.User(self.key.string_id().decode('utf8'))

    def get_provider(self, provider_id):
        for pup in self.providers:
            if pup.provider_id == provider_id:
                return pup
        return None

    def has_provider(self, provider_id):
        if self.get_provider(provider_id):
            return True
        return False
    
    def has_asset(self, provider_id, asset_id):
        if not self.assets:
            return False
        for asset in self.assets:
            if asset.provider_id == provider_id:
                if asset.asset_id == asset_id:
                    return True
        return False
        

    def get_assets_by_provider(self, provider_id):
        if not self.assets:
            return {}
        return {asset.asset_id: asset for asset in self.assets if asset.provider_id == provider_id}

    @classmethod
    def create_key(cls, app_user):
        from rogerthat.dal import parent_ndb_key
        return ndb.Key(cls, app_user.email(), parent=parent_ndb_key(app_user))

    @classmethod
    def list_by_provider_id(cls, provider_id):
        return cls.query(cls.providers.provider_id == provider_id)


class PaymentServiceProviderFee(ndb.Model):
    amount = ndb.IntegerProperty(default=0)
    precision = ndb.IntegerProperty(default=2)
    min_amount = ndb.IntegerProperty(default=0)
    currency = ndb.StringProperty()


class PaymentServiceProvider(ndb.Model):
    provider_id = ndb.StringProperty()
    enabled = ndb.BooleanProperty(default=True)
    fee = ndb.StructuredProperty(PaymentServiceProviderFee)  # type: PaymentServiceProviderFee
    settings = ndb.JsonProperty()


class PaymentService(ndb.Model):
    providers = ndb.StructuredProperty(PaymentServiceProvider, repeated=True)  # type: list[PaymentServiceProvider]
    test_providers = ndb.StructuredProperty(PaymentServiceProvider, repeated=True)  # type: list[PaymentServiceProvider]

    @property
    def service_identity_user(self):
        return users.User(self.key.string_id().decode('utf8'))

    def get_providers(self, test_mode=False):
        return self.test_providers if test_mode else self.providers

    def add_provider(self, psp, test_mode=False):
        self.get_providers(test_mode).append(psp)

    def get_provider(self, provider_id, test_mode=False):
        for psp in self.get_providers(test_mode):
            if psp.provider_id == provider_id:
                return psp
        return None

    def has_provider(self, provider_id, test_mode=False):
        if self.get_provider(provider_id, test_mode):
            return True
        return False

    def remove_provider(self, provider_id, test_mode=False):
        provider = self.get_provider(provider_id, test_mode)
        if provider:
            self.get_providers(test_mode).remove(provider)
            return True
        return False

    @classmethod
    def create_key(cls, service_identity_user):
        from rogerthat.dal import parent_ndb_key_unsafe
        azzert("/" in service_identity_user.email())
        return ndb.Key(cls, service_identity_user.email(), parent=parent_ndb_key_unsafe(service_identity_user))

    @classmethod
    def list_by_provider_id(cls, provider_id, test_mode=False):
        if test_mode:
            return cls.query(cls.test_providers.provider_id == provider_id)
        return cls.query(cls.providers.provider_id == provider_id)


class PaymentPendingReceive(ndb.Model):
    STATUS_CREATED = u"created"
    STATUS_SCANNED = u"scanned"
    STATUS_CANCELLED_BY_RECEIVER = u"cancelled_by_receiver"
    STATUS_CANCELLED_BY_PAYER = u"cancelled_by_payer"
    STATUS_FAILED = u"failed"
    STATUS_PENDING = u'pending'
    STATUS_SIGNATURE = u"signature"
    STATUS_CONFIRMED = u"confirmed"
    STATUSES = [STATUS_CREATED, STATUS_SCANNED, STATUS_CANCELLED_BY_RECEIVER, STATUS_CANCELLED_BY_PAYER, STATUS_FAILED,
                STATUS_PENDING, STATUS_SIGNATURE, STATUS_CONFIRMED]

    timestamp = ndb.IntegerProperty(indexed=False)
    provider_id = ndb.StringProperty(indexed=False)
    asset_id = ndb.StringProperty(indexed=False)
    app_user = ndb.UserProperty(indexed=False)
    currency = ndb.StringProperty(indexed=False)
    amount = ndb.IntegerProperty(indexed=False)
    memo = ndb.StringProperty(indexed=False)
    precision = ndb.IntegerProperty(indexed=False)

    status = ndb.StringProperty(indexed=False, choices=STATUSES)
    pay_user = ndb.UserProperty(indexed=False)
    pay_asset_id = ndb.StringProperty(indexed=False)

    @property
    def transaction_id(self):
        return self.key.string_id().decode('utf8')

    @classmethod
    def create_key(cls, guid):
        return ndb.Key(cls, guid)
