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
from types import NoneType

from google.appengine.api import urlfetch

from mcfw.rpc import returns, arguments
from rogerthat.rpc import users
from solutions.common.dal.cityapp import get_uitdatabank_settings
from solutions.common.models.cityapp import UitdatabankSettings


@returns(NoneType)
@arguments(service_user=users.User, version=unicode, params=dict)
def save_uitdatabank_settings(service_user, version, params):
    settings = get_uitdatabank_settings(service_user)
    settings.version = version
    settings.params = params
    settings.put()


@returns(tuple)
@arguments(settings=UitdatabankSettings, page=(int, long), pagelength=(int, long), changed_since=(int, long, NoneType))
def get_uitdatabank_events(settings, page, pagelength, changed_since=None):
    if settings.version == UitdatabankSettings.VERSION_3:
        return _get_uitdatabank_events_v3(settings, page, pagelength, changed_since)

    return False, 0, "Incorrect API version"


@returns(tuple)
@arguments(settings=UitdatabankSettings, page=(int, long), pagelength=(int, long), changed_since=(int, long, NoneType))
def _get_uitdatabank_events_v3(settings, page, pagelength, changed_since=None):
    key = settings.params.get('key')
    postal_codes = settings.params.get('postal_codes') or []

    if not key or not postal_codes:
        return False, 0, "Not all fields are provided"

    q_array = []
    for postal_code in postal_codes:
        q_array.append('address.nl.postalCode:%s' % postal_code)

    if settings.params.get('test'):
        url = "https://search-test.uitdatabank.be/events?"
    else:
        url = "https://search.uitdatabank.be/events?"
    values = {'apiKey': key,
              'start': (page - 1) * pagelength,
              'limit': pagelength,
              'calendarType': 'single,multiple,periodic',
              'q': ' OR '.join(q_array)}
    if changed_since:
        values['modifiedFrom'] = datetime.utcfromtimestamp(changed_since).isoformat() + '+00:00'
    data = urllib.urlencode(values)
    logging.debug(url + data)
    try:
        result = urlfetch.fetch(url + data, deadline=30)
    except urlfetch.DownloadError as e:
        logging.debug('Caught %s. Retrying....', e.__class__.__name__)
        result = urlfetch.fetch(url + data, deadline=30)
    if result.status_code != 200:
        logging.info("_get_uitdatabank_events_v3 failed with status_code %s and content:\n%s" %
                     (result.status_code, result.content))
        return False, 0, "Make sure your credentials are correct."
    r = json.loads(result.content)

    if r['totalItems'] == 0:
        if changed_since:
            return True, 0, []
        return False, 0, "0 upcoming events. Make sure your postal codes are correct."

    if r['totalItems'] > 10000:
        logging.error('Result has more then 10.000 items')

    return True, r['totalItems'], [member['@id'] for member in r['member']]
