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

import base64
import imghdr
import importlib
import logging
import uuid

from google.appengine.api import images
from google.appengine.ext import deferred, ndb

from mcfw.consts import MISSING
from mcfw.rpc import returns, arguments
from mcfw.utils import chunks
from rogerthat.bizz.embedded_applications import get_embedded_application
from rogerthat.bizz.job import run_job
from rogerthat.bizz.payment.response_handlers import update_payment_providers_response_handler, \
    update_payment_provider_response_handler, update_payment_assets_response_handler, \
    update_payment_asset_response_handler, update_payment_status_response_handler
from rogerthat.bizz.user import get_lang
from rogerthat.capi.payment import updatePaymentProvider, updatePaymentStatus, updatePaymentProviders, \
    updatePaymentAssets, updatePaymentAsset
from rogerthat.dal.payment import get_payment_provider, get_payment_providers, get_payment_user, get_payment_user_key, \
    get_payment_service, get_payment_service_key
from rogerthat.dal.profile import get_user_profile
from rogerthat.exceptions.payment import PaymentProviderNotFoundException, PaymentProviderAlreadyExistsException, \
    InvalidPaymentProviderException, InvalidPaymentImageException, PaymentProviderNoOauthSettingsException, \
    PaymentException, UnsupportedEmbeddedAppException
from rogerthat.models import Image
from rogerthat.models.apps import EmbeddedApplication, EmbeddedApplicationType
from rogerthat.models.payment import PaymentProvider, PaymentUser, PaymentPendingReceive, PaymentUserProvider, \
    PaymentService, PaymentServiceProvider, ConversionRatio, ConversionRatioValue, PaymentServiceProviderFee
from rogerthat.rpc import users
from rogerthat.rpc.rpc import logError
from rogerthat.settings import get_server_settings
from rogerthat.to.app import EmbeddedAppTO
from rogerthat.to.messaging.forms import PaymentMethodTO
from rogerthat.to.payment import AppPaymentProviderTO, UpdatePaymentProviderRequestTO, UpdatePaymentStatusRequestTO, \
    ErrorPaymentTO, PendingPaymentTO, PendingPaymentDetailsTO, \
    PaymentProviderAssetTO, UpdatePaymentProvidersRequestTO, UpdatePaymentAssetsRequestTO, PaymentProviderTO, \
    CreatePaymentAssetTO, CryptoTransactionTO, GetPaymentProfileResponseTO, TargetInfoTO, TargetInfoAssetTO, \
    CreateTransactionResultTO, GetPaymentMethodsRequestTO, GetPaymentMethodsResponseTO, PaymentProviderMethodsTO, \
    PayMethodTO, ServicePaymentProviderFeeTO, ServicePaymentProviderTO
from rogerthat.to.service import UserDetailsTO
from rogerthat.utils import now
from rogerthat.utils.app import get_app_id_from_app_user, create_app_user_by_email
from rogerthat.utils.service import create_service_identity_user, add_slash_default

IMAGE_MAX_SIZE = 102400  # 100kb


def get_api_module(provider_id, log_error=True):
    module_name = 'rogerthat.bizz.payment.providers.%s.api' % provider_id
    try:
        return importlib.import_module(module_name)
    except ImportError:
        if log_error:
            logging.error('Payment module %s not found', module_name)
        else:
            logging.info('Payment module %s not found', module_name)
        return None


def is_valid_provider_id(provider_id):
    if get_api_module(provider_id, False):
        return True
    return False


def _create_image(image):
    try:
        _meta, img_b64 = image.split(',')
        image = base64.b64decode(img_b64)
    except:
        raise InvalidPaymentImageException()

    image_type = imghdr.what(None, image)
    img = images.Image(image)
    orig_width = img.width
    orig_height = img.height
    if orig_width != orig_height:
        logging.info('Image has an invalid ratio. (expected 1:1, got %s:%s)', orig_width, orig_height)
        raise InvalidPaymentImageException('invalid_aspect_ratio', {'aspect_ratio': '1:1'})

    img = images.Image(image)
    img.resize(250, 250)
    image_model = Image(blob=img.execute_transforms(images.JPEG if image_type == 'jpeg' else images.PNG))
    image_model.put()
    return image_model


def _get_logo_id(original_id, logo):
    if logo is not MISSING and logo:
        image = _create_image(logo)
        if original_id:
            Image.create_key(original_id).delete()
        return image.id
    else:
        return original_id


@returns(PaymentProvider)
@arguments(provider=PaymentProvider, data=PaymentProviderTO)
def _save_provider(provider, data):
    # type: (PaymentProvider, PaymentProviderTO) -> PaymentProvider
    d = data.to_dict(exclude=['id', 'logo', 'black_white_logo', 'oauth_settings', 'conversion_ratio'])
    d.update(
        oauth_settings=data.oauth_settings.to_model() if data.oauth_settings else None,
        logo_id=_get_logo_id(provider.logo_id, data.logo),
        black_white_logo_id=_get_logo_id(provider.black_white_logo_id, data.black_white_logo),
        conversion_ratio=ConversionRatio(base=data.conversion_ratio.base,
                                         values=[ConversionRatioValue(**v.to_dict()) for v in
                                                 data.conversion_ratio.values]) if MISSING.default(
            data.conversion_ratio, None) else None,
        embedded_application=EmbeddedApplication.create_key(data.embedded_application) if MISSING.default(
            data.embedded_application, None) else None
    )
    provider.populate(**d)
    provider.put()
    return provider


@ndb.transactional(xg=True)
@returns(PaymentProvider)
@arguments(data=PaymentProviderTO)
def create_payment_provider(data):
    """
    Args:
        data (CreatePaymentProviderTO)
    """
    provider_id = data.id
    if not is_valid_provider_id(provider_id):
        raise InvalidPaymentProviderException(provider_id)
    if get_payment_provider(provider_id):
        raise PaymentProviderAlreadyExistsException(provider_id)

    provider = PaymentProvider(key=PaymentProvider.create_key(provider_id))
    return _save_provider(provider, data)


@ndb.transactional(xg=True)
@returns(PaymentProvider)
@arguments(provider_id=unicode, data=PaymentProviderTO)
def update_payment_provider(provider_id, data):
    # type: (unicode, PaymentProviderTO) -> PaymentProvider
    provider = get_payment_provider(provider_id)
    if not provider:
        raise PaymentProviderNotFoundException(provider_id)
    if MISSING.default(data.embedded_application, None):
        embedded_app = get_embedded_application(data.embedded_application)
        if EmbeddedApplicationType.WIDGET_PAY not in embedded_app.types:
            raise UnsupportedEmbeddedAppException(embedded_app.name)
    provider = _save_provider(provider, data)
    deferred.defer(send_update_payment_provider_request_to_users, provider_id, _countdown=5, _transactional=True)
    return provider


@returns()
@arguments(provider_id=unicode)
def delete_payment_provider(provider_id):
    provider = get_payment_provider(provider_id)
    if not provider:
        raise PaymentProviderNotFoundException(provider_id)
    to_delete = [provider.key]
    to_put = []

    def filter_by_provider(thing):
        return thing.provider_id != provider_id

    for payment_user in PaymentUser.list_by_provider_id(provider_id):
        payment_user.providers = filter(filter_by_provider, payment_user.providers)
        payment_user.assets = filter(filter_by_provider, payment_user.assets)
        if not payment_user.providers and not payment_user.assets:
            to_delete.append(payment_user.key)
        else:
            to_put.append(payment_user)
    services = PaymentService.list_by_provider_id(provider_id, True).fetch() + PaymentService.list_by_provider_id(
        provider_id, False).fetch()
    for service in services:  # type: PaymentService
        service.providers = filter(filter_by_provider, service.providers)
        service.test_providers = filter(filter_by_provider, service.test_providers)
        if service.providers and service.test_providers:
            to_put.append(service)
        else:
            to_delete.append(service.key)
    for chunk in chunks(to_put, 200):
        ndb.put_multi(chunk)
    for chunk in chunks(to_delete, 200):
        ndb.delete_multi(chunk)


@returns(tuple)
@arguments(provider_id=unicode)
def get_payment_provider_oauth_secrets(provider_id):
    pp = get_payment_provider(provider_id)
    if not pp.oauth_settings:
        raise PaymentProviderNoOauthSettingsException(provider_id)

    return pp.oauth_settings.client_id, pp.oauth_settings.secret


@returns(dict)
@arguments(app_user=users.User, provider_id=unicode)
def get_access_token_for_user(app_user, provider_id):
    payment_user = get_payment_user(app_user)
    if not payment_user:
        return None

    pup = payment_user.get_provider(provider_id)
    if pup:
        return pup.token
    return None


@returns(AppPaymentProviderTO)
@arguments(app_user=users.User, provider_id=unicode)
def get_payment_provider_for_user(app_user, provider_id):
    payment_user = get_payment_user(app_user)
    pp = get_payment_provider(provider_id)
    base_url = get_server_settings().baseUrl
    enabled = payment_user is not None and payment_user.has_provider(pp.id)
    return AppPaymentProviderTO.from_model(base_url, pp, enabled, app_user)


@returns([AppPaymentProviderTO])
@arguments(app_user=users.User)
def get_payment_providers_for_user(app_user):
    pps = get_payment_providers()
    payment_user = get_payment_user(app_user)
    tos = []
    base_url = get_server_settings().baseUrl
    for pp in pps:
        enabled = payment_user is not None and payment_user.has_provider(pp.id)
        tos.append(AppPaymentProviderTO.from_model(base_url, pp, enabled, app_user))
    return tos


@returns(GetPaymentProfileResponseTO)
@arguments(app_user=users.User, provider_id=unicode)
def get_payment_profile(app_user, provider_id):
    return get_api_module(provider_id).get_payment_profile(app_user)


@returns([PaymentProviderAssetTO])
@arguments(app_user=users.User, provider_id=unicode, save=bool)
def get_payment_assets(app_user, provider_id, save=True):
    latest_assets = get_api_module(provider_id).get_payment_assets(app_user)  # type: list[PaymentProviderAssetTO]
    payment_user = get_payment_user(app_user)
    db_assets = payment_user.get_assets_by_provider(provider_id)
    to_assets = {asset.id: asset for asset in latest_assets}

    if not save:
        assets = []
        for asset_id in to_assets:
            assets.append(PaymentProviderAssetTO.from_model(db_assets.get(asset_id), to_assets.get(asset_id)))
        return assets

    for pua in db_assets.values():
        payment_user.assets.remove(pua)

    for asset in latest_assets:
        model = asset.to_model()
        if asset.id in db_assets:
            # merge with existing asset
            db_action = db_assets[asset.id].required_action
            if db_action:
                model.required_action = db_action
        payment_user.assets.append(model)
    payment_user.put()
    return [PaymentProviderAssetTO.from_model(model, to_assets.get(model.asset_id)) for model in payment_user.assets]


@returns(PaymentProviderAssetTO)
@arguments(app_user=users.User, provider_id=unicode, asset_id=unicode)
def get_payment_asset(app_user, provider_id, asset_id):
    asset = get_api_module(provider_id).get_payment_asset(app_user, asset_id)
    pu = get_payment_user(app_user)
    if not pu:
        return None
    db_assets = pu.get_assets_by_provider(provider_id)
    return PaymentProviderAssetTO.from_model(db_assets.get(asset.id), asset)


@returns(PaymentProviderAssetTO)
@arguments(app_user=users.User, asset=CreatePaymentAssetTO)
def create_payment_asset(app_user, asset):
    """
    Args:
        app_user (users.User)
        asset (CreatePaymentAssetTO)
    Raises:
        PaymentException: In case an exception occurred
    """
    new_asset = get_api_module(asset.provider_id).create_payment_asset(app_user, asset)
    assert isinstance(new_asset, PaymentProviderAssetTO)
    payment_user = get_payment_user(app_user)
    payment_user.assets.append(new_asset.to_model())
    payment_user.put()
    # Sync the new asset to the phone
    updatePaymentAsset(update_payment_asset_response_handler, logError, app_user, request=new_asset)
    return new_asset


@returns(TargetInfoTO)
@arguments(app_user=users.User, provider_id=unicode, target=unicode, currency=unicode)
def get_target_info(app_user, provider_id, target, currency):
    target_user = users.User(target)

    if '/' not in target:
        target_service_user = create_service_identity_user(target_user)
    else:
        target_service_user = target_user
    target_info_service = _get_target_info_service(target_service_user, provider_id, currency)
    if target_info_service:
        return target_info_service

    if ':' not in target:
        target_user = create_app_user_by_email(target, get_app_id_from_app_user(app_user))
    return _get_target_info_user(target_user, provider_id, currency)


def _get_target_info_service(target_user, provider_id, currency):
    ps = get_payment_service(target_user)
    if not ps:
        return None
    if not ps.has_provider(provider_id):
        return None

    return get_api_module(provider_id).get_target_info_service(target_user,
                                                               currency,
                                                               ps.get_provider(provider_id).settings)


def _get_target_info_user(target_user, provider_id, currency):
    pu = get_payment_user(target_user)
    if not pu:
        return None

    user_profile = get_user_profile(target_user)

    to = TargetInfoTO()
    to.name = user_profile.name if user_profile else None
    to.assets = []
    for asset in pu.get_assets_by_provider(provider_id).itervalues():
        if asset.currency == currency:
            asset_to = TargetInfoAssetTO()
            asset_to.id = asset.asset_id
            asset_to.type = asset.type
            to.assets.append(asset_to)
    return to


@returns(CreateTransactionResultTO)
@arguments(app_user=users.User, provider_id=unicode, params=unicode)
def create_transaction(app_user, provider_id, params):
    return get_api_module(provider_id).create_transaction(app_user, params)


@returns()
@arguments(app_user=users.User, provider_id=unicode, asset_id=unicode, code=unicode)
def verify_payment_asset(app_user, provider_id, asset_id, code):
    return get_api_module(provider_id).verify_payment_asset(app_user, asset_id, code)


@returns(tuple)
@arguments(app_user=users.User, provider_id=unicode, asset_id=unicode, cursor=unicode, type=unicode)
def get_payment_transactions(app_user, provider_id, asset_id, cursor, type):  # @ReservedAssignment
    if type == u"confirmed":
        return get_api_module(provider_id).get_confirmed_transactions(app_user, asset_id, cursor)
    elif type == u"pending":
        return get_api_module(provider_id).get_pending_transactions(app_user, asset_id, cursor)
    else:
        logging.error(u"Called get_payment_transactions with unknown type: '%s'" % type)
        return [], None


@returns(PendingPaymentTO)
@arguments(app_user=users.User, provider_id=unicode, asset_id=unicode, amount=(int, long), memo=unicode,
           precision=(int, long))
def receive_payment(app_user, provider_id, asset_id, amount, memo, precision):
    currency = get_api_module(provider_id).get_payment_asset_currency(app_user, asset_id)

    if not currency:
        raise PaymentException(ErrorPaymentTO.CURRENCY_UNKNOWN, get_lang(app_user))

    transaction_id = unicode(uuid.uuid4())
    ppr = PaymentPendingReceive(key=PaymentPendingReceive.create_key(transaction_id))
    ppr.timestamp = now()
    ppr.provider_id = provider_id
    ppr.asset_id = asset_id
    ppr.app_user = app_user
    ppr.currency = currency
    ppr.amount = amount
    ppr.memo = memo
    ppr.precision = precision
    ppr.status = PaymentPendingReceive.STATUS_CREATED
    ppr.put()

    return PendingPaymentTO.create(ppr.status, transaction_id)


@returns()
@arguments(app_user=users.User, transaction_id=unicode)
def cancel_payment(app_user, transaction_id):
    ppr = PaymentPendingReceive.create_key(transaction_id).get()
    _validate_transaction_call(ppr, app_user, validate_started=False)

    if ppr.status not in (PaymentPendingReceive.STATUS_CREATED, PaymentPendingReceive.STATUS_SCANNED):
        raise PaymentException(ErrorPaymentTO.TRANSACTION_FINISHED, get_lang(app_user))

    if ppr.app_user == app_user:
        ppr.status = PaymentPendingReceive.STATUS_CANCELLED_BY_RECEIVER
    elif ppr.pay_user and ppr.pay_user == app_user:
        ppr.status = PaymentPendingReceive.STATUS_CANCELLED_BY_PAYER
    else:
        raise PaymentException(ErrorPaymentTO.PERMISSION_DENIED, get_lang(app_user))
    ppr.put()
    deferred.defer(send_update_payment_status_request, ppr)


@returns(PendingPaymentDetailsTO)
@arguments(app_user=users.User, transaction_id=unicode)
def get_pending_payment_details(app_user, transaction_id):
    ppr = PaymentPendingReceive.create_key(transaction_id).get()
    user_profile = get_user_profile(ppr.app_user)
    payment_provider = _validate_transaction_call(ppr, app_user, validate_started=False)
    provider_module = get_api_module(ppr.provider_id)

    status = PaymentPendingReceive.STATUS_SCANNED
    payment_user = get_payment_user(app_user)
    enabled = payment_user is not None and payment_user.has_provider(payment_provider.id)
    base_url = get_server_settings().baseUrl
    provider = AppPaymentProviderTO.from_model(base_url, payment_provider, enabled, app_user)

    assets = []
    if payment_user and payment_user.has_provider(ppr.provider_id):
        assets = provider_module.get_payment_assets(app_user, ppr.currency)
    receiver = UserDetailsTO.fromUserProfile(user_profile)
    receiver_asset = provider_module.get_payment_asset(ppr.app_user, ppr.asset_id)

    ppr.status = status
    ppr.pay_user = app_user
    if ppr.precision is None:
        ppr.precision = 2

    ppr.put()

    deferred.defer(send_update_payment_status_request, ppr)
    return PendingPaymentDetailsTO(status, transaction_id, provider, assets, receiver, receiver_asset, ppr.currency,
                                   ppr.amount, ppr.memo, ppr.timestamp, ppr.precision)


@returns(CryptoTransactionTO)
@arguments(app_user=users.User, transaction_id=unicode, asset_id=unicode)
def get_pending_payment_signature_data(app_user, transaction_id, asset_id):
    ppr = PaymentPendingReceive.create_key(transaction_id).get()
    _validate_transaction_call(ppr, app_user)

    if not ppr.pay_user or ppr.pay_user != app_user:
        raise PaymentException(ErrorPaymentTO.PERMISSION_DENIED, get_lang(app_user))

    if ppr.status not in (PaymentPendingReceive.STATUS_SCANNED,):
        raise PaymentException(ErrorPaymentTO.TRANSACTION_FINISHED, get_lang(app_user))
    try:
        ppr.status = PaymentPendingReceive.STATUS_SIGNATURE
        ppr.pay_asset_id = asset_id
        return get_api_module(ppr.provider_id).get_payment_signature_data(app_user, transaction_id, asset_id,
                                                                          ppr.asset_id, ppr.amount, ppr.currency,
                                                                          ppr.memo, ppr.precision)
    except PaymentException:
        raise
    except Exception as e:
        logging.exception(e)
        ppr.status = PaymentPendingReceive.STATUS_FAILED
        raise PaymentException(ErrorPaymentTO.UNKNOWN, get_lang(app_user))
    finally:
        ppr.put()
        deferred.defer(send_update_payment_status_request, ppr)


def _validate_transaction_call(pending_payment, app_user, validate_started=True):
    # type: (PaymentPendingReceive, users.User) -> PaymentProvider
    if not pending_payment:
        raise PaymentException(ErrorPaymentTO.TRANSACTION_NOT_FOUND, get_lang(app_user))
    payment_provider = get_payment_provider(pending_payment.provider_id)
    if not payment_provider:
        raise PaymentException(ErrorPaymentTO.PROVIDER_NOT_FOUND, get_lang(app_user))
    if validate_started and not pending_payment.pay_user:
        raise PaymentException(ErrorPaymentTO.TRANSACTION_NOT_INITIATED, get_lang(app_user))
    return payment_provider


@returns(PendingPaymentTO)
@arguments(app_user=users.User, transaction_id=unicode, crypto_transaction=CryptoTransactionTO)
def confirm_payment(app_user, transaction_id, crypto_transaction):
    ppr = PaymentPendingReceive.create_key(transaction_id).get()
    _validate_transaction_call(ppr, app_user)

    if not ppr.pay_user or ppr.pay_user != app_user:
        raise PaymentException(ErrorPaymentTO.PERMISSION_DENIED, get_lang(app_user))

    if ppr.status not in (PaymentPendingReceive.STATUS_SIGNATURE,):
        raise PaymentException(ErrorPaymentTO.TRANSACTION_FINISHED, get_lang(app_user))

    try:
        ppr.status = get_api_module(ppr.provider_id).confirm_payment(ppr.pay_user, ppr.app_user, transaction_id,
                                                                     ppr.pay_asset_id,
                                                                     ppr.asset_id, ppr.amount, ppr.currency, ppr.memo,
                                                                     ppr.precision, crypto_transaction)
        if ppr.status == PaymentPendingReceive.STATUS_CONFIRMED:
            deferred.defer(sync_payment_asset, app_user, ppr.provider_id, ppr.pay_asset_id)
            deferred.defer(sync_payment_asset, ppr.app_user, ppr.provider_id, ppr.asset_id)
        return PendingPaymentTO.create(ppr.status, transaction_id)
    except Exception as e:
        logging.exception(e)
        ppr.status = PaymentPendingReceive.STATUS_FAILED
        raise PaymentException(ErrorPaymentTO.UNKNOWN, get_lang(app_user))
    finally:
        ppr.put()
        deferred.defer(send_update_payment_status_request, ppr)


def get_and_update_payment_database_info(app_user):
    pps = get_payment_providers()
    payment_user = get_payment_user(app_user)

    added_providers = {}

    provider_list = []
    asset_list = []

    if not payment_user:
        payment_user_key = get_payment_user_key(app_user)
        payment_user = PaymentUser(key=payment_user_key)
        payment_user.providers = []
        payment_user.assets = []
        payment_user.put()

    for pp in pps:
        pp_enabled = payment_user.has_provider(pp.id)
        try:
            assets = get_payment_assets(app_user, pp.id, False)
            if not assets:
                continue

            provider_list.append(pp)

            if not pp_enabled and pp.id not in added_providers:
                payment_user.providers.append(PaymentUserProvider(provider_id=pp.id, token=None))
                added_providers[pp.id] = []

            elif pp.id not in added_providers:
                db_assets = payment_user.get_assets_by_provider(pp.id)
                for pua in db_assets.values():
                    payment_user.assets.remove(pua)

                added_providers[pp.id] = []

            for asset in assets:
                asset_enabled = payment_user.has_asset(pp.id, asset.id)
                if not asset_enabled:
                    if pp.id not in added_providers:
                        added_providers[pp.id] = []

                    if asset.id not in added_providers[pp.id]:
                        added_providers[pp.id].append(asset.id)
                        payment_user.assets.append(asset.to_model())

            asset_list.extend(assets)
        except:
            logging.exception("Failed to sync_app_database for provider '%s'", pp.id)

    if added_providers:
        payment_user.put()

    return provider_list, asset_list


@returns()
@arguments(app_user=users.User)
def sync_payment_database(app_user):
    provider_list, asset_list = get_and_update_payment_database_info(app_user)
    base_url = get_server_settings().baseUrl

    request = UpdatePaymentProvidersRequestTO()
    request.provider_ids = []  # empty array clears all providers
    request.payment_providers = [UpdatePaymentProviderRequestTO.from_model(base_url, pp, True, app_user) for pp
                                 in provider_list]
    updatePaymentProviders(update_payment_providers_response_handler, logError, app_user, request=request)

    request = UpdatePaymentAssetsRequestTO()
    request.provider_ids = []  # empty array clears all assets
    request.assets = asset_list
    updatePaymentAssets(update_payment_assets_response_handler, logError, app_user, request=request)


@returns()
@arguments(app_user=users.User, provider_id=unicode, save=bool)
def sync_payment_assets(app_user, provider_id, save=False):
    """
    Args:
        app_user (users.User)
        provider_id (unicode)
        save (bool)
    """
    logging.debug('Syncing payment assets for user %s and provider %s', app_user.email(), provider_id)
    request = UpdatePaymentAssetsRequestTO()
    request.provider_ids = [provider_id]  # Updates all assets of this provider_id
    request.assets = get_payment_assets(app_user, provider_id, save)
    updatePaymentAssets(update_payment_assets_response_handler, logError, app_user, request=request)


@returns()
@arguments(app_user=users.User, provider_id=unicode, asset_id=unicode)
def sync_payment_asset(app_user, provider_id, asset_id):
    request = get_payment_asset(app_user, provider_id, asset_id)
    if not request:
        return
    updatePaymentAsset(update_payment_asset_response_handler, logError, app_user, request=request)


@returns()
@arguments(provider_id=unicode)
def send_update_payment_provider_request_to_users(provider_id):
    base_url = get_server_settings().baseUrl
    pp = get_payment_provider(provider_id)
    run_job(send_update_payment_provider_request_query, [provider_id], send_update_payment_provider_request_worker,
            [base_url, pp])


def send_update_payment_provider_request_query(provider_id):
    return PaymentUser.list_by_provider_id(provider_id)


def send_update_payment_provider_request_worker(payment_user_key, base_url, pp):
    payment_user = payment_user_key.get()
    enabled = payment_user.has_provider(pp.id)
    request = UpdatePaymentProviderRequestTO.from_model(base_url, pp, enabled, payment_user.user)
    updatePaymentProvider(update_payment_provider_response_handler, logError, payment_user.user, request=request)


@returns()
@arguments(ppr=PaymentPendingReceive)
def send_update_payment_status_request(ppr):
    send_update_payment_status_request_to_user(ppr.app_user, ppr.transaction_id, ppr.status)
    if ppr.pay_user:
        send_update_payment_status_request_to_user(ppr.pay_user, ppr.transaction_id, ppr.status)


@returns()
@arguments(app_user=users.User, transaction_id=unicode, status=unicode)
def send_update_payment_status_request_to_user(app_user, transaction_id, status):
    request = UpdatePaymentStatusRequestTO.create(status, transaction_id)
    updatePaymentStatus(update_payment_status_response_handler, logError, app_user, request=request)


@returns(PaymentServiceProvider)
@arguments(service_identity_user=users.User, provider_id=unicode, settings=dict, test_mode=bool, enabled=bool,
           fee=ServicePaymentProviderFeeTO)
def service_put_provider(service_identity_user, provider_id, settings, test_mode=False, enabled=True, fee=None):
    # type: (users.User, unicode, dict, bool, object, ServicePaymentProviderFeeTO) -> PaymentServiceProvider
    psp = PaymentServiceProvider(provider_id=provider_id,
                                 settings=settings,
                                 fee=PaymentServiceProviderFee(**fee.to_dict()),
                                 enabled=enabled)

    ps_key = get_payment_service_key(service_identity_user)

    def trans():
        ps = ps_key.get()
        if not ps:
            ps = PaymentService(key=ps_key)
        ps.remove_provider(provider_id, test_mode)
        ps.add_provider(psp, test_mode)
        ps.put()
        return ps.get_provider(provider_id, test_mode)

    return ndb.transaction(trans)


@returns(PaymentServiceProvider)
@arguments(service_identity_user=users.User, provider_id=unicode, test_mode=bool)
def service_get_provider(service_identity_user, provider_id, test_mode=False):
    # type: (users.User, unicode, bool) -> PaymentServiceProvider
    ps = get_payment_service(service_identity_user)
    if not ps:
        return None
    return ps.get_provider(provider_id, test_mode)


@returns()
@arguments(service_identity_user=users.User, provider_id=unicode, test_mode=bool)
def service_delete_provider(service_identity_user, provider_id, test_mode=False):
    def trans():
        ps = get_payment_service(service_identity_user)
        if ps and ps.remove_provider(provider_id, test_mode):
            ps.put()

    ndb.transaction(trans)


@returns([PaymentServiceProvider])
@arguments(service_identity_user=users.User, test_mode=bool)
def service_get_providers(service_identity_user, test_mode=False):
    # type: (users.User, bool) -> list[PaymentServiceProvider]
    ps = get_payment_service(service_identity_user)
    if not ps:
        return []
    return ps.get_providers(test_mode)


def get_payment_methods(request, app_user):
    # type: (GetPaymentMethodsRequestTO, users.User) -> GetPaymentMethodsResponseTO
    providers = ndb.get_multi([PaymentProvider.create_key(m.provider_id) for m in request.methods])
    response = GetPaymentMethodsResponseTO(methods=[])
    base_url = get_server_settings().baseUrl
    payment_user = get_payment_user(app_user)
    methods_per_provider = {}
    _service_providers = service_get_providers(add_slash_default(users.User(request.service)), request.test_mode)
    service_providers = {p.provider_id: p for p in _service_providers}  # type: dict[str, ServicePaymentProviderTO]
    base_amount = float(request.base_method.amount) / pow(10, request.base_method.precision)
    embedded_apps = {e.name: e for e in ndb.get_multi([provider.embedded_application for provider in providers])}
    for provider, method in zip(providers, request.methods):  # type: (PaymentProvider, PaymentMethodTO)
        if not provider:
            logging.error('Payment provider %s not found', method.provider_id)
            continue
        service_provider = service_providers.get(method.provider_id)
        if not service_provider:
            logging.error('Service provider not found: %s', method.provider_id)
            continue
        if provider.id not in methods_per_provider:
            methods_per_provider[provider.id] = []
            enabled = payment_user is not None and payment_user.has_provider(provider.id)
            response.methods.append(PaymentProviderMethodsTO(
                provider=AppPaymentProviderTO.from_model(base_url, provider, enabled, app_user),
                embedded_app=EmbeddedAppTO.from_model(embedded_apps[provider.embedded_application.id()]),
                methods=methods_per_provider[provider.id]
            ))
        if method.calculate_amount:
            fee_rate = provider.get_currency_rate(service_provider.fee.currency, method.currency)
            min_fee_float = float(service_provider.fee.min_amount / fee_rate) / pow(10, service_provider.fee.precision)
            fee = float(service_provider.fee.amount / fee_rate) / pow(10, service_provider.fee.precision)
            base_amount_for_provider = base_amount / provider.get_currency_rate(request.base_method.currency,
                                                                                method.currency)
            if base_amount_for_provider < min_fee_float:
                base_amount_for_provider += fee
            amount = long(round(base_amount_for_provider * pow(10, method.precision)))
            methods_per_provider[provider.id].append(PayMethodTO(amount=amount, **method.to_dict(exclude=['amount'])))
        else:
            methods_per_provider[provider.id].append(PayMethodTO(**method.to_dict()))
    return response
