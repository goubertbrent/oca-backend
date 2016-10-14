# -*- coding: utf-8 -*-
# Copyright 2016 Mobicage NV
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
# @@license_version:1.1@@

import json
import logging
import time
from types import NoneType
import urllib

from google.appengine.api import urlfetch
from mcfw.rpc import returns, arguments
from rogerthat.rpc import users
from rogerthat.utils.transactions import run_in_transaction
from solutions.common.dal.cityapp import get_cityapp_profile
from solutions.common.models.cityapp import CityAppProfile


@returns(NoneType)
@arguments(service_user=users.User, uitdatabank_key=unicode, uitdatabank_region=unicode, gather_events=bool)
def save_cityapp_settings(service_user, uitdatabank_key, uitdatabank_region, gather_events):
    def trans():
        settings = get_cityapp_profile(service_user)
        settings.uitdatabank_key = uitdatabank_key
        settings.uitdatabank_region = uitdatabank_region
        settings.gather_events_enabled = gather_events
        settings.put()
    run_in_transaction(trans, False)

@returns(tuple)
@arguments(city_app_profile=CityAppProfile, page=(int, long), pagelength=(int, long), changed_since=(int, long, NoneType))
def get_uitdatabank_events(city_app_profile, page, pagelength, changed_since=None):
    url = "http://build.uitdatabank.be/api/events/search?"
    values = {'key' : city_app_profile.uitdatabank_key,
              'format' : "json",
              'regio' : city_app_profile.uitdatabank_region,
              'changedsince' : time.strftime('%Y-%m-%dT%H.%M', time.gmtime(changed_since)) if changed_since else "",
              'page' : page,
              'pagelength' : pagelength }
    data = urllib.urlencode(values)
    logging.debug(url + data);
    result = urlfetch.fetch(url + data)
    r = json.loads(result.content)

    if not r:
        if changed_since or page != 1:
            return True, []
        return False, "0 upcoming events. Make sure your region is correct."

    if "error" in r[0]:
        return False, r[0]["error"]

    return True, r


def get_uitdatabank_events_detail(uitdatabank_key, cbd_id):
    url = "http://build.uitdatabank.be/api/event/%s?" % cbd_id
    values = {'key' : uitdatabank_key,
              'format' : "json" }
    data = urllib.urlencode(values)
    result = urlfetch.fetch(url + data)
    r = json.loads(result.content)

    if not isinstance(r, list):
        event = r.get("event")
        if event is not None:
            return True, event
    elif "error" in r[0]:
        return False, r[0]["error"]
    return False, "Unknown error occurred"
