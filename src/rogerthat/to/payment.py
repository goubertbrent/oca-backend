# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
# NOTICE: THIS FILE HAS BEEN MODIFIED BY GREEN VALLEY BELGIUM NV IN ACCORDANCE WITH THE APACHE LICENSE VERSION 2.0
# Copyright 2018 GIG Technology NV
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
# @@license_version:1.6@@

import urllib

from mcfw.properties import long_property, unicode_property, typed_property, bool_property, unicode_list_property, \
    float_property
from rogerthat.models.payment import PaymentUserAsset, PaymentRequiredAction, \
    RequiredAction
from rogerthat.models.properties.forms import BasePaymentMethod
from rogerthat.to import TO
from rogerthat.to.app import EmbeddedAppTO
from rogerthat.to.messaging.forms import PaymentMethodTO
from rogerthat.to.service import UserDetailsTO
from rogerthat.utils.app import get_app_user_tuple


class PaymentOAuthSettingsTO(object):
    client_id = unicode_property('client_id')
    secret = unicode_property('secret')
    base_url = unicode_property('base_url')
    authorize_path = unicode_property('authorize_path')
    token_path = unicode_property('token_path')
    scope = unicode_property('scope')

    def __init__(self, client_id=None, secret=None, base_url=None, authorize_path=None, token_path=None, scope=None):
        self.client_id = client_id
        self.secret = secret
        self.base_url = base_url
        self.authorize_path = authorize_path
        self.token_path = token_path
        self.scope = scope

    @staticmethod
    def redirect_url(base_url, provider_id, app_user):
        human_user, app_id = get_app_user_tuple(app_user)
        args = {'email': human_user.email(), 'app_id': app_id}
        return "%s/payments/login/%s/redirect?%s" % (base_url, provider_id, urllib.urlencode(args))

    @classmethod
    def from_model(cls, model):
        if not model:
            return None
        return cls(model.client_id, model.secret, model.base_url, model.authorize_path, model.token_path, model.scope)

    def to_model(self):
        from rogerthat.models.payment import PaymentOAuthSettings
        return PaymentOAuthSettings(
            client_id=self.client_id,
            secret=self.secret,
            base_url=self.base_url,
            authorize_path=self.authorize_path,
            token_path=self.token_path,
            scope=self.scope
        )


class ConversionRatioValueTO(TO):
    currency = unicode_property('currency')
    rate = float_property('rate')


class ConversionRatioTO(TO):
    base = unicode_property('base')
    values = typed_property('values', ConversionRatioValueTO, True)  # type: list[ConversionRatioValueTO]


class PaymentProviderTO(TO):
    id = unicode_property('id')
    name = unicode_property('name')
    logo = unicode_property('logo')
    version = long_property('version')
    embedded_application = unicode_property('embedded_application')
    description = unicode_property('description')
    oauth_settings = typed_property('oauth_settings', PaymentOAuthSettingsTO)  # type: PaymentOAuthSettingsTO
    background_color = unicode_property('background_color')
    text_color = unicode_property('text_color')
    button_color = unicode_property('button_color')
    black_white_logo = unicode_property('black_white_logo')
    asset_types = unicode_list_property('asset_types')
    currencies = unicode_list_property('currencies')
    settings = typed_property('settings', dict)
    app_ids = unicode_list_property('app_ids')
    conversion_ratio = typed_property('conversion_ratio', ConversionRatioTO)  # type: ConversionRatioTO

    @classmethod
    def from_model(cls, base_url, model):
        """
        Args:
            base_url (unicode)
            model (PaymentProvider)
        """
        d = model.to_dict()
        d.update(logo=model.logo_url(base_url),
                 black_white_logo=model.black_white_logo_url(base_url))
        return super(PaymentProviderTO, cls).from_dict(d)


# Mostly the same as PaymentProviderTO
class AppPaymentProviderTO(TO):
    id = unicode_property('1')
    name = unicode_property('2')
    logo_url = unicode_property('3')
    version = long_property('4')
    description = unicode_property('5')
    oauth_authorize_url = unicode_property('6')
    enabled = bool_property('7')
    background_color = unicode_property('8')
    text_color = unicode_property('9')
    button_color = unicode_property('10')
    black_white_logo = unicode_property('11')
    asset_types = unicode_list_property('12')
    currencies = unicode_list_property('13')
    embedded_app_id = unicode_property('embedded_app_id', default=None)

    @classmethod
    def from_model(cls, base_url, model, enabled, app_user):
        """
        Args:
            base_url (unicode)
            model (PaymentProvider)
            enabled (bool)
            app_user (users.User)
        """

        d = model.to_dict()
        d.update(logo_url=model.logo_url(base_url),
                 black_white_logo=model.black_white_logo_url(base_url),
                 enabled=enabled,
                 oauth_authorize_url=PaymentOAuthSettingsTO.redirect_url(base_url, model.id, app_user),
                 embedded_app_id=model.embedded_application.id().decode(
                     'utf-8') if model.embedded_application else None)
        return super(AppPaymentProviderTO, cls).from_dict(d)


class PaymentAssetRequiredActionTO(object):
    action = unicode_property('1')  # One of payment.consts.RequiredAction
    description = unicode_property('2')
    data = unicode_property('3')

    def __init__(self, action=None, description=None, data=None):
        if action and not hasattr(RequiredAction, action.upper()):
            raise ValueError('Invalid required action type %s' % action)

        self.action = action
        self.description = description
        self.data = data

    @classmethod
    def from_model(cls, required_action):
        # type: (PaymentRequiredAction) -> cls
        if required_action:
            return cls(required_action.action, required_action.description, required_action.data)
        return None

    def to_model(self):
        # type: () -> PaymentRequiredAction
        return PaymentRequiredAction(action=self.action, description=self.description, data=self.data)


class PaymentAssetBalanceTO(object):
    amount = long_property('1')
    description = unicode_property('2')
    precision = long_property('3', default=2)


class PaymentProviderAssetTO(object):
    provider_id = unicode_property('1')
    id = unicode_property('2')
    type = unicode_property('3')  # Is one of payment.consts.AssetTypes
    name = unicode_property('4')
    currency = unicode_property('5')
    available_balance = typed_property('6', PaymentAssetBalanceTO)
    total_balance = typed_property('7', PaymentAssetBalanceTO)
    verified = bool_property('8')
    enabled = bool_property('9')
    has_balance = bool_property('10')
    has_transactions = bool_property('11')
    required_action = typed_property('12', PaymentAssetRequiredActionTO)  # type: PaymentAssetRequiredActionTO

    def __init__(self, provider_id=None, id=None, type=None, name=None, currency=None, available_balance=None,
                 total_balance=None, verified=False, enabled=False, has_balance=False, has_transactions=False,
                 required_action=None):
        self.provider_id = provider_id
        self.id = id
        self.type = type
        self.name = name
        self.currency = currency
        self.available_balance = available_balance
        self.total_balance = total_balance
        self.verified = verified
        self.enabled = enabled
        self.has_balance = has_balance
        self.has_transactions = has_transactions
        self.required_action = required_action

    @classmethod
    def from_model(cls, model, asset):
        """
        Since we cannot store everything we need both the model and the asset retrieved from the payment provider
        It still is possible that we have a model but no asset on the provider, for example a credit card
        Args:
            model (PaymentUserAsset)
            asset (PaymentProviderAssetTO)
        """
        # todo better name
        provider_id = asset.provider_id if asset else model.provider_id
        asset_id = asset.id if asset else model.asset_id
        type = asset.type if asset else model.type
        currency = asset.currency if asset else model.currency

        name = asset.name if asset else u'Unknown'
        available_balance = asset.available_balance if asset else None
        total_balance = asset.total_balance if asset else None
        verified = asset.verified if asset else False
        enabled = asset.enabled if asset else False
        has_balance = asset.has_balance if asset else False
        has_transactions = asset.has_transactions if asset else False
        required_action = asset.required_action if asset else PaymentAssetRequiredActionTO.from_model(
            model.required_action)
        return cls(provider_id, asset_id, type, name, currency, available_balance,
                   total_balance, verified, enabled, has_balance, has_transactions, required_action)

    def to_model(self):
        return PaymentUserAsset(provider_id=self.provider_id, asset_id=self.id, type=self.type, currency=self.currency,
                                required_action=self.required_action.to_model() if self.required_action else None)


class CreatePaymentAssetTO(object):
    provider_id = unicode_property('provider_id')
    type = unicode_property('type')  # Must be one of payment.consts.AssetTypes
    currency = unicode_property('currency')
    iban = unicode_property('iban')  # Only used when type == 'bank'
    address = unicode_property('address')  # Only used when type == 'cryptocurrency_wallet'
    id = unicode_property('id')  # Currently only used when type == 'cryptocurrency_wallet'


class PaymentProviderTransactionTO(object):
    id = unicode_property('1')
    type = unicode_property('2')
    name = unicode_property('3')
    amount = long_property('4')
    currency = unicode_property('5')
    memo = unicode_property('6')
    timestamp = long_property('7')
    from_asset_id = unicode_property('8')
    to_asset_id = unicode_property('9')
    precision = long_property('10', default=2)


class PendingPaymentTO(object):
    status = unicode_property('1')
    transaction_id = unicode_property('2')

    def __init__(self, status=None, transaction_id=None):
        self.status = status
        self.transaction_id = transaction_id

    @classmethod
    def create(cls, status=None, transaction_id=None):
        r = cls()
        r.status = status
        r.transaction_id = transaction_id
        return r


class ErrorPaymentTO(TO):
    # All of these errors must be translation keys, with a 'payments.' prefix.
    UNKNOWN = u'unknown'
    PROVIDER_NOT_FOUND = u'provider_not_found'
    CURRENCY_UNKNOWN = u'currency_unknown'
    PERMISSION_DENIED = u'permission_denied'
    TRANSACTION_NOT_FOUND = u'transaction_not_found'
    TRANSACTION_NOT_INITIATED = u'transaction_not_initiated'
    TRANSACTION_ALREADY_INITIATED = u'transaction_already_initiated'
    TRANSACTION_FINISHED = u'transaction_finished'
    ACCOUNT_ALREADY_EXISTS = u'account_already_exists'
    DUPLICATE_WALLET = u'duplicate_wallet'
    INVALID_IBAN = u'invalid_iban'
    INVALID_VERIFICATION_CODE = u'invalid_verification_code'
    CANNOT_VERIFY_WALLET_TYPE = u'cannot_verify_wallet_type'
    INSUFFICIENT_FUNDS = u'insufficient_funds'

    code = unicode_property('1')
    message = unicode_property('2')
    data = unicode_property('3', default=None)

    def __init__(self, code=None, message=None, data=None):
        super(ErrorPaymentTO, self).__init__(code=code, message=message, data=data)


class PendingPaymentDetailsTO(PendingPaymentTO):
    provider = typed_property('50', AppPaymentProviderTO, False)
    assets = typed_property('51', PaymentProviderAssetTO, True)
    receiver = typed_property('52', UserDetailsTO, False)
    receiver_asset = typed_property('53', PaymentProviderAssetTO, False)
    currency = unicode_property('54')
    amount = long_property('55')
    memo = unicode_property('56')
    timestamp = long_property('57')
    precision = long_property('58')

    def __init__(self, status=None, transaction_id=None, provider=None, assets=None, receiver=None, receiver_asset=None,
                 currency=None, amount=0, memo=None, timestamp=0, precision=2):
        super(PendingPaymentDetailsTO, self).__init__(status, transaction_id)
        if assets is None:
            assets = []
        self.provider = provider
        self.assets = assets
        self.receiver = receiver
        self.receiver_asset = receiver_asset
        self.currency = currency
        self.amount = amount
        self.memo = memo
        self.timestamp = timestamp
        self.precision = precision


class GetPaymentProvidersRequestTO(object):
    pass


class GetPaymentProvidersResponseTO(object):
    payment_providers = typed_property('1', AppPaymentProviderTO, True)


class UpdatePaymentProvidersRequestTO(object):
    provider_ids = unicode_list_property('1')
    payment_providers = typed_property('2', AppPaymentProviderTO, True)


class UpdatePaymentProvidersResponseTO(object):
    pass


class UpdatePaymentProviderRequestTO(AppPaymentProviderTO):
    pass


class UpdatePaymentProviderResponseTO(object):
    pass


class UpdatePaymentAssetsRequestTO(object):
    provider_ids = unicode_list_property('1')
    assets = typed_property('2', PaymentProviderAssetTO, True)


class UpdatePaymentAssetsResponseTO(object):
    pass


class UpdatePaymentAssetRequestTO(PaymentProviderAssetTO):
    pass


class UpdatePaymentAssetResponseTO(object):
    pass


class GetPaymentProfileRequestTO(object):
    provider_id = unicode_property('1')


class GetPaymentProfileResponseTO(object):
    first_name = unicode_property('1')
    last_name = unicode_property('2')


class GetPaymentAssetsRequestTO(object):
    provider_id = unicode_property('1')


class GetPaymentAssetsResponseTO(object):
    assets = typed_property('1', PaymentProviderAssetTO, True)


class GetPaymentTransactionsRequestTO(object):
    provider_id = unicode_property('1')
    asset_id = unicode_property('2')
    cursor = unicode_property('3', default=None)
    type = unicode_property('4')


class GetPaymentTransactionsResponseTO(object):
    cursor = unicode_property('1', default=None)
    transactions = typed_property('2', PaymentProviderTransactionTO, True)


class VerifyPaymentAssetRequestTO(object):
    provider_id = unicode_property('1')
    asset_id = unicode_property('2')
    code = unicode_property('3')


class PaymentRpcResultTO(object):
    success = bool_property('1')
    error = typed_property('2', ErrorPaymentTO)

    def __init__(self, success=False, error=None):
        """
        Args:
            success (bool)
            error (ErrorPaymentTO)
        """
        self.success = success
        self.error = error


class VerifyPaymentAssetResponseTO(PaymentRpcResultTO):
    pass


class ReceivePaymentRequestTO(object):
    provider_id = unicode_property('1')
    asset_id = unicode_property('2')
    amount = long_property('3')
    memo = unicode_property('4')
    precision = long_property('5')


class ReceivePaymentResponseTO(PaymentRpcResultTO):
    result = typed_property('result', PendingPaymentTO, False)

    def __init__(self, success=False, error=None, result=None):
        super(ReceivePaymentResponseTO, self).__init__(success, error)
        self.result = result


class CancelPaymentRequestTO(object):
    transaction_id = unicode_property('1')


class CancelPaymentResponseTO(PaymentRpcResultTO):
    pass


class GetPendingPaymentDetailsRequestTO(object):
    transaction_id = unicode_property('1')


class GetPendingPaymentDetailsResponseTO(PaymentRpcResultTO):
    result = typed_property('result', PendingPaymentDetailsTO, False)

    def __init__(self, success=False, error=None, result=None):
        super(GetPendingPaymentDetailsResponseTO, self).__init__(success, error)
        self.result = result


class GetPendingPaymentSignatureDataRequestTO(object):
    transaction_id = unicode_property('1')
    asset_id = unicode_property('2')


class CryptoTransactionInputTO(object):
    parent_id = unicode_property('1')
    timelock = long_property('2')

    def __init__(self, parent_id=None, timelock=0):
        self.parent_id = parent_id
        self.timelock = timelock


class CryptoTransactionOutputTO(object):
    value = unicode_property('1')
    unlockhash = unicode_property('2')

    def __init__(self, value=None, unlockhash=None):
        self.value = value
        self.unlockhash = unlockhash


class CryptoTransactionDataTO(object):
    input = typed_property('1', CryptoTransactionInputTO, False)
    outputs = typed_property('2', CryptoTransactionOutputTO, True)
    timelock = long_property('3', default=0)
    algorithm = unicode_property('4', default=None)
    public_key_index = long_property('5', default=0)
    public_key = unicode_property('6', default=None)
    signature_hash = unicode_property('7', default=None)
    signature = unicode_property('8', default=None)


class CryptoTransactionTO(object):
    minerfees = unicode_property('1')
    data = typed_property('2', CryptoTransactionDataTO, True)
    from_address = unicode_property('3')
    to_address = unicode_property('4')

    def __init__(self, minerfees=None, data=None, from_address=None, to_address=None):
        self.minerfees = minerfees
        self.data = data or []
        self.from_address = from_address
        self.to_address = to_address


class GetPendingPaymentSignatureDataResponseTO(PaymentRpcResultTO):
    result = typed_property('result', CryptoTransactionTO, False)

    def __init__(self, success=False, error=None, result=None):
        super(GetPendingPaymentSignatureDataResponseTO, self).__init__(success, error)
        self.result = result


class ConfirmPaymentRequestTO(object):
    transaction_id = unicode_property('1')
    crypto_transaction = typed_property('2', CryptoTransactionTO, False)


class ConfirmPaymentResponseTO(PaymentRpcResultTO):
    result = typed_property('result', PendingPaymentTO, False)

    def __init__(self, success=False, error=None, result=None):
        super(ConfirmPaymentResponseTO, self).__init__(success, error)
        self.result = result


class UpdatePaymentStatusRequestTO(PendingPaymentTO):
    pass


class UpdatePaymentStatusResponseTO(object):
    pass


class CreateAssetRequestTO(CreatePaymentAssetTO):
    pass


class CreateAssetResponseTO(PaymentRpcResultTO):
    result = typed_property('result', PaymentProviderAssetTO)

    def __init__(self, success=False, error=None, result=None):
        super(CreateAssetResponseTO, self).__init__(success, error)
        self.result = result


class TargetInfoAssetTO(object):
    id = unicode_property('1')
    type = unicode_property('2')


class TargetInfoTO(object):
    name = unicode_property('1')
    assets = typed_property('2', TargetInfoAssetTO, True)

    def __init__(self, name=None, assets=None):
        self.name = name
        self.assets = assets or []


class GetTargetInfoRequestTO(object):
    provider_id = unicode_property('1')
    target = unicode_property('2')
    currency = unicode_property('3')


class GetTargetInfoResponseTO(PaymentRpcResultTO):
    result = typed_property('result', TargetInfoTO)

    def __init__(self, success=False, error=None, result=None):
        super(GetTargetInfoResponseTO, self).__init__(success, error)
        self.result = result


class CreateTransactionResultTO(object):
    params = unicode_property('1')
    transaction_id = unicode_property('2')


class CreateTransactionRequestTO(object):
    provider_id = unicode_property('1')
    params = unicode_property('2')


class CreateTransactionResponseTO(PaymentRpcResultTO):
    result = typed_property('result', CreateTransactionResultTO)

    def __init__(self, success=False, error=None, result=None):
        super(CreateTransactionResponseTO, self).__init__(success, error)
        self.result = result


class PayconiqSettingsTO(TO):
    merchant_id = unicode_property('merchant_id', default=None)
    jwt = unicode_property('jwt', default=None)


class ThreeFoldSettingsTO(TO):
    address = unicode_property('address', default=None)


class ServicePaymentProviderFeeTO(TO):
    amount = long_property('amount', default=0)
    precision = long_property('precision', default=2)
    min_amount = long_property('min_amount', default=0)
    currency = unicode_property('currency')


PAYMENT_SETTINGS_MAPPING = {
    'payconiq': PayconiqSettingsTO,
    'threefold': ThreeFoldSettingsTO,
    'threefold_testnet': ThreeFoldSettingsTO,
}


class ServicePaymentProviderTO(TO):
    provider_id = unicode_property('provider_id')
    enabled = bool_property('enabled')
    fee = typed_property('fee', ServicePaymentProviderFeeTO)  # type: ServicePaymentProviderFeeTO
    settings = typed_property('settings', TO, subtype_mapping=PAYMENT_SETTINGS_MAPPING, subtype_attr_name='provider_id')

    @property
    def can_enable(self):
        # type: () -> bool
        if self.provider_id == 'payconiq':
            return not not (self.settings.merchant_id and self.settings.jwt)
        elif self.provider_id in ['threefold', 'threefold_testnet']:
            return not not self.settings.address

    @property
    def is_enabled(self):
        # type: () -> bool
        return self.enabled and self.can_enable

    @classmethod
    def from_model(cls, model):
        return cls.from_dict({'provider_id': model.provider_id,
                              'enabled': model.enabled,
                              'fee': model.fee.to_dict() if model.fee else {
                                  'amount': ServicePaymentProviderFeeTO.amount.default,
                                  'precision': ServicePaymentProviderFeeTO.precision.default,
                                  'currency': None
                              },
                              'settings': model.settings})


class PayMethodTO(TO):
    amount = long_property('amount')
    currency = unicode_property('currency')
    precision = long_property('precision')
    target = unicode_property('target', default=None)


class GetPaymentMethodsRequestTO(TO):
    service = unicode_property('service')
    test_mode = bool_property('test_mode')
    base_method = typed_property('base_method', BasePaymentMethod)  # type: BasePaymentMethod
    methods = typed_property('methods', PaymentMethodTO, True)  # type: list[PaymentMethodTO]


class PaymentProviderMethodsTO(TO):
    provider = typed_property('provider', AppPaymentProviderTO)
    embedded_app = typed_property('embedded_app', EmbeddedAppTO)
    methods = typed_property('methods', PayMethodTO, True)  # type: list[PayMethodTO]


class GetPaymentMethodsResponseTO(TO):
    methods = typed_property('methods', PaymentProviderMethodsTO, True)  # type: list[PaymentProviderMethodsTO]
