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

import json
import logging
import random

from google.appengine.api import urlfetch

from mcfw.cache import cached
from mcfw.rpc import returns, arguments
from rogerthat.rpc import users
from rogerthat.to.payment import GetPaymentProfileResponseTO, PaymentProviderAssetTO, CreatePaymentAssetTO, \
    CryptoTransactionTO, CreateTransactionResultTO, TargetInfoTO


@returns(GetPaymentProfileResponseTO)
@arguments(app_user=users.User)
def get_payment_profile(app_user):
    raise NotImplementedError(u'get_payment_profile is not implemented yet')


@returns([PaymentProviderAssetTO])
@arguments(app_user=users.User, currency=unicode)
def get_payment_assets(app_user, currency=None):
    return []


@returns(PaymentProviderAssetTO)
@arguments(app_user=users.User, asset_id=unicode)
def get_payment_asset(app_user, asset_id):
    return None


@returns(unicode)
@arguments(app_user=users.User, asset_id=unicode)
def get_payment_asset_currency(app_user, asset_id):
    raise NotImplementedError(u'get_payment_asset_currency is not implemented yet')


@returns(PaymentProviderAssetTO)
@arguments(app_user=users.User, asset=CreatePaymentAssetTO)
def create_payment_asset(app_user, asset):
    raise NotImplementedError(u'create_payment_asset is not implemented yet')


@returns(tuple)
@arguments(app_user=users.User, asset_id=unicode, cursor=unicode)
def get_confirmed_transactions(app_user, asset_id, cursor=None):
    raise NotImplementedError(u'get_confirmed_transactions is not implemented yet')


@returns(tuple)
@arguments(app_user=users.User, asset_id=unicode, cursor=unicode)
def get_pending_transactions(app_user, asset_id, cursor=None):
    raise NotImplementedError(u'get_pending_transactions is not implemented yet')


@returns(bool)
@arguments(app_user=users.User, asset_id=unicode, code=unicode)
def verify_payment_asset(app_user, asset_id, code):
    raise NotImplementedError(u'verify_payment_asset is not implemented yet')


@returns(CryptoTransactionTO)
@arguments(app_user=users.User, transaction_id=unicode, from_asset_id=unicode, to_asset_id=unicode, amount=(int, long),
           currency=unicode, memo=unicode, precision=(int, long))
def get_payment_signature_data(app_user, transaction_id, from_asset_id, to_asset_id, amount, currency, memo, precision):
    return None


@returns(unicode)
@arguments(from_user=users.User, to_user=users.User, transaction_id=unicode, from_asset_id=unicode, to_asset_id=unicode,
           amount=(int, long), currency=unicode, memo=unicode, precision=(int, long), crypto_transaction=CryptoTransactionTO)
def confirm_payment(from_user, to_user, transaction_id, from_asset_id, to_asset_id, amount, currency, memo,
                    precision, crypto_transaction):
    raise NotImplementedError(u'confirm_payment is not implemented yet')


@returns(CreateTransactionResultTO)
@arguments(app_user=users.User, params=unicode)
def create_transaction(app_user, params):
    raise NotImplementedError(u'create_transaction is not implemented yet')


@returns(dict)
@arguments(transaction_id=unicode)
def get_public_transaction(transaction_id):
    base_url = _get_explorer_url()
    return _get_public_transaction(base_url, transaction_id)


def _get_public_transaction(base_url, transaction_id):
    url = '%s/explorer/hashes/%s' % (base_url, transaction_id)
    result = urlfetch.fetch(url)  # type: urlfetch._URLFetchResult
    if result.status_code == 200:
        return json.loads(result.content)
    else:
        logging.error('Failed to get transaction: %s %s', result.status_code, result.content)
        raise Exception(result.content)


@returns(TargetInfoTO)
@arguments(target_user=users.User, currency=unicode, settings=dict)
def get_target_info_service(target_user, currency, settings):
    raise NotImplementedError(u'get_target_info_service is not implemented yet')


def _get_explorer_url():
    urls = [u'https://explorer.threefoldtoken.com', u'https://explorer2.threefoldtoken.com',
            u'https://explorer3.threefoldtoken.com', u'https://explorer4.threefoldtoken.com']
    return random.choice(urls)


@cached(1, lifetime=86400 * 7)
@returns(long)
@arguments(block_id=long)
def get_timestamp_from_block(block_id):
    # type: (long) -> long
    base_url = _get_explorer_url()
    return _get_timestamp_from_block(base_url, block_id)


def _get_timestamp_from_block(base_url, block_id):
    url = '%s/explorer/blocks/%d' % (base_url, block_id)
    result = urlfetch.fetch(url)  # type: urlfetch._URLFetchResult
    if result.status_code == 200:
        block = json.loads(result.content)
        return block['block']['rawblock']['timestamp']
    else:
        raise Exception('Failed to get block timestamp: %s %s' % (result.status_code, result.content))


def _get_total_amount(transaction, service_address):
    total_amount = 0
    raw_transaction = _convert_to_v1_transaction(transaction['transaction']['rawtransaction'])
    if raw_transaction['data']['coinoutputs']:
        for output in raw_transaction['data']['coinoutputs']:
            if output['condition']['data']['unlockhash'] == service_address:
                total_amount += long(output['value'])
    return total_amount


def _convert_to_v1_transaction(transaction):
    if transaction['version'] == 0:
        data = transaction['data']
        return {
            'version': 1,
            'data': {
                'coininputs': map(_convert_to_v1_input, data['coininputs'] or []),
                'coinoutputs': map(_convert_to_v1_output, data['coinoutputs'] or []),
                'arbitrarydata': data.get('arbitrarydata'),
                'blockstakeinputs': map(_convert_to_v1_input, data.get('blockstakeinputs') or []),
                'blockstakeoutputs': map(_convert_to_v1_output, data.get('blockstakeoutputs') or []),
                'minerfees': data['minerfees'],
            }
        }
    else:
        return transaction


def _convert_to_v1_input(input):  # @ReservedAssignment
    return {
        'parentid': input['parentid'],
        'fulfillment': {
            'type': 1,  # single signature
            'data': {
                'publickey': input['unlocker']['condition']['publickey'],
                'signature': input['unlocker']['fulfillment']['signature'],
            }
        }
    }


def _convert_to_v1_output(output):
    return {
        'value': output['value'],
        'condition': {
            'type': 1,  # unlockhash
            'data': {
                'unlockhash': output['unlockhash']
            }
        }
    }
