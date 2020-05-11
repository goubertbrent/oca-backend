# -*- coding: utf-8 -*-
# Copyright 2018 Mobicage NV
# NOTICE: THIS FILE HAS BEEN MODIFIED BY MOBICAGE NV IN ACCORDANCE WITH THE APACHE LICENSE VERSION 2.0
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
# @@license_version:1.5@@

import base64
import json
import logging

from google.appengine.api import urlfetch
from typing import Iterable, Dict, List, Tuple

from rogerthat.consts import DEBUG
from rogerthat.models.elasticsearch import ElasticsearchSettings


def get_elasticsearch_config():
    # type: () -> ElasticsearchSettings
    settings = ElasticsearchSettings.create_key().get()
    if not settings:
        raise Exception('elasticsearch settings not found')
    return settings


def delete_index(index):
    path = '/%s' % index
    return es_request(path, urlfetch.DELETE, allowed_status_codes=(200, 204, 404))


def create_index(index, request):
    path = '/%s' % index
    return es_request(path, urlfetch.PUT, request)


def delete_doc(index, uid):
    path = '/%s/_doc/%s' % (index, uid)
    return es_request(path, urlfetch.DELETE, allowed_status_codes=(200, 404))


def index_doc(index, uid, doc):
    path = '/%s/_doc/%s' % (index, uid)
    return es_request(path, urlfetch.PUT, doc, allowed_status_codes=(200, 201))


def delete_doc_operations(uid):
    yield {'delete': {'_id': uid}}


def index_doc_operations(uid, doc):
    yield {'index': {'_id': uid}}
    yield doc
    

def execute_bulk_request(index, operations):
    # type: (str, Iterable[Dict]) -> List[Dict]
    path = '/%s/_bulk' % index
    # NDJSON
    payload = '\n'.join([json.dumps(op) for op in operations])
    payload += '\n'
    result = es_request(path, urlfetch.POST, payload)
    if result['errors'] is True:
        logging.debug(result)
        # throw the first error found
        for item in result['items']:
            k = item.keys()[0]
            if 'error' in item[k]:
                reason = item[k]['error']['reason']
                raise Exception(reason)
    return result['items']


def es_request(path, method=urlfetch.GET, payload=None, allowed_status_codes=(200, 204)):
    # type: (str, int, Dict, Tuple[int, ...]) -> Dict
    config = get_elasticsearch_config()
    headers = {
        'Accept': 'application/json',
        'Authorization': 'Basic %s' % base64.b64encode('%s:%s' % (config.auth_username, config.auth_password))
    }
    if payload:
        if isinstance(payload, basestring):
            headers['Content-Type'] = 'application/x-ndjson'
        else:
            headers['Content-Type'] = 'application/json'
    data = json.dumps(payload, indent=2 if DEBUG else None) if isinstance(payload, dict) else payload
    url = config.base_url + path
    if DEBUG:
        if data:
            logging.debug('%s\n%s', url, data)
        else:
            logging.debug(url)
    result = urlfetch.fetch(url, data, method, headers, deadline=30)  # type: urlfetch._URLFetchResult
    if result.status_code not in allowed_status_codes:
        logging.debug(result.content)
        raise Exception('Invalid response from elasticsearch: %s' % result.status_code)
    if result.headers.get('Content-Type').startswith('application/json'):
        return json.loads(result.content)
    return result.content
