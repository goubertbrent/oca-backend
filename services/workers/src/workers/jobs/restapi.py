import logging

from google.appengine.api import users

from common.mcfw.exceptions import HttpNotFoundException
from common.mcfw.restapi import rest
from common.mcfw.rpc import returns, arguments
from common.elasticsearch import get_elasticsearch_config, delete_index
from workers.jobs import create_job_offer_matches, remove_job_offer_matches
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
    
    
@rest('/jobs/v1/users/<user_id:[^/]+>', 'delete', silent=True, silent_result=True)
@returns(dict)
@arguments(user_id=unicode)
def rest_cleanup_user(user_id):
    cleanup_jobs_data(users.User(user_id))
    return {'user_id': user_id}
