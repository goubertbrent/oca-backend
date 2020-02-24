# -*- coding: utf-8 -*-
# Copyright 2020 Green Valley NV
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
import itertools
import json
import logging
from datetime import datetime

from google.appengine.api import urlfetch
from google.appengine.ext import ndb
from typing import Dict, Tuple, List, Generator, Iterable

from rogerthat.bizz.job import run_job, MODE_BATCH
from rogerthat.consts import DEBUG
from rogerthat.models.elasticsearch import ElasticsearchSettings
from solutions.common.models.agenda import Event, EventCalendarType


def _request(path, method=urlfetch.GET, payload=None, allowed_status_codes=(200, 204)):
    # type: (str, int, Dict, Tuple[int]) -> Dict
    config = ElasticsearchSettings.create_key().get()  # type: ElasticsearchSettings
    headers = {
        'Accept': 'application/json',
        'Authorization': 'Basic %s' % base64.b64encode('%s:%s' % (config.auth_username, config.auth_password))
    }
    if payload:
        if isinstance(payload, basestring):
            headers['Content-Type'] = 'application/x-ndjson'
        else:
            headers['Content-Type'] = 'application/json'
    data = json.dumps(payload) if isinstance(payload, dict) else payload
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


def execute_bulk_request(config, operations):
    # type: (ElasticsearchSettings, Iterable[Dict]) -> List[Dict]
    path = '/%s/_bulk' % config.events_index
    # NDJSON
    payload = '\n'.join([json.dumps(op) for op in operations])
    payload += '\n'
    result = _request(path, urlfetch.POST, payload)
    if result['errors'] is True:
        logging.debug(result)
        # throw the first error found
        for item in result['items']:
            k = item.keys()[0]
            if 'error' in item[k]:
                reason = item[k]['error']['reason']
                raise Exception(reason)
    return result['items']


def create_events_index():
    request = {
        'mappings': {
            'properties': {
                'app_ids': {
                    'type': 'keyword',
                },
                'service': {
                    'type': 'keyword',
                },
                'title': {
                    'type': 'text'
                },
                'description': {
                    'type': 'text'
                },
                'time_frames': {
                    'type': 'date_range',
                },
                'place': {
                    'type': 'text'
                },
                'organizer': {
                    'type': 'text'
                }
            }
        }
    }
    path = '/%s' % ElasticsearchSettings.create_key().get().events_index
    return _request(path, urlfetch.PUT, request)


def delete_events_index():
    path = '/%s' % ElasticsearchSettings.create_key().get().events_index
    return _request(path, urlfetch.DELETE, allowed_status_codes=(200, 204, 404))


def _index_event(event):
    # type: (Event) -> Generator[Dict]
    if event.deleted:
        yield {'delete': {'_id': event.key.urlsafe()}}
    else:
        # TODO: in order to make it possible to order by start date, we should create a new document for
        # every occurrence of an event, which is not great.
        doc = {
            'app_ids': event.app_ids,
            'service': event.service_user.email(),
            'title': event.title,
            'description': event.description,
            'place': event.place,
            'organizer': event.organizer,
            'time_frames': [{'gte': start_date.isoformat() + 'Z', 'lte': end_date.isoformat() + 'Z'}
                            for start_date, end_date in event.get_occurrence_dates(datetime.now())],
        }
        yield {'index': {'_id': event.key.urlsafe()}}
        yield doc


@ndb.non_transactional()
def index_events(events):
    # type: (List[Event]) -> List[Dict]
    if events:
        operations = itertools.chain.from_iterable(_index_event(event) for event in events)
        return execute_bulk_request(ElasticsearchSettings.create_key().get(), operations)


def re_index_all_events():
    delete_events_index()
    create_events_index()
    run_job(_get_all_events, [], _index_events, [], mode=MODE_BATCH)


def re_index_periodic_events():
    # Some events have only 100 occurrences because they have no opening hours specified
    # These should be updated periodically so the old dates are removed and future dates are added to the index
    run_job(_get_periodic_events, [], _index_events, [], mode=MODE_BATCH)


def delete_events_from_index(keys):
    # type: (List[ndb.Key]) -> None
    if keys:
        operations = [{'delete': {'_id': key.urlsafe()}} for key in keys]
        execute_bulk_request(ElasticsearchSettings.create_key().get(), operations)


def search_events(start_date, end_date, app_id=None, service=None, search_string=None, cursor=None, amount=50):
    start_offset = long(cursor) if cursor else 0

    if (start_offset + amount) > 10000:
        amount = 10000 - start_offset
    if amount <= 0:
        return None, []
    qry = {
        'size': amount,
        'from': start_offset,
        'query': {
            'bool': {
                'filter': [
                    {
                        'range': {
                            'time_frames': {
                                'gte': start_date,
                                'lte': end_date,
                                'relation': 'intersects',
                            }
                        }
                    }
                ],
                'must': []
            }
        },
        # We don't care what's in the document as we'll have to fetch the datastore model anyway
        'stored_fields': [],
        'sort': [
            '_score'
        ]
    }
    if app_id:
        qry['query']['bool']['filter'].append({'term': {'app_ids': app_id}})
    if service:
        qry['query']['bool']['filter'].append({'term': {'service': service}})
    if search_string:
        qry['query']['bool']['must'].append({
            'multi_match': {
                'query': search_string,
                'fuzziness': '1',
                'fields': ['title^10', 'description', 'place', 'organizer']
            }
        })
    path = '/%s/_search' % ElasticsearchSettings.create_key().get().events_index
    result_data = _request(path, urlfetch.POST, qry)
    new_cursor = None
    next_offset = start_offset + len(result_data['hits']['hits'])
    if result_data['hits']['total']['relation'] in ('eq', 'gte'):
        if result_data['hits']['total']['value'] > next_offset and next_offset < 10000:
            new_cursor = u'%s' % next_offset
    keys = [ndb.Key(urlsafe=hit['_id']) for hit in result_data['hits']['hits']]
    events = [event for event in ndb.get_multi(keys) if event]
    return new_cursor, events


def _get_all_events():
    return Event.query()


def _get_periodic_events():
    return Event.list_by_calendar_type(EventCalendarType.PERIODIC)


def _index_events(events_or_keys):
    if events_or_keys:
        if isinstance(events_or_keys[0], Event):
            events = events_or_keys
        else:
            events = ndb.get_multi(events_or_keys)
        index_events(events)
