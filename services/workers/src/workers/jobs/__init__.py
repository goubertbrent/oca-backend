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
from google.appengine.ext import ndb, deferred

from common.mcfw.rpc import returns, arguments
from common.utils import now
from common.utils.app import get_app_id_from_app_user
from common.utils.cloud_tasks import create_task, schedule_tasks
from common.utils.location import haversine
from common.utils.models import delete_all_models_by_query
from common.consts import JOBS_WORKER_QUEUE, JOBS_CONTROLLER_QUEUE
from common.job import run_job, MODE_BATCH
from workers.jobs.models import JobOffer, JobMatchingCriteria, JobMatch,\
    JobMatchStatus, JobOfferSourceType, JobMatchingNotifications


@returns()
@arguments(job_offer=JobOffer)
def create_job_offer_matches(job_offer):
    for job_domain in job_offer.job_domains:
        run_job(create_matches_query_domain, [job_domain], create_matches_for_job, [job_offer.key],
                worker_queue=JOBS_WORKER_QUEUE, controller_queue=JOBS_CONTROLLER_QUEUE, mode=MODE_BATCH, batch_size=25)
        

def remove_job_offer_matches(job_id):
    # type: (int) -> None
    deferred.defer(_remove_job_offer_matches, job_id, _queue=JOBS_WORKER_QUEUE)
    

def _remove_job_offer_matches(job_id):
    delete_all_models_by_query(JobMatch.list_by_job_id_and_status(job_id, JobMatchStatus.NEW))


def create_matches_query_domain(job_domain):
    return JobMatchingCriteria.list_by_job_domain(job_domain)


def create_matches_for_job(job_criteria_keys, job_offer_key):
    # type: (List[ndb.Key], ndb.Key) -> None
    job_id = job_offer_key.id()
    match_keys = [JobMatch.create_key(users.User(key.parent().id()), job_id) for key in job_criteria_keys]
    models = ndb.get_multi(job_criteria_keys + match_keys + [job_offer_key])
    job_offer = models.pop()  # type: JobOffer
    if not job_offer.visible:
        logging.warning('Not creating matches for job, job %s is not visible', job_offer.id)
        return
    criteria_models = models[0: len(models) / 2]
    match_models = models[len(models) / 2:]

    to_put = []
    to_delete = []
    notification_criteria = []
    for criteria, match in zip(criteria_models, match_models):  # type: JobMatchingCriteria, Optional[JobMatch]
        is_match, distance = does_job_match_criteria(job_offer, criteria)
        if not is_match:
            if match and match.can_delete:
                to_delete.append(match.key)
        else:
            should_put = False
            if not match:
                should_put = True
                match = JobMatch(key=JobMatch.create_key(criteria.app_user, job_id))
                match.status = JobMatchStatus.NEW
                match.job_id = job_id
                notification_criteria.append(criteria)
            score = calculate_job_match_score(job_offer, criteria, distance)
            if match.score != score:
                match.score = score
                should_put = True
            if should_put:
                to_put.append(match)
    ndb.put_multi(to_put)
    ndb.delete_multi(to_delete)

    tasks = []
    for criteria in notification_criteria:
        if criteria.should_send_notifications:
            tasks.append(create_task(add_job_to_notifications, criteria.app_user, job_id))
    schedule_tasks(tasks, JOBS_WORKER_QUEUE)


def calculate_job_match_score(job_offer, criteria, distance):
    # type: (JobOffer, JobMatchingCriteria, float) -> long
    # The lower the distance to the job, the higher the score
    score = abs(distance - criteria.distance)
    if job_offer.source.type == JobOfferSourceType.OCA:
        # Ensure jobs with source OCA are always on top, but still sorted by distance
        score += criteria.distance
    return long(score)


def does_job_match_criteria(job_offer, criteria):
    # type: (JobOffer, JobMatchingCriteria) -> Tuple[bool, Optional[int]]
    # In theory this should be the same as executing rogerthat.bizz.jobs.matching.search_jobs
    if job_offer.demo_app_ids:
        app_id = get_app_id_from_app_user(criteria.app_user)
        if app_id not in job_offer.demo_app_ids:
            return False, None
    if criteria.job_domains:
        if not any(domain in job_offer.job_domains for domain in criteria.job_domains):
            return False, None
    if criteria.contract_types:
        if not any(contract_type == job_offer.info.contract.type for contract_type in criteria.contract_types):
            return False, None
    if criteria.keywords:
        lower_description = job_offer.info.details.lower()
        if not any(keyword in lower_description for keyword in criteria.keywords):
            return False, None
    distance = get_distance_from_job(job_offer, criteria)
    return distance <= criteria.distance, distance


def get_distance_from_job(job_offer, criteria):
    # type: (JobOffer, JobMatchingCriteria) -> int
    job_location = job_offer.info.location.geo_location
    return haversine(criteria.geo_location.lon, criteria.geo_location.lat, job_location.lon, job_location.lat)


# Transaction is necessary as multiple jobs can be added at the same-ish time
@ndb.transactional()
def add_job_to_notifications(app_user, job_id):
    # type: (users.User, int) -> None
    job_notifications_key = JobMatchingNotifications.create_key(app_user)
    job_notifications = job_notifications_key.get() or JobMatchingNotifications(key=job_notifications_key,
                                                                                schedule_time=0)
    if job_notifications.schedule_time == 0:
        # In 30 minutes
        job_notifications.schedule_time = now() + 30 * 60
    if job_id not in job_notifications.job_ids:
        job_notifications.job_ids.append(job_id)
        job_notifications.put()
