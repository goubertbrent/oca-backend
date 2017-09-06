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

import base64
import json
import logging

from google.appengine.api import urlfetch
from mcfw.rpc import arguments, returns
from rogerthat.consts import DEBUG
from solution_server_settings import get_solution_server_settings


SEND_URL = "https://api.createsend.com/api/v3.1/transactional/smartemail/%s/send"


@returns(bool)
@arguments(email_id=unicode, to=[unicode], add_recipients_to_list=bool)
def send_smart_email(email_id, to, add_recipients_to_list=True):
    """Send a smart email"""
    if DEBUG:
        logging.debug('Not sending out smart email %s to %s because DEBUG=True', email_id, to)
        return

    solution_server_settings = get_solution_server_settings()
    credentials = base64.b64encode('%s:' % solution_server_settings.createsend_api_key)

    data = json.dumps({
        'To': to,
        "AddRecipientsToList": add_recipients_to_list
    })

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Basic %s' % credentials
    }

    try:
        response = urlfetch.fetch(SEND_URL % email_id, method=urlfetch.POST,
                                  payload=data, headers=headers)
        if response.status_code >= 400:
            raise Exception('%s: %s' % (response.status_code, response.content))
        result = json.loads(response.content)
        if result and isinstance(result, list):
            result = result[0]
            if 'Status' in result and result['Status'] == "Accepted":
                return True
        return False
    except:
        logging.error('Cannot send smart email to %s', to, exc_info=True, _suppress=False)
        return False
