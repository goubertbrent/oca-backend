# -*- coding: utf-8 -*-
# Copyright 2017 Mobicage NV
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
# @@license_version:1.2@@

import json
import urllib
import logging

from google.appengine.api import urlfetch

from mcfw.rpc import arguments, returns
from solution_server_settings import get_solution_server_settings

VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"


@returns(bool)
@arguments(recaptcha_response_token=unicode)
def recaptcha_verify(recaptcha_response_token):
    """Verify the grecaptcha response token."""
    solution_server_settings = get_solution_server_settings()
    params = {
        'secret': solution_server_settings.recaptcha_secret_key,
        'response': recaptcha_response_token
    }

    try:
        url = VERIFY_URL + '?' + urllib.urlencode(params)
        response = urlfetch.fetch(url, method=urlfetch.POST)
        result = json.loads(response.content)
        return result['success']
    except:
        logging.error('cannot verify recaptcha response token', exc_info=True)
        return False
