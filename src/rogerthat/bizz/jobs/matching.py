# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
# NOTICE: THIS FILE HAS BEEN MODIFIED BY GREEN VALLEY BELGIUM NV IN ACCORDANCE WITH THE APACHE LICENSE VERSION 2.0
# Copyright 2018 GIG Technology NV
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
# @@license_version:1.6@@
import logging

from google.appengine.ext import ndb, deferred
from typing import Optional, Tuple, List

from mcfw.rpc import returns, arguments
from rogerthat.bizz.job import run_job, MODE_BATCH
from rogerthat.bizz.jobs.notifications import add_job_to_notifications
from rogerthat.bizz.jobs.search import search_jobs
from rogerthat.consts import JOBS_WORKER_QUEUE, JOBS_CONTROLLER_QUEUE
from rogerthat.models.jobs import JobMatchingCriteria, JobOffer, \
    JobMatch, JobMatchStatus, JobOfferSourceType
from rogerthat.rpc import users
from rogerthat.to.jobs import JobOfferTO
from rogerthat.utils.app import get_app_id_from_app_user
from rogerthat.utils.cloud_tasks import create_task, schedule_tasks
from rogerthat.utils.location import haversine
from rogerthat.utils.models import delete_all_models_by_query


@returns()
@arguments(job_offer=JobOffer)
def create_job_offer_matches(job_offer):
    for job_domain in job_offer.job_domains:
        run_job(create_matches_query_domain, [job_domain], create_matches_for_job, [job_offer.key],
                worker_queue=JOBS_WORKER_QUEUE, controller_queue=JOBS_CONTROLLER_QUEUE, mode=MODE_BATCH, batch_size=25)


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
                to_delete.append(match)
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


def remove_job_offer_matches(job_id):
    # type: (int) -> None
    deferred.defer(_remove_job_offer_matches, job_id, _queue=JOBS_WORKER_QUEUE)


def _remove_job_offer_matches(job_id):
    delete_all_models_by_query(JobMatch.list_by_job_id_and_status(job_id, JobMatchStatus.NEW))


def rebuild_matches_check_current(app_user, cursor=None):
    job_criteria = JobMatchingCriteria.create_key(app_user).get()
    if not job_criteria:
        return
    # Basically a sequential version of run_job with something happening at the end
    matches, new_cursor, has_more = JobMatch.list_by_app_user(app_user) \
        .fetch_page(500, start_cursor=cursor)  # type: Tuple[List[JobMatch], ndb.Cursor, bool]
    to_get = [JobMatchingCriteria.create_key(app_user)] + [JobOffer.create_key(match.job_id) for match in matches]
    models = ndb.get_multi(to_get)
    criteria = models.pop(0)  # type: JobMatchingCriteria
    to_delete = []
    to_put = []
    for match, job_offer in zip(matches, models):  # type: JobMatch, JobOffer
        # If it is a match, the model is updated with new score and the old status is kept
        is_match, distance = does_job_match_criteria(job_offer, criteria)
        if is_match:
            match.score = calculate_job_match_score(job_offer, criteria, distance)
            to_put.append(match)
        elif match.can_delete:
            to_delete.append(match.key)
    ndb.put_multi(to_put)
    ndb.delete_multi(to_delete)

    if has_more:
        deferred.defer(rebuild_matches_check_current, app_user, new_cursor, _queue=JOBS_WORKER_QUEUE)
    else:
        deferred.defer(build_matches_check_new, app_user, _queue=JOBS_WORKER_QUEUE)


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


def calculate_job_match_score(job_offer, criteria, distance):
    # type: (JobOffer, JobMatchingCriteria, float) -> long
    # The lower the distance to the job, the higher the score
    score = abs(distance - criteria.distance)
    if job_offer.source.type == JobOfferSourceType.OCA:
        # Ensure jobs with source OCA are always on top, but still sorted by distance
        score += criteria.distance
    return long(score)


def build_matches_check_new(app_user, cursor=None, send_new_jobs_available=True):
    from rogerthat.bizz.jobs import send_new_jobs_for_activity_types
    criteria = JobMatchingCriteria.create_key(app_user).get()
    if not criteria:
        return

    results, new_cursor = search_jobs(criteria, cursor)
    keys_to_get = results + [JobMatch.create_key(app_user, key.id()) for key in results]
    models = ndb.get_multi(keys_to_get)
    job_offers = models[0: len(models) / 2]
    matches = models[len(models) / 2:]

    to_put = []
    for job_offer, match in zip(job_offers, matches):  # type: JobOffer, Optional[JobMatch]
        if not match:
            distance = get_distance_from_job(job_offer, criteria)
            if distance > criteria.distance:
                continue
            match = JobMatch(key=JobMatch.create_key(app_user, job_offer.id))
            match.status = JobMatchStatus.NEW
            match.job_id = job_offer.id
            match.score = calculate_job_match_score(job_offer, criteria, distance)
            to_put.append(match)
        else:
            # Nothing to do here... score should already be set by rebuild_matches_check_current
            continue
    ndb.put_multi(to_put)
    tasks = []
    new_send_new_jobs_available = False
    if send_new_jobs_available:
        if to_put:
            tasks.append(create_task(send_new_jobs_for_activity_types, app_user, [JobOfferTO.ACTIVITY_TYPE_NEW]))
        else:
            new_send_new_jobs_available = True

    if new_cursor:
        tasks.append(create_task(build_matches_check_new, app_user, new_cursor, new_send_new_jobs_available))
    schedule_tasks(tasks, JOBS_WORKER_QUEUE)
