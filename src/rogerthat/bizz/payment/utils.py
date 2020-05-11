# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
# NOTICE: THIS FILE HAS BEEN MODIFIED BY GREEN VALLEY BELGIUM NV IN ACCORDANCE WITH THE APACHE LICENSE VERSION 2.0
# Copyright 2018 GIG Technology NV
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
# @@license_version:1.6@@

import httplib
import json
import logging

from google.appengine.api import urlfetch

from mcfw.rpc import parse_complex_value
from rogerthat.bizz.payment.to import OpenIbanResultTO
from rogerthat.rpc.service import BusinessException


def get_provider_namespace(provider_id):
    return u'payment.providers.%s' % provider_id


def get_bank_details(iban):
    """
    Args:
        iban (unicode)
    Returns:
        OpenIbanResultTO
    """
    response = urlfetch.fetch('https://openiban.com/validate/%s?getBIC=true' % iban)
    if response.status_code != httplib.OK:
        raise BusinessException('Could not fetch bank details.\'Status: %s\'Content: %s', response.status_code,
                                response.content)
    json_result = json.loads(response.content)
    logging.debug('Bank details for iban %s: %s', iban, json_result)
    return parse_complex_value(OpenIbanResultTO, json_result, False)
