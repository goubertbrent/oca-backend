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
import urllib

from google.appengine.api import urlfetch
from typing import List

from mcfw.utils import Enum
from rogerthat.consts import DEBUG
from rogerthat.rpc import users
from rogerthat.to import convert_to_unicode
from rogerthat.to.service import SendApiCallCallbackResultTO, UserDetailsTO
from solution_server_settings import get_solution_server_settings, SolutionServerSettings
from solutions import translate, SOLUTION_COMMON
from solutions.common.dal import get_solution_settings
from solutions.common.integrations.cirklo.models import CirkloUserVouchers


class CirkloApiMethod(Enum):
    GET_VOUCHERS = 'integrations.cirklo.getvouchers'
    ADD_VOUCHER = 'integrations.cirklo.addvoucher'
    DELETE_VOUCHER = 'integrations.cirklo.deletevoucher'


class UnknownMethodException(Exception):
    def __init__(self, method):
        super(UnknownMethodException, self).__init__('Unknown cirkle method: ' + method)


def _do_call(settings, url, method, payload):
    # type: (SolutionServerSettings, str, str, dict) -> urlfetch._URLFetchResult
    url_params = ('?' + urllib.urlencode(payload)) if payload and method == urlfetch.GET else ''
    url = settings.cirklo_server_url + url + url_params
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    if method in ('PUT', 'POST') and payload:
        payload = json.dumps(payload)
    else:
        payload = None
    if DEBUG:
        logging.debug(url)
    result = urlfetch.fetch(url, payload, method, headers, deadline=30, follow_redirects=False)
    if DEBUG:
        logging.debug(result.content)
    return result


def add_voucher(app_user, voucher_id):
    key = CirkloUserVouchers.create_key(app_user)
    vouchers = key.get() or CirkloUserVouchers(key=key)  # type: CirkloUserVouchers
    if voucher_id not in vouchers.voucher_ids:
        vouchers.voucher_ids.append(voucher_id)
        vouchers.put()


def delete_voucher(app_user, voucher_id):
    vouchers = CirkloUserVouchers.create_key(app_user).get()  # type: CirkloUserVouchers
    if vouchers and voucher_id in vouchers.voucher_ids:
        vouchers.voucher_ids.remove(voucher_id)
        vouchers.put()


def get_user_vouchers_ids(app_user):
    vouchers = CirkloUserVouchers.create_key(app_user).get()  # type: CirkloUserVouchers
    return vouchers.voucher_ids if vouchers else []


def handle_method(service_user, email, method, params, tag, service_identity, user_details):
    # type: (users.User, str, str, str, str, str, List[UserDetailsTO]) -> SendApiCallCallbackResultTO
    response = SendApiCallCallbackResultTO()
    try:
        settings = get_solution_server_settings()
        json_data = json.loads(params) if params else {}
        app_user = user_details[0].toAppUser()
        # TODO: properly implement with correct urls and data
        if method == CirkloApiMethod.GET_VOUCHERS:
            ids = get_user_vouchers_ids(app_user)
            data = {
                'ids': ids
            }
            result = _do_call(settings, '/vouchers', 'GET', data)
        elif method == CirkloApiMethod.ADD_VOUCHER:
            add_voucher(app_user, json_data['id'])
            # TODO: return voucher details as result
            result = {}
        elif method == CirkloApiMethod.DELETE_VOUCHER:
            delete_voucher(app_user, json_data['id'])
            result = {}
        else:
            raise UnknownMethodException(method)
        response.result = convert_to_unicode(json.dumps(result))
    except Exception:
        logging.error('Error while handling cirklo call %s' % method, exc_info=True)
        sln_settings = get_solution_settings(service_user)
        response.error = translate(sln_settings.main_language, SOLUTION_COMMON, 'error-occured-unknown')
    return response
