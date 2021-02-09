# -*- coding: utf-8 -*-
# Copyright 2021 Green Valley NV
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
from __future__ import unicode_literals

import itertools

from functools32 import lru_cache
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
from typing import List

from mcfw.rpc import returns
from rogerthat.bizz.communities.models import Community
from rogerthat.bizz.elasticsearch import delete_index, create_index, delete_doc, index_doc_operations, \
    execute_bulk_request, es_request
from rogerthat.bizz.job import run_job, MODE_BATCH
from rogerthat.bizz.maps.poi.models import PointOfInterest, POIStatus
from rogerthat.bizz.maps.services import SearchTag, get_place_details
from rogerthat.models.elasticsearch import ElasticsearchSettings


@lru_cache(1)
@returns(unicode)
def _get_elasticsearch_index():
    return ElasticsearchSettings.create_key().get().poi_index


def _delete_index():
    return delete_index(_get_elasticsearch_index())


def _create_index():
    request = {
        'mappings': {
            'properties': {
                'id': {
                    'type': 'keyword'
                },
                'name': {
                    'type': 'keyword'
                },
                'suggestion': {
                    'type': 'search_as_you_type'
                },
                'location': {
                    'type': 'geo_point'
                },
                'tags': {
                    'type': 'keyword'
                },
                'txt': {
                    'type': 'text'
                },
            }
        }
    }
    return create_index(_get_elasticsearch_index(), request)


def get_poi_uid(poi_id):
    return unicode(poi_id)


def cleanup_poi_index(poi_id):
    uid = get_poi_uid(poi_id)
    return delete_doc(_get_elasticsearch_index(), uid)


def _get_poi_index_ops(poi, community):
    # type: (PointOfInterest, Community) -> dict
    uid = get_poi_uid(poi.id)
    tags = {
        SearchTag.community(community.id),
        SearchTag.environment(community.demo),
        SearchTag.poi_status(poi.status),
    }
    if poi.status == POIStatus.VISIBLE:
        tags.add(SearchTag.visible_for_end_user())
    if community.country:
        tags.add(SearchTag.country(community.country))
    for place_type in poi.place_types:
        place_details = get_place_details(place_type, 'en')
        if not place_details:
            continue
        tags.add(SearchTag.place_type(place_type))

    txt = [poi.title]
    if poi.description:
        txt.append(poi.description)

    doc = {
        'id': uid,
        'name': poi.title,
        'suggestion': poi.title,
        'location': [],
        'tags': list(tags),
        'txt': txt
    }
    lat = float(poi.location.coordinates.lat)
    lon = float(poi.location.coordinates.lon)
    doc['location'].append({'lat': lat, 'lon': lon})
    return index_doc_operations(uid, doc)


def re_index_poi(poi, community):
    # type: (PointOfInterest, Community) -> dict
    return execute_bulk_request(_get_elasticsearch_index(), _get_poi_index_ops(poi, community))


def _query_re_index_all():
    # Order by community so that we only have to fetch 1 or 2 communities per request
    return PointOfInterest.query().order(PointOfInterest.community_id)


def _worker_re_index_all(poi_keys):
    poi_list = ndb.get_multi(poi_keys)  # type: List[PointOfInterest]
    community_ids = {poi.community_id for poi in poi_list}
    communities = {comm.id: comm for comm in ndb.get_multi([Community.create_key(c) for c in community_ids])}
    ops = itertools.chain.from_iterable(_get_poi_index_ops(poi, communities[poi.community_id]) for poi in poi_list)
    return execute_bulk_request(_get_elasticsearch_index(), ops)


def re_index_all():
    _delete_index()
    _create_index()

    run_job(_query_re_index_all, [], _worker_re_index_all, [], mode=MODE_BATCH)


def _suggest_poi(tags, lat, lon, search, community_ids):
    # type: (List[unicode], float, float, str, List[int]) -> List[dict]
    qry = {
        'size': 12,
        'from': 0,
        '_source': {
            'includes': [],
        },
        'query': {
            'bool': {
                'must': [
                    {
                        'multi_match': {
                            # See https://www.elastic.co/guide/en/elasticsearch/reference/7.x/search-as-you-type.html
                            'query': search,
                            'fields': ['suggestion',
                                       'suggestion._2gram',
                                       'suggestion._3gram'],
                            'type': 'bool_prefix'
                        }
                    }
                ],
                'filter': [{'term': {'tags': tag}} for tag in tags],
            }
        },
        'sort': [
            {'_score': {'order': 'desc'}},
            {
                '_geo_distance': {
                    'location': {
                        'lat': lat,
                        'lon': lon
                    },
                    'order': 'asc',
                    'unit': 'm'
                }
            }
        ]
    }

    if community_ids:
        # Must match one of the specified community ids
        qry['query']['bool']['must'].append({
            'bool': {
                'should': [{'term': {'tags': SearchTag.community(community_id)}} for community_id in community_ids],
                'minimum_should_match': 1
            }
        })

    path = '/%s/_search' % _get_elasticsearch_index()
    result_data = es_request(path, urlfetch.POST, qry)
    results = []
    for hit in result_data['hits']['hits']:
        results.append({'id': hit['_source']['id'], 'name': hit['_source']['name']})
    return results


def search_poi(tags, place_type_tags, lat=None, lon=None, distance=None, cursor=None, limit=50, search_qry=None,
               community_ids=None):
    # we can only fetch up to 10000 items with from param
    start_offset = long(cursor) if cursor else 0

    if (start_offset + limit) > 10000:
        limit = 10000 - start_offset
    if limit <= 0:
        return None, []

    qry = {
        'size': limit,
        'from': start_offset,
        '_source': {
            'includes': ['id', 'name'],
        },
        'query': {
            'bool': {
                'must': [],
                'filter': [],
                'should': []
            }
        },
        'sort': [
            '_score',
        ]
    }

    if lat and lon:
        qry['sort'].insert(0, {
            '_geo_distance': {
                'location': {
                    'lat': lat,
                    'lon': lon
                },
                'order': 'asc',
                'unit': 'm'
            }
        })
    else:
        qry['sort'].insert(0, {'name': {'order': 'asc'}})

    # Must match all tags
    for tag in tags:
        qry['query']['bool']['filter'].append({
            'term': {
                'tags': tag
            }
        })

    if place_type_tags:
        # Must match one of the specified place types
        qry['query']['bool']['must'].append({
            'bool': {
                'should': [{'term': {'tags': tag}} for tag in place_type_tags],
                "minimum_should_match": 1
            }
        })

        if search_qry:
            qry['query']['bool']['should'].append({
                'multi_match': {
                    'query': search_qry,
                    'fields': ['name^500', 'txt^5'],
                    "fuzziness": "1"
                }
            })
    if community_ids:
        # Must match one of the specified community ids
        qry['query']['bool']['must'].append({
            'bool': {
                'should': [{'term': {'tags': SearchTag.community(community_id)}} for community_id in community_ids],
                'minimum_should_match': 1
            }
        })

    elif search_qry:
        qry['query']['bool']['must'].append({
            'multi_match': {
                'query': search_qry,
                'fields': ['name^500', 'txt^5'],
                "operator": "and"
            }
        })
    else:
        if lat and lon:
            qry['query']['bool']['filter'].append({
                'geo_distance': {
                    'distance': '%sm' % distance,
                    'location': {
                        'lat': lat,
                        'lon': lon
                    }
                }
            })

    path = '/%s/_search' % _get_elasticsearch_index()
    result_data = es_request(path, urlfetch.POST, qry)

    new_cursor = None
    if place_type_tags or search_qry:
        pass  # no cursor
    else:
        next_offset = start_offset + len(result_data['hits']['hits'])
        if result_data['hits']['total']['relation'] in ('eq', 'gte'):
            if result_data['hits']['total']['value'] > next_offset and next_offset < 10000:
                new_cursor = '%s' % next_offset

    result_ids = [hit['_source']['id'] for hit in result_data['hits']['hits']]
    return new_cursor, result_ids
