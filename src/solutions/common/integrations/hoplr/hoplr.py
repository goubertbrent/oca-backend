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
from types import NoneType

from requests import sessions, Response
from typing import List

from mcfw.utils import Enum
from rogerthat.consts import DEBUG
from rogerthat.rpc import users
from rogerthat.to import convert_to_unicode, TO
from rogerthat.to.service import SendApiCallCallbackResultTO, UserDetailsTO
from rogerthat.utils.location import geo_code, GeoCodeZeroResultsException
from solution_server_settings import get_solution_server_settings, SolutionServerSettings
from solutions import translate
from solutions.common.dal import get_solution_settings
from solutions.common.integrations.hoplr.models import HoplrUser


class HoplrApiMethod(Enum):
    LOOKUP_NEIGHBOURHOOD = 'integrations.hoplr.lookup_neighbourhood'
    GET_USER_INFORMATION = 'integrations.hoplr.get_user_information'
    REGISTER = 'integrations.hoplr.register'
    LOGIN = 'integrations.hoplr.login'
    LOGOUT = 'integrations.hoplr.logout'
    GET_FEED = 'integrations.hoplr.get_feed'


class HoplrApiException(Exception):
    def __init__(self, response):
        # type: (Response) -> HoplrApiException
        self.response = response
        super(HoplrApiException, self).__init__('%s Client error for url: %s' % (response.status_code, response.url))


class UnknownMethodException(Exception):
    def __init__(self, method):
        super(UnknownMethodException, self).__init__('Unknown hoplr method: ' + method)


class TranslatedException(Exception):
    def __init__(self, msg):
        super(TranslatedException, self).__init__(msg)


def hoplr_api_call(settings, url, method, user=None, params=None, data=None, json=None):
    # type: (SolutionServerSettings, str, str, HoplrUser, dict, dict, dict) -> dict
    method = method.upper()
    url = settings.holpr_api_url + url
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'IntegrationClientId': settings.hoplr_client_id
    }
    if user:
        if user.is_token_expired:
            logging.debug('Refreshing expired token: %s', user.token)
            new_token = refresh_access_token(settings, user.get_refresh_token())
            user.set_token(new_token)
            user.put()
        headers['Authorization'] = 'Bearer %s' % user.get_access_token()
    with sessions.Session() as session:
        response = session.request(method, url, headers=headers, params=params, data=data, json=json, timeout=(30, 30))
    log_line = '%s %s\nHeaders:%s\nPayload: %s' % (method, response.url, headers, data or json)
    if DEBUG:
        logging.debug(log_line)
        logging.debug('%s %s', response.status_code, response.content)
    if response.status_code not in (200, 204):
        if not DEBUG:
            logging.debug('Request: %s', log_line)
            logging.debug('Response: %s %s', response.status_code, response.content)
        raise HoplrApiException(response)
    return response.json()


def lookup_neighbourhood(settings, service_user, app_user, params):
    # type: (SolutionServerSettings, users.User, users.User, dict) -> dict
    address = '%s %s, %s' % (params['streetName'], params['streetNumber'], params['cityName'])
    sln_settings = get_solution_settings(service_user)
    try:
        result = geo_code(address, extra_params={'language': sln_settings.main_language})
    except GeoCodeZeroResultsException:
        msg = translate(sln_settings.main_language, 'could_not_resolve_job_address')
        raise TranslatedException(msg)
    lat = result['geometry']['location']['lat']
    lon = result['geometry']['location']['lng']
    payload = {
        'cityName': params['cityName'],
        'latitude': lat,
        'longitude': lon,
        'code': params.get('code'),
    }
    neighbourhood_result = hoplr_api_call(settings, '/service/integrations/osa/neighbourhood/find', 'get',
                                          params=payload)
    return {
        'location': {
            'lat': lat,
            'lon': lon,
            'fullAddress': result['formatted_address'],
        },
        'result': neighbourhood_result
    }


def register_hoplr_user(settings, service_user, app_user, params):
    # type: (SolutionServerSettings, users.User, users.User, dict) -> dict
    info = params['info']
    result = hoplr_api_call(settings, '/service/integrations/osa/user/create', 'post', json=info)
    if not result.get('success', False):
        if result.get('message') == 'user_already_exists':
            msg = translate(get_solution_settings(service_user).main_language, 'hoplr_user_already_exists_pls_login')
            raise TranslatedException(msg)
        raise Exception('Could not register on Hoplr for some reason: %s' % result)
    token = get_token(settings, info['Username'], info['Password'])
    hoplr_user = HoplrUser(key=HoplrUser.create_key(app_user))
    hoplr_user.set_token(token)
    hoplr_user.put()
    return _return_user_information(result)


def get_token(settings, username, password):
    # type: (SolutionServerSettings, str, str) -> dict
    payload = {
        'grant_type': 'password',
        'username': username,
        'password': password,
    }
    return hoplr_api_call(settings, '/service/token', 'post', data=payload)


def refresh_access_token(settings, refresh_token):
    # type: (SolutionServerSettings, str) -> dict
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
    }
    return hoplr_api_call(settings, '/service/token', 'post', data=data)


def get_user_information(settings, hoplr_user):
    # type: (SolutionServerSettings, HoplrUser) -> dict
    return hoplr_api_call(settings, '/service/integrations/osa/user/%d' % hoplr_user.user_id, 'get', hoplr_user)


def login_hoplr_user(settings, service_user, app_user, params):
    # type: (SolutionServerSettings, users.User, users.User, dict) -> dict
    key = HoplrUser.create_key(app_user)
    hoplr_user = key.get() or HoplrUser(key=key)
    if hoplr_user.is_token_expired:
        try:
            token = get_token(settings, params['username'], params['password'])
            hoplr_user.set_token(token)
            hoplr_user.put()
        except HoplrApiException as e:
            if e.response.status_code == 400:
                response_data = e.response.json()
                if response_data.get('error_description') == 'username_or_password_incorrect':
                    lang = get_solution_settings(service_user).main_language
                    msg = translate(lang, 'hoplr_incorrect_email_or_password')
                    raise TranslatedException(msg)
                elif response_data.get('error_description') == 'client_cannot_access_user':
                    logging.error('Unsupported neighbourhood for user: %s', params['username'])
                    lang = get_solution_settings(service_user).main_language
                    msg = translate(lang, 'hoplr_neighbourhood_not_supported')
                    raise TranslatedException(msg)
            raise e
    info = get_user_information(settings, hoplr_user)
    return _return_user_information(info)


def logout_hoplr_user(settings, service_user, app_user, params):
    # type: (SolutionServerSettings, users.User, users.User, dict) -> NoneType
    HoplrUser.create_key(app_user).delete()
    return None


def app_get_user_information(settings, service_user, app_user, params):
    # type: (SolutionServerSettings, users.User, users.User, dict) -> dict
    hoplr_user = HoplrUser.create_key(app_user).get()
    if hoplr_user:
        info = get_user_information(settings, hoplr_user)
    else:
        info = None
    return _return_user_information(info)


def _return_user_information(user_info):
    # type: (dict) -> dict
    result = {
        'registered': False,
        'info': None,
    }
    if user_info:
        result['registered'] = True
        result['info'] = user_info
    return result


def get_feed(settings, service_user, app_user, params):
    # type: (SolutionServerSettings, users.User, users.User, dict) -> dict
    hoplr_user = HoplrUser.create_key(app_user).get()  # type: HoplrUser
    if not hoplr_user:
        raise Exception('User not registered as hoplr user: %s' % app_user)
    else:
        page = params.get('page', 0)
        payload = {
            'p': page
        }
        url = '/service/integrations/osa/neighbourhood/feed/%d' % hoplr_user.neighbourhood_id
        try:
            results = hoplr_api_call(settings, url, 'get', hoplr_user, params=payload)
            return {
                'results': results,
                'page': page,
                'baseUrl': settings.hoplr_base_url,
                'mediaBaseUrl': settings.hoplr_media_base_url,
                'more': len(results) > 0,
            }
        except HoplrApiException as e:
            if e.response.status_code == 403:
                response_data = e.response.json()
                if response_data.get('message') == 'forbidden':
                    msg = translate(get_solution_settings(service_user).main_language, 'hoplr_not_verified_yet')
                    raise TranslatedException(msg)
            raise e


method_mapping = {
    HoplrApiMethod.LOOKUP_NEIGHBOURHOOD: lookup_neighbourhood,
    HoplrApiMethod.REGISTER: register_hoplr_user,
    HoplrApiMethod.LOGIN: login_hoplr_user,
    HoplrApiMethod.LOGOUT: logout_hoplr_user,
    HoplrApiMethod.GET_USER_INFORMATION: app_get_user_information,
    HoplrApiMethod.GET_FEED: get_feed,
}


def _get_error(msg, can_retry):
    # type: (str, bool) -> unicode
    return json.dumps({'message': msg, 'can_retry': can_retry}).decode('utf-8')


def handle_method(service_user, email, method, params, tag, service_identity, user_details):
    # type: (users.User, str, str, str, str, str, List[UserDetailsTO]) -> SendApiCallCallbackResultTO
    response = SendApiCallCallbackResultTO()
    try:
        json_data = json.loads(params) if params else {}
        user = user_details[0]
        app_user = user.toAppUser()
        settings = get_solution_server_settings()
        func = method_mapping.get(method)
        if not func:
            raise UnknownMethodException(method)
        result = func(settings, service_user, app_user, json_data)
        response.result = convert_to_unicode(json.dumps(result.to_dict() if isinstance(result, TO) else result))
    except TranslatedException as e:
        logging.debug('User error while handling hoplr callback: %s', e.message)
        response.error = _get_error(e.message, False)
    except Exception:
        logging.error('Error while handling hoplr call %s' % method, exc_info=True)
        sln_settings = get_solution_settings(service_user)
        msg = translate(sln_settings.main_language, 'error-occured-unknown')
        response.error = _get_error(msg, True)
    return response
