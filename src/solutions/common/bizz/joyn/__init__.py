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
from google.appengine.api.taskqueue import taskqueue
from google.appengine.ext import db
from google.appengine.ext.deferred import deferred

from mcfw.cache import cached
from mcfw.properties import azzert
from mcfw.rpc import arguments, returns
from mcfw.utils import chunks
from rogerthat.bizz.job import run_job
from rogerthat.consts import HIGH_LOAD_WORKER_QUEUE
from rogerthat.utils.cloud_tasks import schedule_tasks, create_task
from shop.models import ShopApp, Customer
from solution_server_settings import get_solution_server_settings
from solutions.common.bizz import enable_or_disable_solution_module, SolutionModule
from solutions.common.bizz.joyn.merchants import find_merchant
from solutions.common.models.joyn import JoynMerchantMatches

JOYN_TOKEN_ENDPOINT = "https://api.joyn.be/oauth/token"
JOYN_API_ENDPOINT = "https://api-v2.joyn.be"


@cached(1, lifetime=3500)
@returns(unicode)
@arguments()
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
    # token_json['expires_in'] -> usually 3600 (one hour)
    return token_json["access_token"]


def get_businesses(app_id, zip_codes, page):
    # type: (str, list[str], int) -> int
    headers = {"Authorization": "Bearer " + get_access_token(),
               "Accept": "application/json"}

    params = urllib.urlencode([('zipcode', zipcode) for zipcode in zip_codes] + [('page', page)])
    url = u"%s/api/v2/businesses?%s" % (JOYN_API_ENDPOINT, params)
    logging.info('Sending request to %s', url)
    response = urlfetch.fetch(url, headers=headers, deadline=60)
    azzert(response.status_code == 200,
           "Got response status code %s and response content: %s" % (response.status_code, response.content))
    logging.info("Got response: %s" % response.content)
    businesses_json = json.loads(response.content)
    schedule_tasks([create_task(find_match, app_id, business) for business in businesses_json['content']])
    return businesses_json['totalPages']


def find_match(app_id, business):
    # type: (str, dict) -> None
    current_match = JoynMerchantMatches.create_key(business['id']).get()  # type: JoynMerchantMatches
    if current_match:
        if current_match.customer_id:
            logging.debug('joyn merchant %s already matched with %s', business['id'], current_match.customer_id)
        return

    matches = {}
    for key in ["email", "phone", "website", "address", "facebookPage", "name"]:
        value = business.get(key)
        if not value:
            continue
        # Some people don't understand urls
        if key == 'facebookPage' and value == 'https://www.facebook.com/profile.php':
            continue
        results = find_merchant(value)
        if not results:
            continue
        matches[key] = [{'merchant': result.fields[0].value,
                         'customer_id': result.fields[1].value,
                         'customer_name': result.fields[2].value} for result in results]

    if matches:
        logging.debug('joyn merchant %s has matches:\n%s', business['id'], matches)
        new_match_key = JoynMerchantMatches.create_key(business['id'])

        JoynMerchantMatches(
            key=new_match_key,
            app_id=app_id,
            zipcode=business['zipcode'],
            joyn_data=business,
            matches=matches
        ).put()


def find_matches(app_id, zip_codes):
    total_pages = get_businesses(app_id, zip_codes, 0)
    schedule_tasks([create_task(get_businesses, app_id, zip_codes, page) for page in xrange(1, total_pages)])


def find_all_joyn_matches():
    run_job(_get_shop_apps, [], find_matches_for_shopapp, [])


def find_matches_for_shopapp(shop_app_key):
    # type: (db.Key) -> None
    # Joyn is only for belgium
    app_id = shop_app_key.name()
    if app_id.startswith('be-'):
        shop_app = db.get(shop_app_key)  # type: ShopApp
        find_matches(app_id, shop_app.postal_codes)


def _get_shop_apps():
    return ShopApp.all(keys_only=True)




def _add_joyn_module(customer_id):
    customer = db.get(Customer.create_key(customer_id))
    if customer.service_email:
        enable_or_disable_solution_module(customer.service_user, SolutionModule.JOYN, True)
