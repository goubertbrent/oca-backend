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



from google.appengine.ext import ndb, deferred

from rogerthat.bizz.jobs.search import search_jobs
from rogerthat.consts import JOBS_WORKER_QUEUE
from rogerthat.models.jobs import JobMatchingCriteria, JobOffer, JobMatch,\
    JobOfferSourceType, JobMatchStatus
from rogerthat.to.jobs import JobOfferTO
from rogerthat.utils.app import get_app_id_from_app_user
from rogerthat.utils.cloud_tasks import create_task, schedule_tasks
from rogerthat.utils.location import haversine



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
