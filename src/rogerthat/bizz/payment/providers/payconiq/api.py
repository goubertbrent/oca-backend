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

import binascii
import json
import logging
import uuid

from google.appengine.api import urlfetch
from google.appengine.ext import ndb, deferred

from mcfw.properties import azzert
from mcfw.rpc import returns, arguments
from rogerthat.bizz.payment import send_update_payment_status_request_to_user
from rogerthat.bizz.payment.providers.payconiq.consts import PAYMENT_PROVIDER_ID
from rogerthat.bizz.payment.providers.payconiq.models import PayconiqTransaction
from rogerthat.bizz.user import get_lang
from rogerthat.consts import DEBUG, FAST_QUEUE
from rogerthat.dal.payment import get_payment_service, get_payment_provider
from rogerthat.exceptions.payment import PaymentException
from rogerthat.models.payment import PaymentPendingReceive
from rogerthat.rpc import users
from rogerthat.settings import get_server_settings
from rogerthat.to.payment import GetPaymentProfileResponseTO, PaymentProviderAssetTO, CreatePaymentAssetTO, \
    ErrorPaymentTO, CreateTransactionResultTO, TargetInfoTO
from rogerthat.translations import localize
from rogerthat.utils import now
from rogerthat.utils.service import create_service_identity_user, add_slash_default


def web_callback(handler, path, params):
    """
    Args:
        handler (webapp2.RequestHandler)
        path (unicode)
        params (dict)
    """
    if u'transaction/update' == path:
        handle_update_transaction_status(handler, params)
    else:
        handler.abort(404)


def get_public_key(hostname):
    if DEBUG:
        # The code below does not work on dev servers
        # but we return the subjectPublicKeyInfo for dev.payconiq.com
        return '0\x82\x01"0\r\x06\t*\x86H\x86\xf7\r\x01\x01\x01\x05\x00\x03\x82\x01\x0f\x000\x82\x01\n\x02\x82\x01\x01\x00\xd0\x1d8S8\x96\xfd\x9c\xc3\x0f\x0f\x17\x7f\xfe!Ac\xc7hS\xda\xe7f\x05\xee\x1eM\x884|N7\x9e\xd0\xab0c\xf1h\xf9Y\xb7\xe5\xed\xd1G\xe2%\xf1\xd3\xe5\x0f\ti&\xaa\x83m>\x9d\x89@\xe0\x19E\x0e\xfc\xeb\xb8\\\x08TL\xcd\x0c,\xab\xfd\xa7h<\x0cj\xbb\xd7\xf3\x15=\xed1\x0f\xcd\x1b=/\xf1\x8by\xaa\xc1$\xd3"\x1b\xc3\xb7n\xa6\x00\xe8\xc6\x8d%\xfc\xdf\xc4\xfd/\x86\xe6\xba^dK\xb2\x8fQ\xa8(\nxU\xd6K\xd7@\xd7#\x01Qjr\x17\xb1\xd3\xc0B,)\tC\x14\x98\x0b\xa2\xcb\x0c<kI`\xe9\xd7ne\xa9\x99\r\xd4b\xd1P\x94.\xe4\xd9\x80\x96\xf1\x02\xde-\xb4\rt\xb5\x80\xc0Y\xea\xda\x1ds\xc4\xae\xcf\x1b\xa2!\x95C\x15;\x01\x8c8^\x03$\xc4\xad\xe3\xf02\'.\x17N\x95**\xff\x01\x0f\x97\xc8\'\xda\xec\xfcoN\x06\x9f<\xf8g\xe3L\x91\xd9@K\xe6\xd8\xd9\x03O\xedz\xbdd\xa7/\xd7O\x02\x03\x01\x00\x01'

    # https://stackoverflow.com/a/12921889
    import ssl
    from binascii import a2b_base64
    from Crypto.Util.asn1 import DerSequence

    pem = ssl.get_server_certificate((hostname, 443))
    lines = pem.replace(" ", '').split()
    der = a2b_base64(''.join(lines[1:-1]))

    cert = DerSequence()
    cert.decode(der)
    tbsCertificate = DerSequence()
    tbsCertificate.decode(cert[0])
    subjectPublicKeyInfo = tbsCertificate[6]
    return subjectPublicKeyInfo


def handle_update_transaction_status(handler, params):
    transaction_id = handler.request.get('id')
    if not transaction_id:
        logging.debug('Missing id parameter')
        handler.abort(400)
        return

    transaction = PayconiqTransaction.create_key(transaction_id).get()
    if not transaction:
        logging.debug('Transaction not found')
        handler.abort(400)
        return

    target_user = users.User(transaction.target)
    if '/' not in transaction.target:
        target_user = create_service_identity_user(target_user)
    ps = get_payment_service(target_user)
    if not ps:
        logging.debug('payment service not found')
        handler.abort(400)
        return

    if not ps.has_provider(PAYMENT_PROVIDER_ID, transaction.test_mode):
        logging.debug("payment service has no payconiq provider")
        handler.abort(400)
        return

    settings = ps.get_provider(PAYMENT_PROVIDER_ID, transaction.test_mode).settings
    if not settings.get('merchant_id'):
        logging.debug("payment service has no merchant_id")
        handler.abort(400)
        return

    logging.debug(handler.request.headers)
    logging.debug(handler.request.body)

    payconiq_signature = handler.request.headers.get("X-Security-Signature", None)
    payconiq_timestamp = handler.request.headers.get("X-Security-Timestamp", None)
    payconiq_key_url = handler.request.headers.get("X-Security-Key", None)
    payconiq_algorithm = handler.request.headers.get("X-Security-Algorithm", None)

    if payconiq_algorithm != 'SHA256WithRSA':
        logging.debug('Invalid algoritm')
        handler.abort(400)
        return

    if payconiq_key_url not in ("https://dev.payconiq.com", "https://api.payconiq.com",):
        logging.debug('Could not verify signature, unknown key')
        handler.abort(400)
        return

    pub_key = get_public_key(payconiq_key_url.replace('https://', ''))

    crc32 = '{:x}'.format(binascii.crc32(handler.request.body.encode('utf-8')) & 0xffffffff)
    expected_sig = '{}|{}|{}'.format(settings.get('merchant_id'), payconiq_timestamp, crc32).encode('utf-8')
    logging.debug(expected_sig)
    if not _verify_sign(pub_key, payconiq_signature, expected_sig):
        logging.debug('Verification failed')
        handler.abort(400)
        return

    status = json.loads(handler.request.body)['status'].lower()
    deferred.defer(_update_transaction_status, transaction_id, status, _queue=FAST_QUEUE)


@returns(GetPaymentProfileResponseTO)
@arguments(app_user=users.User)
def get_payment_profile(app_user):
    response = GetPaymentProfileResponseTO()
    response.first_name = u'FAKE fn'
    response.last_name = u'FAKE ln'
    return response


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
    return None


@returns(PaymentProviderAssetTO)
@arguments(app_user=users.User, asset=CreatePaymentAssetTO)
def create_payment_asset(app_user, asset):
    language = get_lang(app_user)
    raise PaymentException(ErrorPaymentTO.ACCOUNT_ALREADY_EXISTS, language,
                           {'currency': asset.currency})


@returns(tuple)
@arguments(asset_id=unicode, transaction_type=unicode, cursor=unicode)
def _get_transactions_by_type(asset_id, transaction_type, cursor):
    return [], None


@returns(tuple)
@arguments(app_user=users.User, asset_id=unicode, cursor=unicode)
def get_confirmed_transactions(app_user, asset_id, cursor=None):
    return _get_transactions_by_type(asset_id, u"confirmed", cursor)


@returns(tuple)
@arguments(app_user=users.User, asset_id=unicode, cursor=unicode)
def get_pending_transactions(app_user, asset_id, cursor=None):
    return _get_transactions_by_type(asset_id, u"pending", cursor)


@returns(bool)
@arguments(app_user=users.User, asset_id=unicode, code=unicode)
def verify_payment_asset(app_user, asset_id, code):
    raise NotImplementedError(u'verify_payment_asset is not implemented yet')


@returns(CreateTransactionResultTO)
@arguments(app_user=users.User, params=unicode)
def create_transaction(app_user, params):
    payload = json.loads(params)
    test_mode = payload.get('test_mode', False)
    target = payload['target']
    target_user = add_slash_default(users.User(target))
    ps = get_payment_service(target_user)
    if not ps:
        logging.debug('Payment service for target user %s not found', target_user)
        raise PaymentException(ErrorPaymentTO.UNKNOWN, get_lang(app_user))
    if not ps.has_provider(PAYMENT_PROVIDER_ID, test_mode):
        logging.debug("payment service has no payconiq provider")
        raise PaymentException(ErrorPaymentTO.UNKNOWN, get_lang(app_user))

    settings = ps.get_provider(PAYMENT_PROVIDER_ID, test_mode).settings
    if not settings.get('jwt'):
        logging.debug("payment service has no jwt")
        raise PaymentException(ErrorPaymentTO.UNKNOWN, get_lang(app_user))

    headers = {
        'Authorization': settings.get('jwt'),
        'Cache-Control': u'no-cache',
        'Content-Type': u'application/json'
    }

    if 'message_key' in payload:
        transaction_id = payload['message_key']
        transaction = PayconiqTransaction.create_key(transaction_id).get()  # type: PayconiqTransaction
        if transaction:
            transaction_already_finished = False
            if transaction.status == PayconiqTransaction.STATUS_SUCCEEDED:
                transaction_already_finished = True

            elif transaction.payconic_transaction_id and \
                    payconiq_transaction_finished(transaction.test_mode, transaction.payconic_transaction_id, headers):
                transaction_already_finished = True
                deferred.defer(_update_transaction_status, transaction_id,
                               PayconiqTransaction.STATUS_SUCCEEDED, _queue=FAST_QUEUE)

            if transaction_already_finished:
                raise PaymentException(ErrorPaymentTO.TRANSACTION_FINISHED, get_lang(app_user),
                                       data=json.dumps({u'provider_id': PAYMENT_PROVIDER_ID,
                                                        u'transaction_id': payload['message_key'],
                                                        u'payconiq_transaction_id': transaction.payconic_transaction_id,
                                                        u'payconic_transaction_url': transaction.transaction_url,
                                                        u'success': True,
                                                        u'status': transaction.status}))
    else:
        transaction_id = unicode(uuid.uuid4())

    currency = payload['currency']
    amount = long(payload['amount'])
    precision = long(payload['precision'])
    memo = u"%s\n%s: %s" % (payload['memo'] or u'',
                            localize(get_lang(app_user), u'payments.ref'),
                            transaction_id)

    transaction = PayconiqTransaction(key=PayconiqTransaction.create_key(transaction_id),
                                      timestamp=now(),
                                      test_mode=test_mode,
                                      target=target,
                                      currency=currency,
                                      amount=amount,
                                      precision=precision,
                                      memo=memo,
                                      app_user=app_user,
                                      status=PayconiqTransaction.STATUS_PENDING)
    transaction.put()

    payconiq_amount_float = round(float(amount) / pow(10, precision), precision)
    payconiq_amount = long(payconiq_amount_float * 100)  # needs to be in cents

    if DEBUG:
        payment_provider = get_payment_provider(PAYMENT_PROVIDER_ID)
        base_url = payment_provider.get_setting('test_base_url')
        azzert(base_url)
    else:
        base_url = get_server_settings().baseUrl

    payload = json.dumps({
        'amount': payconiq_amount,
        'description': memo,
        'currency': currency,
        'callbackUrl': u'%s/payments/callbacks/payconiq/transaction/update?id=%s' % (base_url, transaction_id)
    })

    url = ('https://dev.payconiq.com' if test_mode else 'https://api.payconiq.com') + '/v2/transactions'
    logging.debug('Sending request to %s\n%s', url, payload)
    result = urlfetch.fetch(
        url=url,
        payload=payload,
        method=urlfetch.POST,
        headers=headers,
        deadline=10)  # type: urlfetch._URLFetchResult

    if result.status_code not in (201,):
        logging.info('Status:%s Content: %s', result.status_code, result.content)
        raise PaymentException(ErrorPaymentTO.UNKNOWN, get_lang(app_user))

    logging.debug(result.content)
    logging.debug(result.headers)
    payconic_transaction_id = json.loads(result.content)['transactionId']

    deferred.defer(_update_transaction_with_payconiq_info, transaction_id, payconic_transaction_id, _queue=FAST_QUEUE)

    r = CreateTransactionResultTO()
    r.params = json.dumps({
        u'app_user': app_user.email(),
        u'success': True,
        u'provider_id': PAYMENT_PROVIDER_ID,
        u'transaction_id': transaction_id,
        u'status': u'pending',
        u'payconic_transaction_id': payconic_transaction_id
    }).decode('utf8')
    r.transaction_id = transaction_id
    return r


@returns(dict)
@arguments(transaction_id=unicode)
def get_public_transaction(transaction_id):
    transaction = PayconiqTransaction.create_key(transaction_id).get()  # type: PayconiqTransaction
    if not transaction:
        return None
    result = transaction.to_dict(include={'timestamp', 'currency', 'amount', 'precision', 'status'})
    result['id'] = transaction_id
    return result


@returns(TargetInfoTO)
@arguments(target_user=users.User, currency=unicode, settings=dict)
def get_target_info_service(target_user, currency, settings):
    return None


def _update_transaction_with_payconiq_info(transaction_id, payconic_transaction_id):
    def trans():
        transaction = PayconiqTransaction.create_key(transaction_id).get()
        transaction.payconic_transaction_id = payconic_transaction_id
        transaction.put()

    ndb.transaction(trans)


def _update_transaction_status(transaction_id, status):
    def trans():
        transaction = PayconiqTransaction.create_key(transaction_id).get()
        if transaction.status != PayconiqTransaction.STATUS_PENDING and transaction.status != status:
            return

        transaction.status = status
        transaction.put()

        deferred.defer(send_update_payment_status_request_to_user, transaction.app_user, transaction_id, status,
                       _transactional=True, _queue=FAST_QUEUE)

    ndb.transaction(trans)


def _verify_sign(pub_key, signature, data):
    from Crypto.PublicKey import RSA
    from Crypto.Signature import PKCS1_v1_5
    from Crypto.Hash import SHA256
    from base64 import b64decode

    rsakey = RSA.importKey(pub_key)
    signer = PKCS1_v1_5.new(rsakey)

    digest = SHA256.new()
    digest.update(data)

    if signer.verify(digest, b64decode(signature)):
        return True
    return False


def payconiq_transaction_finished(test_mode, transaction_id, headers):
    url = ('https://dev.payconiq.com' if test_mode else 'https://api.payconiq.com') + \
        '/v2/transactions/' + transaction_id
    result = urlfetch.fetch(url=url, headers=headers, deadline=10)

    if result.status_code not in (200,):
        return False

    status = json.loads(result.content)['status'].lower()
    if status == PayconiqTransaction.STATUS_SUCCEEDED:
        return True
    return False
