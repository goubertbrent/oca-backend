# -*- coding: utf-8 -*-
# Copyright 2018 Mobicage NV
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
# @@license_version:1.3@@

import json
import logging
import urllib

from google.appengine.api import urlfetch
from google.appengine.ext import deferred

from mcfw.properties import azzert
from shop.models import Customer
from solution_server_settings import get_solution_server_settings
from solutions.common.bizz.joyn.merchants import find_merchant
from solutions.common.models.joyn import JoynMerchantMatch, JoynMerchantMatches

JOYN_TOKEN_ENDPOINT = "https://api.joyn.be/oauth/token"
JOYN_API_ENDPOINT = "https://api-v2.joyn.be"


def get_access_token():
    sln_server_settings = get_solution_server_settings()
    payload = dict(grant_type="client_credentials",
                   client_id=sln_server_settings.joyn_client_id,
                   client_secret=sln_server_settings.joyn_client_secret)

    logging.info("Sending request to %s:\n%s" % (JOYN_TOKEN_ENDPOINT, payload))
    response = urlfetch.fetch(JOYN_TOKEN_ENDPOINT, urllib.urlencode(payload), urlfetch.POST)

    azzert(response.status_code == 200,
           "Got response status code %s and response content: %s" % (response.status_code, response.content))
    token_json = json.loads(response.content)
    return token_json["access_token"]


def get_businesses(app_id, zipcode, page):
    access_token = get_access_token()
    headers = {"Authorization": "Bearer " + access_token,
               "Accept": "application/json"}

    params = urllib.urlencode(dict(zipcode=zipcode,
                                   page=page))
    url = u"%s/api/v2/businesses?%s" % (JOYN_API_ENDPOINT, params)
    logging.info("Sending request to %s" % (url))
    response = urlfetch.fetch(url, headers=headers, deadline=60)
    azzert(response.status_code == 200,
           "Got response status code %s and response content: %s" % (response.status_code, response.content))
    logging.info("Got response: %s" % response.content)
    businesses_json = json.loads(response.content)
    for business in businesses_json['content']:
        deferred.defer(find_match, app_id, zipcode, business)
    return businesses_json['totalPages']


def find_match(app_id, zipcode, business):
    current_match = JoynMerchantMatch.create_key(business['id']).get()
    if current_match:
        logging.debug('joyn merchant %s already matched with %s', business['id'], current_match.service)
        return

    matches = {}
    for k in ["email", "phone", "website", "address", "facebookPage", "name"]:
        v = business.get(k)
        if not v:
            continue
        results = find_merchant(v)
        if not results:
            continue
        matches[k] = [{'merchant': result.fields[0].value,
                       'customer_id': result.fields[1].value,
                       'customer_name': result.fields[2].value} for result in results]

    if matches:
        logging.debug('joyn merchant %s has matches:\n%s', business['id'], matches)
        new_match_key = JoynMerchantMatches.create_key(business['id'])

        JoynMerchantMatches(
            key=new_match_key,
            app_id=app_id,
            zipcode=zipcode,
            joyn_data=business,
            matches=matches
        ).put()


def find_matches(app_id, zipcode):
    total_pages = get_businesses(app_id, zipcode, 0)
    for page in xrange(1, total_pages):
        deferred.defer(get_businesses, app_id, zipcode, page)
