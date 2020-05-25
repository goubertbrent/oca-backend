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
from datetime import datetime

from google.appengine.api import urlfetch
from google.appengine.api.apiproxy_stub_map import UserRPC
from google.appengine.ext import ndb, db
from typing import List, Optional

from mcfw.cache import cached
from mcfw.rpc import arguments, returns
from mcfw.utils import Enum
from rogerthat.bizz.opening_hours import get_opening_hours_info
from rogerthat.consts import DEBUG
from rogerthat.dal.profile import get_user_profile
from rogerthat.models import OpeningHours, ServiceIdentity
from rogerthat.models.settings import ServiceInfo
from rogerthat.rpc import users
from rogerthat.to import convert_to_unicode, TO
from rogerthat.to.service import SendApiCallCallbackResultTO, UserDetailsTO
from solution_server_settings import get_solution_server_settings, SolutionServerSettings
from solutions import translate, SOLUTION_COMMON
from solutions.common.dal import get_solution_settings
from solutions.common.integrations.cirklo.models import CirkloUserVouchers, VoucherSettings, VoucherProviderId, \
    CirkloCity
from solutions.common.integrations.cirklo.to import AppVoucher, AppVoucherList
from solutions.common.models import SolutionBrandingSettings


class CirkloApiMethod(Enum):
    GET_VOUCHERS = 'integrations.cirklo.getvouchers'
    ADD_VOUCHER = 'integrations.cirklo.addvoucher'
    DELETE_VOUCHER = 'integrations.cirklo.deletevoucher'
    GET_TRANSACTIONS = 'integrations.cirklo.gettransactions'
    GET_MERCHANTS = 'integrations.cirklo.getmerchants'


class UnknownMethodException(Exception):
    def __init__(self, method):
        super(UnknownMethodException, self).__init__('Unknown cirkle method: ' + method)


class TranslatedException(Exception):
    def __init__(self, msg):
        super(TranslatedException, self).__init__(msg)


def _cirklo_api_call(settings, url, method, payload=None):
    # type: (SolutionServerSettings, str, str, dict) -> UserRPC
    url_params = ('?' + urllib.urlencode(payload)) if payload and method == urlfetch.GET else ''
    url = settings.cirklo_server_url + url + url_params
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'x-api-key': settings.cirklo_api_key
    }
    if method in ('PUT', 'POST') and payload:
        payload = json.dumps(payload)
    else:
        payload = None
    if DEBUG:
        logging.debug('%s %s', method, url)
    rpc = urlfetch.create_rpc(30)
    return urlfetch.make_fetch_call(rpc, url, payload, method, headers, follow_redirects=False)


def add_voucher(service_user, app_user, qr_content):
    # type: (users.User, users.User, str) -> dict
    try:
        parsed = json.loads(qr_content)
        voucher_id = parsed.get('voucher')
    except ValueError:
        voucher_id = None
    voucher_details = None
    if voucher_id:
        rpc = _cirklo_api_call(get_solution_server_settings(), '/vouchers/' + voucher_id, 'GET')
        result = rpc.get_result()  # type: urlfetch._URLFetchResult
        if result.status_code == 200:
            voucher_details = json.loads(result.content)
            voucher_details['id'] = voucher_id
        elif result.status_code in (400, 404):
            logging.debug('%s\n%s', result.status_code, result.content)
            voucher_id = None
        else:
            logging.debug('%s\n%s', result.status_code, result.content)
            raise Exception('Unexpected result from cirklo api')
    if not voucher_id:
        sln_settings = get_solution_settings(service_user)
        msg = translate(sln_settings.main_language, SOLUTION_COMMON, 'not_a_valid_cirklo_qr_code')
        raise TranslatedException(msg)
    key = CirkloUserVouchers.create_key(app_user)
    vouchers = key.get() or CirkloUserVouchers(key=key)  # type: CirkloUserVouchers
    if voucher_id not in vouchers.voucher_ids:
        vouchers.voucher_ids.append(voucher_id)
        vouchers.put()
    voucher = AppVoucher.from_cirklo(voucher_id, voucher_details, datetime.utcnow())
    city = CirkloCity.create_key(voucher.cityId).get()  # type: CirkloCity
    branding_settings = db.get(SolutionBrandingSettings.create_key(users.User(city.service_user_email)))
    return {
        'voucher': voucher.to_dict(),
        'city': {
            'logo_url': branding_settings.avatar_url
        }
    }


def delete_voucher(app_user, voucher_id):
    vouchers = CirkloUserVouchers.create_key(app_user).get()  # type: CirkloUserVouchers
    if vouchers and voucher_id in vouchers.voucher_ids:
        vouchers.voucher_ids.remove(voucher_id)
        vouchers.put()


def get_user_vouchers_ids(app_user):
    vouchers = CirkloUserVouchers.create_key(app_user).get()  # type: CirkloUserVouchers
    return vouchers.voucher_ids if vouchers else []


@cached(0)
@returns(unicode)
@arguments(service_email=unicode)
def get_city_id_by_service_email(service_email):
    return CirkloCity.get_by_service_email(service_email).city_id


def get_vouchers(service_user, app_user):
    # type: (users.User, users.User) -> AppVoucherList
    ids = get_user_vouchers_ids(app_user)
    settings = get_solution_server_settings()
    rpcs = [(voucher_id, _cirklo_api_call(settings, '/vouchers/' + voucher_id, 'GET')) for voucher_id in ids]
    vouchers = []  # type: List[AppVoucher]
    current_date = datetime.utcnow()
    for voucher_id, rpc in rpcs:
        result = rpc.get_result()  # type: urlfetch._URLFetchResult
        logging.debug('%s: %s', result.status_code, result.content)
        if result.status_code == 200:
            vouchers.append(AppVoucher.from_cirklo(voucher_id, json.loads(result.content), current_date))
        else:
            logging.error('Invalid cirklo api response: %s', result.status_code)
    main_city_id = get_city_id_by_service_email(service_user.email())
    if not main_city_id:
        raise Exception('No cityId found for service %s' % service_user.email())
    city_keys = {CirkloCity.create_key(voucher.cityId) for voucher in vouchers}
    city_keys.add(CirkloCity.create_key(main_city_id))
    cities = ndb.get_multi(city_keys)  # type: List[CirkloCity]
    branding_keys = [SolutionBrandingSettings.create_key(users.User(city.service_user_email)) for city in cities]
    solution_brandings = db.get(branding_keys)  # type: List[SolutionBrandingSettings]
    voucher_list = AppVoucherList()
    voucher_list.results = vouchers
    voucher_list.main_city_id = main_city_id
    voucher_list.cities = {}
    for city_key, city, branding in zip(city_keys, cities, solution_brandings):
        city_id = city.city_id
        voucher_list.cities[city_id] = {'logo_url': branding.avatar_url}
    return voucher_list


def get_merchants_by_app(app_id, language, cursor, page_size):
    # type: (str, str, Optional[str], int) -> dict
    start_cursor = cursor and ndb.Cursor.from_websafe_string(cursor)
    settings_keys, new_cursor, more = VoucherSettings.list_by_provider_and_app(VoucherProviderId.CIRKLO, app_id) \
        .fetch_page(page_size, keys_only=True, start_cursor=start_cursor)
    service_users = [users.User(key.id()) for key in settings_keys]
    info_keys = [ServiceInfo.create_key(service_user, ServiceIdentity.DEFAULT) for service_user in service_users]
    hours_keys = [OpeningHours.create_key(service_user, ServiceIdentity.DEFAULT) for service_user in service_users]
    models = ndb.get_multi(info_keys + hours_keys)
    infos = models[0: len(info_keys)]
    hours = models[len(info_keys):]
    results = []
    for service_info, opening_hours in zip(infos, hours):  # type: ServiceInfo, Optional[OpeningHours]
        opening_hours_dict = None
        if opening_hours:
            now_open, title, subtitle, weekday_text = get_opening_hours_info(opening_hours, service_info.timezone,
                                                                             language)
            opening_hours_dict = {
                'open_now': now_open,
                'title': title,
                'subtitle': subtitle,
                'weekday_text': [t.to_dict() for t in weekday_text]
            }
        results.append({
            'id': service_info.service_user.email(),
            'name': service_info.name,
            'address': service_info.addresses[0].to_dict() if service_info.addresses else None,
            'email_addresses': [{'name': email.name, 'value': email.value} for email in service_info.email_addresses],
            'websites': [{'name': website.name, 'value': website.value} for website in service_info.websites],
            'phone_numbers': [{'name': phone.name, 'value': phone.value} for phone in service_info.phone_numbers],
            'opening_hours': opening_hours_dict,
        })
    return {
        'results': results,
        'cursor': new_cursor and new_cursor.to_websafe_string().decode('utf-8'),
        'has_more': more,
    }


def handle_method(service_user, email, method, params, tag, service_identity, user_details):
    # type: (users.User, str, str, str, str, str, List[UserDetailsTO]) -> SendApiCallCallbackResultTO
    response = SendApiCallCallbackResultTO()
    try:
        json_data = json.loads(params) if params else {}
        user = user_details[0]
        app_user = user.toAppUser()
        # TODO: properly implement with correct urls and data
        if method == CirkloApiMethod.GET_VOUCHERS:
            result = get_vouchers(service_user, app_user)
        elif method == CirkloApiMethod.ADD_VOUCHER:
            qr_content = json_data['qrContent']
            result = add_voucher(service_user, app_user, qr_content)
        elif method == CirkloApiMethod.DELETE_VOUCHER:
            delete_voucher(app_user, json_data['id'])
            result = {}
        elif method == CirkloApiMethod.GET_TRANSACTIONS:
            # Not implemented yet
            result = {'results': []}
        elif method == CirkloApiMethod.GET_MERCHANTS:
            language = get_user_profile(app_user).language
            cursor = json_data.get('cursor')
            page_size = json_data.get('page_size', 20)
            result = get_merchants_by_app(user.app_id, language, cursor, page_size)
        else:
            raise UnknownMethodException(method)
        response.result = convert_to_unicode(json.dumps(result.to_dict() if isinstance(result, TO) else result))
    except TranslatedException as e:
        logging.debug('User error while handling cirklo callback: %s', e.message)
        response.error = e.message
    except Exception:
        logging.error('Error while handling cirklo call %s' % method, exc_info=True)
        sln_settings = get_solution_settings(service_user)
        response.error = translate(sln_settings.main_language, SOLUTION_COMMON, 'error-occured-unknown')
    return response
