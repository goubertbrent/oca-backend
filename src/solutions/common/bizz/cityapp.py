# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
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
# @@license_version:1.5@@

from datetime import datetime
from hashlib import sha1
from hmac import new as hmac
import json
import logging
from random import getrandbits
import time
from types import NoneType
from urllib import quote as urlquote
import urllib

from google.appengine.api import urlfetch

from mcfw.cache import cached
from mcfw.rpc import returns, arguments
from rogerthat.consts import DEBUG
from rogerthat.dal.app import get_apps_by_type
from rogerthat.models import App
from rogerthat.rpc import users
from rogerthat.utils.transactions import run_in_transaction
from solutions.common.dal.cityapp import get_cityapp_profile, \
    get_uitdatabank_settings
from solutions.common.models.cityapp import UitdatabankSettings


@returns(NoneType)
@arguments(service_user=users.User, gather_events=bool)
def save_cityapp_settings(service_user, gather_events):
    def trans():
        cap = get_cityapp_profile(service_user)
        cap.gather_events_enabled = gather_events
        cap.put()
    run_in_transaction(trans, False)


@returns(dict)
@arguments(country=unicode, live=bool)
def get_country_apps(country, live=True):
    """
    Args:
        country (unicode): country code e.g. be
        live (bool): has a live published build

    Returns:
        apps (dict): a dict with app name (city) as key and app_id as value
    """
    apps = get_apps_by_type(App.APP_TYPE_CITY_APP)

    # TODO: should add 'country' property to an app and filter on that. None if app type != city app

    def should_include(app):
        # check if the ios_app_id is set (has a live build)
        if not DEBUG and live and app.ios_app_id in (None, '-1') or app.disabled:
            return False
        return not app.demo and app.app_id.lower().startswith('%s-' % country.lower())

    return {
        app.name: app.app_id for app in apps if should_include(app)
    }


@cached(1, 3600)
@returns(int)
@arguments(country=unicode)
def get_apps_in_country_count(country):
    return len(get_country_apps(country, True))


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
    if settings.version == UitdatabankSettings.VERSION_1:
        return _get_uitdatabank_events_v1(settings, page, pagelength, changed_since)
    elif settings.version == UitdatabankSettings.VERSION_2:
        return _get_uitdatabank_events_v2(settings, page, pagelength)
    elif settings.version == UitdatabankSettings.VERSION_3:
        return _get_uitdatabank_events_v3(settings, page, pagelength, changed_since)

    return False, "Incorrect API version"


@returns(tuple)
@arguments(settings=UitdatabankSettings, page=(int, long), pagelength=(int, long), changed_since=(int, long, NoneType))
def _get_uitdatabank_events_v1(settings, page, pagelength, changed_since=None):
    key = settings.params.get('key')
    region = settings.params.get('region')

    if not key or not region:
        return False, "Not all fields are provided"

    url = "http://build.uitdatabank.be/api/events/search?"
    values = {'key': key,
              'format': "json",
              'regio': region,
              'changedsince': time.strftime('%Y-%m-%dT%H.%M', time.gmtime(changed_since)) if changed_since else "",
              'page': page,
              'pagelength': pagelength}
    data = urllib.urlencode(values)
    logging.debug(url + data)
    try:
        result = urlfetch.fetch(url + data, deadline=30)
    except urlfetch.DownloadError as e:
        logging.debug('Caught %s. Retrying....', e.__class__.__name__)
        result = urlfetch.fetch(url + data, deadline=30)
    if result.status_code != 200:
        logging.info("_get_uitdatabank_events_v1 failed with status_code %s and content:\n%s" % (result.status_code, result.content))
        return False, "Make sure your credentials are correct."
    r = json.loads(result.content)

    if not r:
        if changed_since or page != 1:
            return True, []
        return False, "0 upcoming events. Make sure your region is correct."

    if "error" in r[0]:
        return False, r[0]["error"]

    return True, r


def do_signed_uitdatabank_v2_request(url, key, secret, url_params=None, deadline=30, log_url=False):
    def encode(text):
        return urlquote(str(text), "~")

    sign_params = {
        "oauth_consumer_key": key,
        "oauth_timestamp": str(int(time.time())),
        "oauth_nonce": str(getrandbits(64)),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_version": "1.0",
    }
    if url_params:
        sign_params.update(url_params)
    for k, v in sign_params.items():
        if isinstance(v, unicode):
            sign_params[k] = v.encode('utf8')

    params_str = "&".join(["%s=%s" % (encode(k), encode(sign_params[k]))
                           for k in sorted(sign_params)])

    base_string = "&".join(["GET", encode(url), encode(params_str)])

    signature = hmac("%s&" % secret, base_string, sha1)
    digest_base64 = signature.digest().encode("base64").strip()
    sign_params["oauth_signature"] = encode(digest_base64)
    headers = {'Accept': "application/json"}
    headers['Authorization'] = 'OAuth oauth_consumer_key="%s",oauth_signature_method="%s",oauth_timestamp="%s",oauth_nonce="%s",oauth_version="1.0",oauth_signature="%s"' % (
        encode(sign_params['oauth_consumer_key']),
        encode(sign_params['oauth_signature_method']),
        encode(sign_params['oauth_timestamp']),
        encode(sign_params['oauth_nonce']),
        sign_params["oauth_signature"])
    
    if url_params:
        data = urllib.urlencode(url_params)
        url = "%s?%s" % (url, data)
    if log_url:
        logging.debug(url)
    return urlfetch.fetch(url, headers=headers, deadline=deadline)


@returns(tuple)
@arguments(settings=UitdatabankSettings, page=(int, long), pagelength=(int, long))
def _get_uitdatabank_events_v2(settings, page, pagelength):
    key = settings.params.get('key')
    secret = settings.params.get('secret')
    regions = settings.params.get('regions') or []
    filters = settings.params.get('filters') or []

    if not key or not secret or not regions:
        return False, "Not all fields are provided"

    str_secret = secret.encode("utf8")
    str_key = key.encode("utf8")
    cities = [c.encode("utf8") for c in regions]

    url = "https://www.uitid.be/uitid/rest/searchv2/search"
    url_params = {"q": " OR ".join(["city:%s" % city for city in cities]),
                  "rows": pagelength,
                  "start": (page - 1) * pagelength,
                  "datetype": "next3months",
                  "group": "event"}
    for f in filters:
        url_params['q'] += ' AND NOT %s:%s' % (f['key'], f['value'])

    logging.info('Uit search params: %s', url_params)
    try:
        result = do_signed_uitdatabank_v2_request(url, str_key, str_secret, url_params=url_params, log_url=True)
    except urlfetch.DownloadError as e:
        logging.debug('Caught %s. Retrying....', e.__class__.__name__)
        result = do_signed_uitdatabank_v2_request(url, str_key, str_secret, url_params=url_params, log_url=True)

    if result.status_code != 200:
        logging.info("_get_uitdatabank_events_v2 failed with status_code %s and content:\n%s" % (result.status_code, result.content))
        return False, "Make sure your credentials are correct."

    r = json.loads(result.content)["rootObject"]

    if "error" in r[0]:
        return False, r[0]["error"]

    event_count = r[0]["Long"]
    if event_count == 0:
        if page != 1:
            return True, []
        return False, "0 upcoming events. Make sure your region is correct."
    return True, [e["event"] for e in r[1:]]


@returns(tuple)
@arguments(settings=UitdatabankSettings, page=(int, long), pagelength=(int, long), changed_since=(int, long, NoneType))
def _get_uitdatabank_events_v3(settings, page, pagelength, changed_since=None):
    key = settings.params.get('key')
    postal_codes = settings.params.get('postal_codes') or []

    if not key or not postal_codes:
        return False, "Not all fields are provided"

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
        logging.info("_get_uitdatabank_events_v3 failed with status_code %s and content:\n%s" % (result.status_code, result.content))
        return False, "Make sure your credentials are correct."
    r = json.loads(result.content)

    if r['totalItems'] == 0:
        if changed_since:
            return True, []
        return False, "0 upcoming events. Make sure your postal codes are correct."

    if r['totalItems'] > 10000:
        logging.error('Result has more then 10.000 items')

    return True, [member['@id'] for member in r['member']]
