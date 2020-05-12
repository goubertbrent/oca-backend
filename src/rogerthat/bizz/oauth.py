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

import httplib
import json
import logging
import urllib

from google.appengine.api import urlfetch

from add_1_monkey_patches import DEBUG
from mcfw.rpc import arguments, returns, parse_complex_value
from rogerthat.rpc.service import BusinessException
from rogerthat.to.oauth import OauthAccessTokenTO


def get_oauth_identity(identity_url, access_token, response_type, identity_url_parameters=None):
    if identity_url_parameters is None:
        identity_url_parameters = {}
    headers = {"Authorization": access_token,
               'Accept': "application/json"}

    response = urlfetch.fetch(identity_url % identity_url_parameters, method=urlfetch.GET, headers=headers, deadline=20)
    logging.debug(response.content)
    if response.status_code == httplib.OK:
        return parse_complex_value(response_type, json.loads(response.content), False)
    else:
        logging.error('%s responded with status code %s.\n%s', identity_url, response.status_code, response.content)
        raise BusinessException('Could not get oauth identity')


@returns(OauthAccessTokenTO)
@arguments(access_token_url=unicode, client_id=unicode, client_secret=unicode, code=unicode, redirect_url=unicode,
           state=unicode, grant_type=unicode)
def get_oauth_access_token(access_token_url, client_id, client_secret, code, redirect_url, state,
                           grant_type=None):
    params = urllib.urlencode({
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'redirect_uri': redirect_url,
        'state': state,
        'grant_type': grant_type if grant_type else ""
    })

    headers = {'Accept': "application/json"}
    response = urlfetch.fetch(access_token_url, payload=params, method=urlfetch.POST, headers=headers, deadline=20,
                              validate_certificate=not DEBUG)
    logging.debug(response.content)
    if response.status_code == httplib.OK:
        return parse_complex_value(OauthAccessTokenTO, json.loads(response.content), False)
    else:
        logging.error('%s responded with status code %s.\n%s\n%s', access_token_url, response.status_code, params, response.content)
        raise BusinessException('Could not get oauth access token')
