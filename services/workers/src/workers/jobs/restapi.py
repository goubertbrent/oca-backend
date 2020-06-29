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

from google.appengine.api import users
from google.appengine.ext import deferred

from common.consts import JOBS_WORKER_QUEUE
from common.elasticsearch import get_elasticsearch_config, delete_index
from common.mcfw.exceptions import HttpNotFoundException
from common.mcfw.restapi import rest
from common.mcfw.rpc import returns, arguments
from workers.jobs import create_job_offer_matches, remove_job_offer_matches,\
    rebuild_matches_check_current
from workers.jobs.cleanup import cleanup_jobs_data
from workers.jobs.models import JobOffer
from workers.jobs.search import create_matching_index, re_index_job_offer,\
    re_index_all_jobs


def get_job_offer(job_id):
    job_offer = JobOffer.create_key(long(job_id)).get()
    if not job_offer:
        raise Exception('Job offer not found')
    return job_offer


@rest('/jobs/v1/matches/<job_id:[^/]+>', 'put', silent=True, silent_result=True)
@returns(dict)
@arguments(job_id=unicode)
def rest_create_matches(job_id):
    try:
        job_offer = get_job_offer(job_id)
        create_job_offer_matches(job_offer)
        return {'job_id': job_id}
    except:
        logging.debug('rest_create_matches', exc_info=True)
        raise HttpNotFoundException('job_not_found', data={'job_id': job_id})
    
    
@rest('/jobs/v1/matches/<job_id:[^/]+>', 'delete', silent=True, silent_result=True)
@returns(dict)
@arguments(job_id=unicode)
def rest_delete_matches(job_id):
    try:
        job_offer = get_job_offer(job_id)
        remove_job_offer_matches(job_offer.id)
        return {'job_id': job_id}
    except:
        logging.debug('rest_delete_matches', exc_info=True)
        raise HttpNotFoundException('job_not_found', data={'job_id': job_id})
    
    
@rest('/jobs/v1/index', 'put', silent=True, silent_result=True)
@returns(dict)
@arguments()
def rest_create_index():
    config = get_elasticsearch_config()
    create_matching_index(config)
    return {'success': True}


@rest('/jobs/v1/index', 'delete', silent=True, silent_result=True)
@returns(dict)
@arguments()
def rest_delete_index():
    config = get_elasticsearch_config()
    delete_index(config.jobs_index)
    return {'success': True}


@rest('/jobs/v1/reindex', 'put', silent=True, silent_result=True)
@returns(dict)
@arguments()
def rest_reindex():
    re_index_all_jobs()
    return {'success': True}


@rest('/jobs/v1/reindex/<job_id:[^/]+>', 'put', silent=True, silent_result=True)
@returns(dict)
@arguments(job_id=unicode)
def rest_reindex_job(job_id):
    try:
        job_offer = get_job_offer(job_id)
        re_index_job_offer(job_offer)
        return {'job_id': job_id}
    except:
        logging.debug('rest_reindex_job', exc_info=True)
        raise HttpNotFoundException('job_not_found', data={'job_id': job_id})
    

@rest('/jobs/v1/users/<user_id:[^/]+>/matches', 'put', silent=True, silent_result=True)
@returns(dict)
@arguments(user_id=unicode)
def rest_create_user_matches(user_id):
    deferred.defer(rebuild_matches_check_current, users.User(user_id), _queue=JOBS_WORKER_QUEUE)
    return {'user_id': user_id}


@rest('/jobs/v1/users/<user_id:[^/]+>', 'delete', silent=True, silent_result=True)
@returns(dict)
@arguments(user_id=unicode)
def rest_cleanup_user(user_id):
    cleanup_jobs_data(users.User(user_id))
    return {'user_id': user_id}
