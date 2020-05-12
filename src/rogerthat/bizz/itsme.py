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

import json
import logging
import string
import urllib

from google.appengine.api import urlfetch

from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from jose import jwt, jws
from jose.utils import base64url_decode, base64_to_long
from mcfw.cache import cached
from mcfw.properties import unicode_list_property, bool_property, unicode_property
from mcfw.rpc import arguments, returns
from rogerthat.models import OpenIdSettings
from rogerthat.to import TO
from rogerthat.utils import guid, now


class OpenIdConfig(TO):
    acr_values_supported = unicode_list_property('acr_values_supported')  # type: list[unicode]
    authorization_endpoint = unicode_property('authorization_endpoint')  # type: unicode
    claim_types_supported = unicode_list_property('claim_types_supported')  # type: list[unicode]
    claims_parameter_supported = bool_property('claims_parameter_supported')  # type: bool
    claims_supported = unicode_list_property('claims_supported')  # type: list[unicode]
    display_values_supported = unicode_list_property('display_values_supported')  # type: list[unicode]
    grant_types_supported = unicode_list_property('grant_types_supported')  # type: list[unicode]
    id_token_encryption_alg_values_supported = unicode_list_property(
        'id_token_encryption_alg_values_supported')  # type: list[unicode]
    id_token_encryption_enc_values_supported = unicode_list_property(
        'id_token_encryption_enc_values_supported')  # type: list[unicode]
    id_token_signing_alg_values_supported = unicode_list_property(
        'id_token_signing_alg_values_supported')  # type: list[unicode]
    issuer = unicode_property('issuer')  # type: unicode
    jwks_uri = unicode_property('jwks_uri')  # type: unicode
    registration_endpoint = unicode_property('registration_endpoint')  # type: list[unicode]
    request_object_encryption_alg_values_supported = unicode_list_property(
        'request_object_encryption_alg_values_supported')  # type: list[unicode]
    request_object_encryption_enc_values_supported = unicode_list_property(
        'request_object_encryption_enc_values_supported')  # type: list[unicode]
    request_object_signing_alg_values_supported = unicode_list_property(
        'request_object_signing_alg_values_supported')  # type: list[unicode]
    request_parameter_supported = bool_property('request_parameter_supported')  # type: bool
    request_uri_parameter_supported = bool_property('request_uri_parameter_supported')  # type: bool
    require_request_uri_registration = bool_property('require_request_uri_registration')  # type: bool
    response_types_supported = unicode_list_property('response_types_supported')  # type: list[unicode]
    scopes_supported = unicode_list_property('scopes_supported')  # type: list[unicode]
    subject_types_supported = unicode_list_property('subject_types_supported')  # type: list[unicode]
    token_endpoint = unicode_property('token_endpoint')  # type: unicode
    token_endpoint_auth_methods_supported = unicode_list_property(
        'token_endpoint_auth_methods_supported')  # type: list[unicode]
    token_endpoint_auth_signing_alg_values_supported = unicode_list_property(
        'token_endpoint_auth_signing_alg_values_supported')  # type: list[unicode]
    ui_locales_supported = unicode_list_property('ui_locales_supported')  # type: list[unicode]
    userinfo_encryption_alg_values_supported = unicode_list_property(
        'userinfo_encryption_alg_values_supported')  # type: list[unicode]
    userinfo_encryption_enc_values_supported = unicode_list_property(
        'userinfo_encryption_enc_values_supported')  # type: list[unicode]
    userinfo_endpoint = unicode_property('userinfo_endpoint')  # type: unicode
    userinfo_signing_alg_values_supported = unicode_list_property(
        'userinfo_signing_alg_values_supported')  # type: list[unicode]


def get_itsme_openid_settings(app_id):
    # type: (str) -> OpenIdSettings
    return OpenIdSettings.create_key(OpenIdSettings.PROVIDER_ITSME, app_id).get()


def get_itsme_openid_config(settings):
    # type: (OpenIdSettings) -> OpenIdConfig
    return OpenIdConfig.from_dict(fetch_cached(settings.configuration_url))


@arguments(openid_config=OpenIdConfig, settings=OpenIdSettings)
def create_client_assertion_jwt(openid_config, settings):
    parsed_key = settings.signature_private_key
    claims = {
        'iss': settings.client_id,
        'sub': settings.client_id,
        'aud': openid_config.token_endpoint,
        # A unique identifier for the token, which can be used to prevent reuse of the token.
        # These tokens MUST only be used once. It is a case-sensitive string.
        'jti': guid(),
        'exp': now() + 300
    }
    logging.debug('Claims: %s', claims)
    token = jwt.encode(claims, parsed_key, openid_config.token_endpoint_auth_signing_alg_values_supported[0])
    logging.debug(token)
    return token


def get_authorization_token(code, openid_config, settings, redirect_url):
    # type: (str, OpenIdConfig, OpenIdSettings, str) -> dict
    post_body = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_url,
        'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
        'client_assertion': create_client_assertion_jwt(openid_config, settings)
    }
    url = openid_config.token_endpoint
    payload = urllib.urlencode(post_body)
    logging.info('Request to itsme: %s\n%s', url, payload)
    token_result = urlfetch.fetch(url, payload, urlfetch.POST, deadline=15)  # type: urlfetch._URLFetchResult
    logging.info('%s\n%s\n%s', token_result.status_code, token_result.headers, token_result.content)
    if token_result.status_code != 200:
        raise Exception('Invalid response from itsme: %s %s' % (token_result.status_code, token_result.content))
    return json.loads(token_result.content)


@cached(1, 3600)
@returns(dict)
@arguments(url=unicode)
def fetch_cached(url):
    result = urlfetch.fetch(url, deadline=15)  # type: urlfetch._URLFetchResult
    if result.status_code == 200:
        return json.loads(result.content)
    else:
        raise Exception('Invalid response: %s %s' % (result.status_code, result.content))


def decrypt_keys(private_key, encrypted_key):
    # type: (dict, str) -> dict
    assert len(encrypted_key) == 256
    n = base64_to_long(private_key['n'])
    e = base64_to_long(private_key['e'])
    d = base64_to_long(private_key['d'])
    key = PKCS1_OAEP.new(RSA.construct((n, e, d))).decrypt(encrypted_key)
    return {
        'aes': key[16:],
        'mac': key[:16]
    }


def parse_payload(payload):
    # type: (str) -> (dict, str, str, str, str)
    split_result = payload.split('.')
    headers = json.loads(base64url_decode(split_result[0]))
    encrypted_key = base64url_decode(split_result[1])
    iv = base64url_decode(split_result[2])
    ciphertext = split_result[3]
    tag = base64url_decode(split_result[4])
    assert len(iv) == 16
    return headers, encrypted_key, iv, ciphertext, tag


def decode_userinfo_result(openid_config, private_key, result):
    # type: (OpenIdConfig, str, str) -> dict
    headers, encrypted_key, iv, ciphertext, tag = parse_payload(result)
    # Decrypt the key using our private key
    decrypted_keys = decrypt_keys(private_key, encrypted_key)
    # Use the decrypted key to decrypt the ciphertext to a JWT
    decipher = AES.new(decrypted_keys['aes'], AES.MODE_CBC, IV=iv)
    decrypted = decipher.decrypt(base64url_decode(ciphertext))  # type: str
    # Verifies the JWT and returns the claims
    issuer_jwkset = fetch_cached(openid_config.jwks_uri)
    algorithms = openid_config.userinfo_signing_alg_values_supported
    # Remove excess invisible characters at end of JWT that sometimes are added for some reason
    # This fixes the jwt verification not working (incorrect padding)
    decrypted = ''.join([letter for letter in decrypted if letter in string.printable]).strip()
    return json.loads(jws.verify(decrypted, issuer_jwkset, algorithms=algorithms))


def get_userinfo(server_settings, openid_config, token):
    # type: (OpenIdSettings, OpenIdConfig, dict) -> dict
    headers = {
        'Authorization': '%s %s' % (token['token_type'], token['access_token'])
    }
    result = urlfetch.fetch(openid_config.userinfo_endpoint, headers=headers,
                            deadline=15)  # type: urlfetch._URLFetchResult
    logging.info('Info result: %s %s', result.status_code, result.content)
    if result.status_code != 200:
        raise Exception('Invalid response %s: %s' % (result.status_code, result.content))
    user_info = decode_userinfo_result(openid_config, server_settings.encryption_private_key, result.content)
    # Address is json encoded again for some reason
    address = user_info.get('address')
    if address:
        user_info['address'] = json.loads(address)
    return user_info
