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


from google.appengine.api import urlfetch
from rogerthat.bizz.elasticsearch import get_elasticsearch_config, es_request
from rogerthat.models.jobs import JobOffer
from rogerthat.utils.app import get_app_id_from_app_user



def search_jobs(job_criteria, cursor=None, amount=500):
    # type: (JobMatchingCriteria, Optional[str], int) -> Tuple[List[ndb.Key], Optional[str]]
    start_offset = long(cursor) if cursor else 0
    if (start_offset + amount) > 10000:
        amount = 10000 - start_offset
    if amount <= 0:
        return [], None

    qry = {
        'size': amount,
        'from': start_offset,
        '_source': {
            'includes': ['_id'],
        },
        'query': {
            'bool': {
                'must': [],
                'filter': [{
                    'geo_distance': {
                        'distance': '%sm' % job_criteria.distance,
                        'location': {
                            'lat': job_criteria.geo_location.lat,
                            'lon': job_criteria.geo_location.lon,
                        }
                    }
                }],
                'should': [],
            }
        },
        'sort': [
            "_score",
            {
                '_geo_distance': {
                    'location': {
                        'lat': job_criteria.geo_location.lat,
                        'lon': job_criteria.geo_location.lon
                    },
                    'order': 'asc',
                    'unit': 'm'
                }
            }
        ]
    }
    if job_criteria.job_domains:
        job_domains_filter = {
            'bool': {
                'should': [],
                "minimum_should_match": 1
            }
        }
        for job_domain in job_criteria.job_domains:
            job_domains_filter['bool']['should'].append({
                'term': {
                    'job_domains': job_domain
                }
            })
        qry['query']['bool']['filter'].append(job_domains_filter)

    if job_criteria.contract_types:
        contract_types_filter = {
            'bool': {
                'should': [],
                "minimum_should_match": 1
            }
        }
        for contract_type in job_criteria.contract_types:
            contract_types_filter['bool']['should'].append({
                'term': {
                    'contract_type': contract_type
                }
            })
        qry['query']['bool']['filter'].append(contract_types_filter)

    if job_criteria.keywords:
        keywords_filter = {
            'bool': {
                'should': [],
                "minimum_should_match": 1
            }
        }
        for keyword in job_criteria.keywords:
            keywords_filter['bool']['should'].append({
                'term': {
                    'details': keyword
                }
            })
        qry['query']['bool']['filter'].append(keywords_filter)

    app_id = get_app_id_from_app_user(job_criteria.app_user)
    qry['query']['bool']['filter'].append({
        'bool': {
            'should': [{
                'term': {
                    'tags': 'environment#production'
                }
            }, {
                'term': {
                    'tags': 'app_id#%s' % app_id
                }
            }],
            "minimum_should_match": 1
        }
    })

    es_config = get_elasticsearch_config()
    path = '/%s/_search' % es_config.jobs_index
    result_data = es_request(path, urlfetch.POST, qry)
    new_cursor = None
    next_offset = start_offset + len(result_data['hits']['hits'])
    if result_data['hits']['total']['value'] > next_offset and next_offset < 10000:
        new_cursor = u'%s' % next_offset
    result_keys = [JobOffer.create_key(int(hit['_id'])) for hit in result_data['hits']['hits']]
    return result_keys, new_cursor
