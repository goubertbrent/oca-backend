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
from base64 import b64encode

from google.appengine.api import urlfetch

from mcfw.exceptions import HttpException
from mcfw.restapi import GenericRESTRequestHandler
from rogerthat.bizz.communities.communities import get_community
from rogerthat.dal.profile import get_service_profile
from rogerthat.dal.service import get_service_identity
from rogerthat.handlers.proxy import _exec_request
from rogerthat.restapi.service_panel import generate_api_key
from rogerthat.rpc import users
from rogerthat.utils.service import create_service_identity_user
from solution_server_settings import get_solution_server_settings
from solutions import translate
from solutions.common.models.participation import ParticipationCity


def _participation_request(secret, url, method, payload=None):
    # type: (str, str, str, dict) -> urlfetch._URLFetchResult
    url = '%s/api/plugins/psp/v1.0%s' % (get_solution_server_settings().participation_server_url, url)
    headers = {
        'Authentication': 'Basic %s' % b64encode(secret)
    }
    if method == 'GET':
        request = GenericRESTRequestHandler.getCurrentRequest()
        if request.params:
            url += '?%s' % urllib.urlencode(request.params)
    if payload:
        payload = json.dumps(payload)
    result = urlfetch.fetch(url, payload, method, headers, deadline=30)  # type: urlfetch._URLFetchResult
    str_code = str(result.status_code)
    if str_code.startswith('4') or str_code.startswith('5'):
        logging.error('Error for request %s %s: %s\n %s', url, method, result.status_code, result.content)
        raise Exception('Error during request to participation backend: %s' % result.status_code)
    return result


def _create_new_city(community_id, api_key, name, info):
    community = get_community(community_id)
    payload = {
        'id': community_id,
        'avatar_url': None,
        'name': name,
        'info': info,
        'app_id': community.default_app,
        'secret': None,
        'api_key': api_key
    }
    url = '/cities'
    result = _participation_request(get_solution_server_settings().participation_server_secret, url, 'POST', payload)
    return json.loads(result.content)['secret']


def get_participation_city(service_user):
    # type: (users.User) -> ParticipationCity
    service_profile = get_service_profile(service_user)
    city_key = ParticipationCity.create_key(service_profile.community_id)
    model = city_key.get()
    if not model:
        # First request, create the secret
        si_user = create_service_identity_user(service_user)
        name = get_service_identity(si_user).name
        api_key_name = 'Participation'
        settings = generate_api_key(api_key_name)
        new_api_key = [key for key in settings.apiKeys if key.name == api_key_name][0]
        info = translate(service_profile.defaultLanguage, 'oca.default_participation_info')
        secret = _create_new_city(service_profile.community_id, new_api_key.key, name, info)
        model = ParticipationCity(key=city_key,
                                  secret=secret)
        model.put()
    return model


def list_projects(service_user):
    # type: (users.User) -> dict
    model = get_participation_city(service_user)
    url = '/cities/%d/projects' % model.community_id
    return json.loads(_participation_request(model.secret, url, 'GET').content)


def get_project(service_user, project_id):
    # type: (users.User, int) -> dict
    model = get_participation_city(service_user)
    url = '/cities/%d/projects/%s' % (model.community_id, project_id)
    return json.loads(_participation_request(model.secret, url, 'GET').content)


def create_project(service_user, project):
    # type: (users.User, dict) -> dict
    model = get_participation_city(service_user)
    url = '/cities/%d/projects' % model.community_id
    return json.loads(_participation_request(model.secret, url, 'POST', project).content)


def update_project(service_user, project_id, project):
    # type: (users.User, int, dict) -> dict
    model = get_participation_city(service_user)
    url = '/cities/%d/projects/%s' % (model.community_id, project_id)
    return json.loads(_participation_request(model.secret, url, 'PUT', project).content)


def get_project_statistics(service_user, project_id):
    # type: (users.User, int) -> dict
    model = get_participation_city(service_user)
    url = '/cities/%d/projects/%s/statistics' % (model.community_id, project_id)
    return json.loads(_participation_request(model.secret, url, 'GET').content)


def get_settings(service_user):
    # type: (users.User) -> dict
    model = get_participation_city(service_user)
    url = '/cities/%d' % model.community_id
    return json.loads(_participation_request(model.secret, url, 'GET').content)


def update_settings(service_user, data):
    # type: (users.User, dict) -> dict
    model = get_participation_city(service_user)
    url = '/cities/%d' % model.community_id
    return json.loads(_participation_request(model.secret, url, 'PUT', data).content)


def register_app(app_id, ios_developer_account_id):
    # type: (unicode, long) -> None
    response = _exec_request('/api/developer-accounts/%s' % ios_developer_account_id, urlfetch.POST, {}, None, True)
    if response.status_code != 200:
        raise HttpException.from_urlfetchresult(response)
    dev_acc = json.loads(response.content)
    url = '/register-app'
    data = {
        'app_id': app_id,
        'ios_dev_team': dev_acc['ios_dev_team'],
    }
    secret = get_solution_server_settings().participation_server_secret
    _participation_request(secret, url, 'POST', data)
