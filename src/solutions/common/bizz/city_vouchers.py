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

from mcfw.rpc import returns, arguments
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from rogerthat.to.friends import GetUserInfoResponseTO
from rogerthat.to.service import SendApiCallCallbackResultTO, UserDetailsTO
from rogerthat.utils.app import get_app_user_tuple
from solutions import translate
from solutions.common.dal import get_solution_settings
from solutions.common.models.loyalty import CustomLoyaltyCard


def _create_resolve_result(result_type, url, email, app_id):
    return {
        'type': result_type,
        'url': url,
        'content': url,
        'userDetails': {
            'appId': app_id,
            'email': email,
            'name': email
        }
    }


@returns(dict)
@arguments(service_user=users.User, service_identity=unicode, url=unicode)
def _resolve_voucher(service_user, service_identity, url):
    """Lookup the provided URL. It will be treated as a custom loyalty card."""

    # 1/ Check if a custom loyalty card already exists for this URL
    custom_loyalty_card = CustomLoyaltyCard.get_by_url(url)
    if custom_loyalty_card and custom_loyalty_card.app_user:
        human_user, app_id = get_app_user_tuple(custom_loyalty_card.app_user)
        return _create_resolve_result(CustomLoyaltyCard.TYPE, url, human_user.email(), app_id)
    logging.debug('Unknown QR code scanned: %s. Loyalty device will create custom paper loyalty card.', url)

    user_info = GetUserInfoResponseTO()
    user_info.app_id = user_info.email = user_info.name = user_info.qualifiedIdentifier = u'dummy'
    return _create_resolve_result(u'unknown', url, u'dummy', u'dummy')



@returns(SendApiCallCallbackResultTO)
@arguments(service_user=users.User, email=unicode, method=unicode, params=unicode, tag=unicode,
           service_identity=unicode,
           user_details=[UserDetailsTO])
def solution_voucher_resolve(service_user, email, method, params, tag, service_identity, user_details):
    logging.debug("Received voucher resolve call with params: %s", params)
    r = SendApiCallCallbackResultTO()
    r.result = None
    r.error = None
    try:
        jsondata = json.loads(params)
        r_dict = _resolve_voucher(service_user, service_identity, jsondata['url'])
        result = json.dumps(r_dict)
        r.result = result if isinstance(result, unicode) else result.decode("utf8")
    except BusinessException as be:
        r.error = be.message
    except:
        logging.error("solutions.voucher.resolve exception occurred", exc_info=True)
        sln_settings = get_solution_settings(service_user)
        r.error = translate(sln_settings.main_language, 'error-occured-unknown')
    return r
