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

import itertools

from google.appengine.api import urlfetch

from rogerthat.bizz.app_search.models import AppSearchItemKeyword, AppSearch
from rogerthat.bizz.elasticsearch import es_request, delete_index, create_index,\
    execute_bulk_request, index_doc_operations, delete_doc_operations
from rogerthat.bizz.maps.services import SearchTag
from rogerthat.models.elasticsearch import ElasticsearchSettings


def _get_elasticsearch_index():
    return ElasticsearchSettings.create_key().get().app_search_index


def _delete_index():
    return delete_index(_get_elasticsearch_index())


def _create_index():
    request = {
        'mappings': {
            'properties': {
                'suggestions_priority_high': {
                    'type': 'search_as_you_type'
                },
                'suggestions': {
                    'type': 'search_as_you_type'
                },
                'tags': {
                    'type': 'keyword'
                }
            }
        }
    }
    return create_index(_get_elasticsearch_index(), request)


def _index_app_search_item(app_search, uid):
    global_uid = u'%s-%s#%s' % (app_search.community_id, app_search.home_screen_id, uid)
    app_search_item = app_search.get_item_by_uid(uid)
    if not app_search_item:
        return delete_doc_operations(global_uid)

    tags = [SearchTag.community(app_search.community_id),
            SearchTag.home_screen_id(app_search.home_screen_id)]
    suggestions_priority_high = set()
    suggestions = set()

    suggestions_priority_high.add(app_search_item.title)
    if app_search_item.description:
        suggestions_priority_high.add(app_search_item.description)
    for keyword in app_search_item.keywords:
        if keyword.priority == AppSearchItemKeyword.PRIORITY_HIGH:
            suggestions_priority_high.add(keyword.text)
        else:
            suggestions.add(keyword.text)

    doc = {
        'suggestions_priority_high': list(suggestions_priority_high),
        'suggestions': list(suggestions),
        'tags': tags
    }
    return index_doc_operations(global_uid, doc)


def index_app_search(community_id, home_screen_id, all_uids_incuding_just_removed_once):
    app_search = AppSearch.create_key(community_id, home_screen_id).get()
    operations = itertools.chain.from_iterable([_index_app_search_item(app_search, uid) for uid in all_uids_incuding_just_removed_once])
    return execute_bulk_request(_get_elasticsearch_index(), operations)


def _suggest_items(search, community_id, home_screen_id):
    tags = [SearchTag.community(community_id),
            SearchTag.home_screen_id(home_screen_id)]
    qry = {
        'size': 12,
        'from': 0,
        '_source': {
            'includes': ['_id'],
        },
        'query': {
            'bool': {
                'must': [
                    {
                        'multi_match': {
                            # See https://www.elastic.co/guide/en/elasticsearch/reference/7.x/search-as-you-type.html
                            'query': search,
                            'fields': ['suggestions_priority_high^5',
                                       'suggestions_priority_high._2gram^5',
                                       'suggestions_priority_high._3gram^5',
                                       'suggestions',
                                       'suggestions._2gram',
                                       'suggestions._3gram'],
                            'type': 'bool_prefix'
                        }
                    }
                ],
                'filter': [{'term': {'tags': tag}} for tag in tags],
            }
        },
        'sort': [
            {'_score': {'order': 'desc'}},
        ]
    }

    path = '/%s/_search' % _get_elasticsearch_index()
    result_data = es_request(path, urlfetch.POST, qry)
    results = []
    for hit in result_data['hits']['hits']:
        app_search_tag, uid = hit['_id'].rsplit('#', 1)
        community_id, home_screen_id = app_search_tag.split('-', 1)
        results.append({'community_id': long(community_id),
                        'home_screen_id': home_screen_id,
                        'uid': uid})
    return results