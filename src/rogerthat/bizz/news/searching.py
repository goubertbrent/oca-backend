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

from datetime import datetime

from google.appengine.api import urlfetch
from google.appengine.ext import ndb

from mcfw.rpc import arguments
from rogerthat.bizz.elasticsearch import delete_index, create_index, \
    get_elasticsearch_config, delete_doc, index_doc, es_request
from rogerthat.bizz.job import run_job
from rogerthat.consts import NEWS_MATCHING_QUEUE
from rogerthat.dal.profile import get_service_visible_non_transactional
from rogerthat.dal.service import get_service_identity
from rogerthat.models.elasticsearch import ElasticsearchSettings
from rogerthat.models.news import NewsItem


def re_index_all(queue=NEWS_MATCHING_QUEUE):
    config = get_elasticsearch_config()
    delete_news_index(config)
    create_news_index(config)
    run_job(re_index_all_query, [], re_index_all_worker, [], worker_queue=queue)


def re_index_all_query():
    return NewsItem.query()


def re_index_all_worker(ni_key):
    re_index_news_item_by_key(ni_key)


@arguments(ni_key=ndb.Key)
def re_index_news_item_by_key(ni_key):
    ni = ni_key.get()
    return re_index_news_item(ni)


def delete_news_index(config):
    delete_index(config.news_index)


def create_news_index(config):
    # type: (ElasticsearchSettings) -> Any
    index = {
        'mappings': {
            'properties': {
                'app_ids': {
                    'type': 'keyword'
                },
                'txt': {
                    'type': 'text'
                },
                'timestamp': {
                    'type': 'date'
                },
            }
        }
    }
    return create_index(config.news_index, index)


@arguments(news_item=NewsItem)
def re_index_news_item(news_item):
    if not news_item:
        return None

    config = get_elasticsearch_config()
    news_id = str(news_item.id)

    if news_item.status != NewsItem.STATUS_PUBLISHED:
        return delete_doc(config.news_index, news_id)

    si = get_service_identity(news_item.sender)
    if not si:
        return delete_doc(config.news_index, news_id)

    if not get_service_visible_non_transactional(news_item.sender):
        return delete_doc(config.news_index, news_id)

    txt = [si.name]
    if news_item.type == NewsItem.TYPE_NORMAL:
        if news_item.title:
            txt.append(news_item.title)
        if news_item.message:
            txt.append(news_item.message)
    elif news_item.type == NewsItem.TYPE_QR_CODE:
        if news_item.qr_code_caption:
            txt.append(news_item.qr_code_caption)
        if news_item.qr_code_content:
            txt.append(news_item.qr_code_content)
    else:
        return delete_doc(config.news_index, news_id)

    timestamp = news_item.scheduled_at if news_item.scheduled_at else news_item.timestamp
    doc = {
        'app_ids': news_item.app_ids,
        'timestamp': datetime.utcfromtimestamp(timestamp).isoformat() + 'Z',
        'txt': txt
    }
    return index_doc(config.news_index, news_id, doc)


def find_news(app_id, search_string, cursor=None):
    start_offset = long(cursor) if cursor else 0
    amount = 10
    if (start_offset + amount) > 10000:
        amount = 10000 - start_offset
    if amount <= 0:
        return None, []
    if not search_string:
        return None, []
    qry = {
        'size': amount,
        'from': start_offset,
        'query': {
            'bool': {
                'filter': [
                    {'term': {'app_ids': app_id}}
                ],
                'must': [
                    {'match_phrase': {'txt': search_string}}
                ],
                'should': []
            }
        },
        # We don't care what's in the document as we'll have to fetch the datastore model anyway
        'stored_fields': [],
        'sort': [
            "_score",
            {'timestamp': 'desc'}
        ]
    }

    config = get_elasticsearch_config()
    path = '/%s/_search' % config.news_index
    result_data = es_request(path, urlfetch.POST, qry)
    new_cursor = None
    next_offset = start_offset + len(result_data['hits']['hits'])
    if result_data['hits']['total']['relation'] in ('eq', 'gte'):
        if result_data['hits']['total']['value'] > next_offset and next_offset < 10000:
            new_cursor = u'%s' % next_offset
    news_ids = [long(hit['_id']) for hit in result_data['hits']['hits']]
    return new_cursor, news_ids
