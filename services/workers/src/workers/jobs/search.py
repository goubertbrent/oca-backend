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

from itertools import chain

from google.appengine.api import urlfetch
from google.appengine.ext import ndb
from typing import Iterable, List, Any, Optional, Tuple

from common.utils.app import get_app_id_from_app_user
from common.consts import JOBS_CONTROLLER_QUEUE, JOBS_WORKER_QUEUE
from common.elasticsearch import create_index, delete_doc_operations,\
    index_doc_operations, get_elasticsearch_config, execute_bulk_request,\
    delete_index, es_request
from common.job import run_job, MODE_BATCH
from workers.jobs.models import JobOffer


def create_matching_index(config):
    # type: (ElasticsearchSettings) -> Any
    index = {
        'mappings': {
            'properties': {
                'source': {
                    'type': 'keyword'
                },
                'details': {
                    'type': 'text'
                },
                'job_domains': {
                    'type': 'keyword'
                },
                'contract_type': {
                    'type': 'keyword'
                },
                'location': {
                    'type': 'geo_point'
                },
                'tags': {
                    'type': 'keyword'
                },
            }
        }
    }
    return create_index(config.jobs_index, index)


def create_job_offer_index_operations(job_offer):
    # type: (JobOffer) -> Iterable[dict]
    if not job_offer.visible:
        return delete_doc_operations(job_offer.id)

    tags = []
    if job_offer.demo_app_ids:
        tags.append('environment#demo')
        for app_id in job_offer.demo_app_ids:
            tags.append('app_id#%s' % app_id)
    else:
        tags.append('environment#production')

    doc = {
        'source': job_offer.source.type,
        'details': job_offer.info.details,
        'job_domains': job_offer.job_domains,
        'contract_type': job_offer.info.contract.type,
        'location': {
            'lat': job_offer.info.location.geo_location.lat,
            'lon': job_offer.info.location.geo_location.lon,
        },
        'tags': tags
    }
    return index_doc_operations(job_offer.id, doc)


def index_jobs(job_offers):
    # type: (Iterable[JobOffer]) -> List[dict]
    config = get_elasticsearch_config()
    operations = chain.from_iterable([create_job_offer_index_operations(job_offer) for job_offer in job_offers])
    return execute_bulk_request(config.jobs_index, operations)


def re_index_job_offer(job_offer):
    # type: (JobOffer) -> dict
    return index_jobs([job_offer])[0]


def _index_jobs_keys(keys):
    # type: (List[ndb.Key]) -> Iterable[dict]
    job_offers = ndb.get_multi(keys)
    return index_jobs(job_offers)


def re_index_all_jobs():
    config = get_elasticsearch_config()
    delete_index(config.jobs_index)
    create_matching_index(config)
    run_job(_get_all_job_offers, [], _index_jobs_keys, [], controller_queue=JOBS_CONTROLLER_QUEUE,
            worker_queue=JOBS_WORKER_QUEUE, mode=MODE_BATCH)


def _get_all_job_offers():
    return JobOffer.query()


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
