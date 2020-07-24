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

import logging

from google.appengine.api import search
from google.appengine.ext import ndb

from mcfw.rpc import returns, arguments
from mcfw.utils import normalize_search_string
from rogerthat.bizz.job import run_job
from rogerthat.bizz.news.matching import get_service_visible
from rogerthat.consts import NEWS_MATCHING_QUEUE
from rogerthat.dal.service import get_service_identity
from rogerthat.models.news import NewsItem
from rogerthat.utils import drop_index

NEWS_INDEX = 'NEWS_INDEX'


def re_index_all(queue=NEWS_MATCHING_QUEUE):
    the_index = search.Index(name=NEWS_INDEX)
    drop_index(the_index)
    run_job(re_index_all_query, [], re_index_all_worker, [], worker_queue=queue)


def re_index_all_query():
    return NewsItem.query()


def re_index_all_worker(ni_key):
    re_index_news_item_by_key(ni_key)


@returns(search.Document)
@arguments(ni_key=ndb.Key)
def re_index_news_item_by_key(ni_key):
    ni = ni_key.get()
    return re_index_news_item(ni)


@returns(search.Document)
@arguments(news_item=NewsItem)
def re_index_news_item(news_item):
    if not news_item:
        return None
    the_index = search.Index(name=NEWS_INDEX)
    news_id = str(news_item.id)
    the_index.delete([news_id])

    if not news_item.published or news_item.deleted:
        return None

    si = get_service_identity(news_item.sender)
    if not si:
        return None

    if not get_service_visible(news_item.sender):
        return None

    timestamp = news_item.scheduled_at if news_item.scheduled_at else news_item.timestamp

    fields = [search.AtomField(name='id', value=news_id),
              search.TextField(name='app_ids', value=" ".join(news_item.app_ids)),
              search.TextField(name='sender_name', value=si.name),
              search.NumberField(name='timestamp', value=timestamp)]

    if news_item.type == NewsItem.TYPE_NORMAL:
        if news_item.title:
            fields.append(search.TextField(name='title', value=news_item.title))
        if news_item.message:
            fields.append(search.TextField(name='message', value=news_item.message))
    elif news_item.type == NewsItem.TYPE_QR_CODE:
        if news_item.qr_code_caption:
            fields.append(search.TextField(name='title', value=news_item.qr_code_caption))
        if news_item.qr_code_content:
            fields.append(search.TextField(name='message', value=news_item.qr_code_content))
    else:
        return None

    m_doc = search.Document(doc_id=news_id, fields=fields)
    the_index.put(m_doc)

    return m_doc


def find_news(app_id, search_string, cursor=None):
    the_index = search.Index(name=NEWS_INDEX)
    try:
        sort_expr = search.SortExpression(expression='timestamp', direction=search.SortExpression.DESCENDING)

        q = u"%s app_ids:%s" % (normalize_search_string(search_string), app_id)

        query = search.Query(query_string=q,
                             options=search.QueryOptions(returned_fields=['id'],
                                                         sort_options=search.SortOptions(expressions=[sort_expr]),
                                                         limit=10,
                                                         cursor=search.Cursor(cursor)))

        search_result = the_index.search(query)
        if search_result.results:
            return search_result.results, search_result.cursor.web_safe_string if search_result.cursor else None
    except:
        logging.error('Search query error', exc_info=True)

    return None
