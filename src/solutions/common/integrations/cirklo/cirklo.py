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
from rogerthat.bizz.communities.communities import get_community
from rogerthat.bizz.maps.services import search_services_by_tags, SearchTag
from rogerthat.bizz.opening_hours import get_opening_hours_info
from rogerthat.consts import DEBUG
from rogerthat.dal.profile import get_user_profile
from rogerthat.models import OpeningHours, ServiceIdentity
from rogerthat.models.settings import ServiceInfo
from rogerthat.rpc import users
from rogerthat.to import convert_to_unicode, TO
from rogerthat.to.service import SendApiCallCallbackResultTO, UserDetailsTO
from rogerthat.utils.service import get_service_user_from_service_identity_user
from solution_server_settings import get_solution_server_settings, SolutionServerSettings
from solutions import translate
from solutions.common.dal import get_solution_settings
from solutions.common.integrations.cirklo.models import CirkloUserVouchers, VoucherProviderId, \
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
        super(UnknownMethodException, self).__init__('Unknown cirklo method: ' + method)


class TranslatedException(Exception):
    def __init__(self, msg):
        super(TranslatedException, self).__init__(msg)


def _cirklo_api_call(settings, url, method, payload=None, staging=False):
    # type: (SolutionServerSettings, str, str, dict) -> UserRPC
    url_params = ('?' + urllib.urlencode(payload)) if payload and method == urlfetch.GET else ''
    url = settings.cirklo_server_url + url + url_params
    if staging and 'staging-app' not in url:
        url = url.replace('https://', 'https://staging-app-')
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'x-api-key': settings.cirklo_api_key_staging if staging else settings.cirklo_api_key
    }
    if method in (urlfetch.PUT, urlfetch.POST) and payload:
        payload = json.dumps(payload)
    else:
        payload = None
    if DEBUG:
        logging.debug('%s %s', method, url)
    rpc = urlfetch.create_rpc(30)
    return urlfetch.make_fetch_call(rpc, url, payload, method, headers, follow_redirects=False)


def list_whitelisted_merchants(city_id):
    staging = city_id.startswith('staging-')
    payload = {'cityId': city_id.replace('staging-', ''),
               'includeShops': True}
    rpc = _cirklo_api_call(get_solution_server_settings(), '/whitelists', urlfetch.GET, payload, staging)
    result = rpc.get_result()  # type: urlfetch._URLFetchResult
    if result.status_code == 200:
        return json.loads(result.content)
    else:
        logging.debug('%s\n%s', result.status_code, result.content)
        raise Exception('Unexpected result from cirklo api')


def check_merchant_whitelisted(city_id, email):
    staging = city_id.startswith('staging-')
    payload = {'cityId': city_id.replace('staging-', ''),
               'emails': email}
    rpc = _cirklo_api_call(get_solution_server_settings(), '/whitelists', urlfetch.GET, payload, staging)
    result = rpc.get_result()  # type: urlfetch._URLFetchResult
    if result.status_code == 200:
        merchant_list = json.loads(result.content)
        return len(merchant_list) > 0
    else:
        logging.debug('%s\n%s', result.status_code, result.content)
        return False


def whitelist_merchant(city_id, email):
    staging = city_id.startswith('staging-')
    payload = {'cityId': city_id.replace('staging-', ''),
               'whitelistEntries': [{'email': email}]}
    rpc = _cirklo_api_call(get_solution_server_settings(), '/whitelists', urlfetch.POST, payload, staging)
    result = rpc.get_result()  # type: urlfetch._URLFetchResult
    if result.status_code != 201:
        logging.debug('%s\n%s', result.status_code, result.content)
        raise Exception('Unexpected result from cirklo api')


def add_voucher(service_user, app_user, qr_content):
    # type: (users.User, users.User, str) -> dict
    try:
        parsed = json.loads(qr_content)
        voucher_id = parsed.get('voucher')
    except ValueError:
        voucher_id = None
    voucher_details = None
    if voucher_id:
        rpc = _cirklo_api_call(get_solution_server_settings(), '/vouchers/' + voucher_id, urlfetch.GET)
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
        msg = translate(sln_settings.main_language, 'not_a_valid_cirklo_qr_code')
        raise TranslatedException(msg)
    key = CirkloUserVouchers.create_key(app_user)
    vouchers = key.get() or CirkloUserVouchers(key=key)  # type: CirkloUserVouchers
    if voucher_id not in vouchers.voucher_ids:
        vouchers.voucher_ids.append(voucher_id)
        vouchers.put()
    else:
        sln_settings = get_solution_settings(service_user)
        msg = translate(sln_settings.main_language, 'duplicate_cirklo_voucher')
        raise TranslatedException(msg)
    voucher = AppVoucher.from_cirklo(voucher_id, voucher_details, datetime.utcnow())
    return {
        'voucher': voucher.to_dict(),
        'city': {
            'city_id': voucher.cityId,
            'logo_url': get_logo_url_for_city_id(voucher.cityId),
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


def get_logo_url_for_city_id(city_id):
    return get_logo_url_for_city_ids([city_id])[city_id]


def get_logo_url_for_city_ids(city_ids):
    city_keys = [CirkloCity.create_key(city_id) for city_id in city_ids]
    cities = ndb.get_multi(city_keys)  # type: List[CirkloCity]
    logos = {}
    for city_id, city in zip(city_ids, cities):
        if city:
            if city.logo_url:
                logos[city_id] = city.logo_url
            else:
                branding_settings = db.get(SolutionBrandingSettings.create_key(users.User(city.service_user_email)))
                logos[city_id] = branding_settings.avatar_url
        else:
            logos[city_id] = 'https://storage.googleapis.com/oca-files/misc/vouchers_default_city.png'
    return logos


@cached(0)
@returns(unicode)
@arguments(service_email=unicode)
def get_city_id_by_service_email(service_email):
    return CirkloCity.get_by_service_email(service_email).city_id


def get_vouchers(service_user, app_user):
    # type: (users.User, users.User) -> AppVoucherList
    ids = get_user_vouchers_ids(app_user)
    settings = get_solution_server_settings()
    rpcs = [(voucher_id, _cirklo_api_call(settings, '/vouchers/' + voucher_id, urlfetch.GET)) for voucher_id in ids]
    vouchers = []  # type: List[AppVoucher]
    current_date = datetime.utcnow()
    for voucher_id, rpc in rpcs:
        result = rpc.get_result()  # type: urlfetch._URLFetchResult
        logging.debug('%s: %s', result.status_code, result.content)
        if result.status_code == 200:
            vouchers.append(AppVoucher.from_cirklo(voucher_id, json.loads(result.content), current_date))
        else:
            logging.error('Invalid cirklo api response: %s', result.status_code)
    try:
        main_city_id = get_city_id_by_service_email(service_user.email())
    except:
        main_city_id = None
    if not main_city_id:
        logging.error('No cityId found for service %s' % service_user.email())
        sln_settings = get_solution_settings(service_user)
        msg = translate(sln_settings.main_language, 'cirklo_vouchers_not_live_yet')
        raise TranslatedException(msg)
    city_ids = {voucher.cityId for voucher in vouchers}
    city_ids.add(main_city_id)
    logos = get_logo_url_for_city_ids(list(city_ids))
    voucher_list = AppVoucherList()
    voucher_list.results = vouchers
    voucher_list.main_city_id = main_city_id
    voucher_list.cities = {}
    for city_id, logo_url in logos.iteritems():
        voucher_list.cities[city_id] = {'logo_url': logo_url}
    return voucher_list


def get_merchants_by_community(community_id, language, cursor, page_size):
    # type: (int, str, Optional[str], int) -> dict
    community = get_community(community_id)
    # Always filter by community id
    tags = [
        SearchTag.community(community_id),
        SearchTag.environment(community.demo),
        SearchTag.vouchers(VoucherProviderId.CIRKLO)
    ]
    service_identity_users, new_cursor = search_services_by_tags(tags, cursor, page_size)
    service_users = [get_service_user_from_service_identity_user(service_user)
                     for service_user in service_identity_users]
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
        'cursor': new_cursor,
        'more': new_cursor is not None,
    }


def handle_method(service_user, email, method, params, tag, service_identity, user_details):
    # type: (users.User, str, str, str, str, str, List[UserDetailsTO]) -> SendApiCallCallbackResultTO
    response = SendApiCallCallbackResultTO()
    try:
        json_data = json.loads(params) if params else {}
        user = user_details[0]
        app_user = user.toAppUser()
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
            user_profile = get_user_profile(app_user)
            result = get_merchants_by_community(user_profile.community_id, language, cursor, page_size)
        else:
            raise UnknownMethodException(method)
        response.result = convert_to_unicode(json.dumps(result.to_dict() if isinstance(result, TO) else result))
    except TranslatedException as e:
        logging.debug('User error while handling cirklo callback: %s', e.message)
        response.error = e.message
    except Exception:
        logging.error('Error while handling cirklo call %s' % method, exc_info=True)
        sln_settings = get_solution_settings(service_user)
        response.error = translate(sln_settings.main_language, 'error-occured-unknown')
    return response
