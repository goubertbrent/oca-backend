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
from __future__ import unicode_literals

import logging
from datetime import datetime
from types import NoneType

from google.appengine.ext import ndb, deferred, db
from google.appengine.ext.ndb.query import Cursor
from typing import Optional, List, Union, Tuple

from mcfw.rpc import returns, arguments
from rogerthat.bizz.jobs.matching import rebuild_matches_check_current
from rogerthat.bizz.jobs.notifications import calculate_next_reminder
from rogerthat.bizz.jobs.translations import localize as localize_jobs
from rogerthat.capi.jobs import newJobs
from rogerthat.consts import JOBS_WORKER_QUEUE
from rogerthat.dal.mobile import get_mobile_key_by_account
from rogerthat.dal.profile import get_user_profile
from rogerthat.models import NdbUserProfile
from rogerthat.models.jobs import JobOffer, JobMatchingCriteria, JobMatchingCriteriaNotifications, JobMatch, \
    JobMatchStatus, JobNotificationSchedule, JobOfferSourceType
from rogerthat.rpc import users
from rogerthat.rpc.models import RpcCAPICall, RpcException
from rogerthat.rpc.rpc import mapping, logError, CAPI_KEYWORD_ARG_PRIORITY, \
    PRIORITY_HIGH
from rogerthat.to.jobs import GetJobsResponseTO, JobOfferTO, NewJobsResponseTO, \
    NewJobsRequestTO, SaveJobsCriteriaResponseTO, GetJobsCriteriaResponseTO, \
    JobKeyLabelTO, JobCriteriaLocationTO, JobCriteriaNotificationsTO, JobCriteriaGeoLocationTO, \
    SaveJobsCriteriaRequestTO, JobOfferChatActionTO, JobOfferOpenActionTO, GetJobChatInfoResponseTO, JobChatAnonymousTO, \
    CreateJobChatResponseTO, CreateJobChatRequestTO, JobsInfoTO, JobOfferProviderTO
from rogerthat.translations import localize
from rogerthat.utils import now, get_epoch_from_datetime
from rogerthat.utils.location import coordinates_to_city

TAG_JOB_CHAT = '__rt__.jobs_chat'

CONTRACT_TYPES = [
    'contract_type_001',
    'contract_type_002',
    'contract_type_003',
    'contract_type_004',
    'contract_type_005',
    'contract_type_006',
    'contract_type_007',
]

JOB_DOMAINS = [
    'job_domain_001',
    'job_domain_002',
    'job_domain_003',
    'job_domain_004',
    'job_domain_005',
    'job_domain_006',
    'job_domain_007',
    'job_domain_008',
    'job_domain_009',
    'job_domain_010',
    'job_domain_011',
    'job_domain_012',
    'job_domain_013',
    'job_domain_014',
    'job_domain_015',
    'job_domain_016',
    'job_domain_017',
    'job_domain_018',
    'job_domain_019',
    'job_domain_020',
    'job_domain_021',
    'job_domain_022',
    'job_domain_023',
    'job_domain_024',
]


def get_job_criteria(app_user):
    # type: (users.User) -> GetJobsCriteriaResponseTO
    user_profile = get_user_profile(app_user)

    response = GetJobsCriteriaResponseTO()
    response.location = JobCriteriaLocationTO()
    response.location.address = None
    response.location.geo = None
    response.location.distance = 20000  # 20 Km
    response.contract_types = []
    response.job_domains = []
    response.keywords = []
    response.notifications = JobCriteriaNotificationsTO()
    response.notifications.timezone = None
    response.notifications.how_often = JobNotificationSchedule.NEVER
    response.notifications.delivery_day = 'monday'
    response.notifications.delivery_time = 64800  # 18:00

    job_criteria = JobMatchingCriteria.create_key(app_user).get()  # type: JobMatchingCriteria

    for contract_type in CONTRACT_TYPES:
        to = JobKeyLabelTO()
        to.key = contract_type
        to.label = localize_jobs(user_profile.language, contract_type)
        to.enabled = contract_type in job_criteria.contract_types if job_criteria else False
        response.contract_types.append(to)

    for domain in JOB_DOMAINS:
        to = JobKeyLabelTO()
        to.key = domain
        to.label = localize_jobs(user_profile.language, domain)
        to.enabled = domain in job_criteria.job_domains if job_criteria else False
        response.job_domains.append(to)

    if job_criteria:
        response.active = job_criteria.active
        response.location = JobCriteriaLocationTO()
        response.location.address = job_criteria.address
        response.location.geo = JobCriteriaGeoLocationTO()
        response.location.geo.latitude = job_criteria.geo_location.lat
        response.location.geo.longitude = job_criteria.geo_location.lon
        response.location.distance = job_criteria.distance
        response.keywords = job_criteria.keywords
        if job_criteria.notifications:
            response.notifications.how_often = job_criteria.notifications.how_often
            if job_criteria.notifications.delivery_day:
                response.notifications.delivery_day = job_criteria.notifications.delivery_day
            if job_criteria.notifications.delivery_time:
                response.notifications.delivery_time = job_criteria.notifications.delivery_time
    else:
        response.active = True # user first usage
    return response


@returns(SaveJobsCriteriaResponseTO)
@arguments(app_user=users.User, request=SaveJobsCriteriaRequestTO)
def save_job_criteria(app_user, request):
    # type: (users.User, SaveJobsCriteriaRequestTO) -> SaveJobsCriteriaResponseTO
    job_criteria_key = JobMatchingCriteria.create_key(app_user)
    job_criteria = job_criteria_key.get()  # type: JobMatchingCriteria
    new_job_profile = not job_criteria
    if new_job_profile:
        if not request.criteria:
            return SaveJobsCriteriaResponseTO(active=False, new_profile=new_job_profile)

        job_criteria = JobMatchingCriteria(key=job_criteria_key)
        job_criteria.last_load_request = datetime.utcnow()
        original_job_criteria = None
    else:
        original_job_criteria = job_criteria.to_dict(exclude=['notifications', 'active'])
    
    notifications = None
    job_criteria.active = request.active
    if request.criteria:
        location = request.criteria.location
        notifications = request.criteria.notifications
        if location.geo:
            job_criteria.geo_location = ndb.GeoPt(location.geo.latitude, location.geo.longitude)
            if location.address:
                job_criteria.address = location.address
            else:
                job_criteria.address = coordinates_to_city(job_criteria.geo_location.lat,
                                                           job_criteria.geo_location.lon)
        job_criteria.distance = location.distance
        job_criteria.contract_types = sorted(request.criteria.contract_types)
        job_criteria.job_domains = sorted(request.criteria.job_domains)
        job_criteria.keywords = sorted(request.criteria.keywords)

        if not job_criteria.job_domains:
            raise RpcException('at_least_one_job_domain_required', app_user)

        if not job_criteria.contract_types:
            raise RpcException('at_least_one_contract_type_required', app_user)

    updated_criteria = job_criteria.to_dict(exclude=['notifications', 'active'])
    should_build_matches = original_job_criteria != updated_criteria
    should_calculate_reminder = should_build_matches
    should_clear_notifications = should_build_matches

    og_notifications = job_criteria.notifications and job_criteria.notifications.to_dict()
    if not job_criteria.notifications:
        job_criteria.notifications = JobMatchingCriteriaNotifications()
        job_criteria.notifications.how_often = JobNotificationSchedule.NEVER
    if notifications and notifications.timezone:
        job_criteria.notifications.timezone = notifications.timezone

        if job_criteria.notifications.how_often != notifications.how_often:
            delayed_notification_types = (JobNotificationSchedule.AT_MOST_ONCE_A_DAY,
                                          JobNotificationSchedule.AT_MOST_ONCE_A_WEEK)
            if job_criteria.notifications.how_often in delayed_notification_types and \
                    notifications.how_often not in delayed_notification_types:
                should_clear_notifications = True
            job_criteria.notifications.how_often = notifications.how_often

        job_criteria.notifications.delivery_day = notifications.delivery_day
        job_criteria.notifications.delivery_time = notifications.delivery_time
    if not should_calculate_reminder:
        should_calculate_reminder = job_criteria.notifications.to_dict() != og_notifications

    job_criteria.put()
    if should_build_matches:
        deferred.defer(rebuild_matches_check_current, app_user, _queue=JOBS_WORKER_QUEUE)
    if should_calculate_reminder:
        deferred.defer(calculate_next_reminder, app_user, should_clear_notifications, _queue=JOBS_WORKER_QUEUE)

    return SaveJobsCriteriaResponseTO(active=job_criteria.active, new_profile=new_job_profile)


def get_jobs_for_activity_type(app_user, activity_type, cursor, ids):
    # type: (users.User, unicode, Optional[unicode], List[int]) -> GetJobsResponseTO
    job_criteria_key = JobMatchingCriteria.create_key(app_user)
    user_profile_key = NdbUserProfile.createKey(app_user)
    keys = [job_criteria_key, user_profile_key]
    job_criteria, user_profile = ndb.get_multi(keys)  # type: Optional[JobMatchingCriteria], NdbUserProfile
    resp = GetJobsResponseTO()
    if not job_criteria or not job_criteria.active:
        resp.is_profile_active = False
        resp.items = []
        resp.cursor = None
        resp.has_more = False
    else:
        if cursor is None and activity_type == JobOfferTO.ACTIVITY_TYPE_NEW:
            job_criteria.last_load_request = datetime.utcnow()
            job_criteria.put()

        user_profile = get_user_profile(app_user)
        resp.items, resp.cursor, resp.has_more = _get_jobs(activity_type, app_user, cursor, user_profile.language, ids)
        resp.is_profile_active = True

    info = JobsInfoTO()
    info.title = localize(user_profile.language, 'app_jobs_title')
    info.description = localize(user_profile.language, 'app_jobs_description')
    info.providers = [
        JobOfferProviderTO(image_url='https://storage.googleapis.com/oca-files/jobs/OCA.png'),
        JobOfferProviderTO(image_url='https://storage.googleapis.com/oca-files/jobs/VDAB.jpg'),
    ]
    resp.info = info
    return resp


def bulk_save_jobs(app_user, job_ids, status):
    # type: (users.User, List[int], int) -> List[int]
    keys = [JobMatch.create_key(app_user, job_id) for job_id in job_ids]
    matches = ndb.get_multi(keys)  # type: List[JobMatch]
    to_put = []
    for match in matches:
        if not match:
            continue
        match.status = status
        to_put.append(match)
    ndb.put_multi(to_put)
    return [match.get_job_id() for match in to_put]


@mapping('com.mobicage.capi.jobs.new_jobs_response_handler')
@returns(NoneType)
@arguments(context=RpcCAPICall, result=NewJobsResponseTO)
def new_jobs_response_handler(context, result):
    pass


def _get_jobs(activity_type, app_user, cursor, language, ids):
    # type: (str, users.User, Optional[str], str, List[int]) -> Tuple[List[JobOfferTO], Optional[str], bool]
    fetch_size = 20
    start_cursor = Cursor.from_websafe_string(cursor) if cursor else None

    if activity_type == JobOfferTO.ACTIVITY_TYPE_NEW:
        qry = JobMatch.list_new_by_app_user(app_user)
    elif activity_type == JobOfferTO.ACTIVITY_TYPE_HISTORY:
        qry = JobMatch.list_by_app_user_and_status(app_user, JobMatchStatus.DELETED)
    elif activity_type == JobOfferTO.ACTIVITY_TYPE_STARRED:
        qry = JobMatch.list_by_app_user_and_status(app_user, JobMatchStatus.STARRED)
    else:
        raise Exception('Unknown activity type %s' % activity_type)
    job_matches_keys, new_cursor, has_more = qry.fetch_page(
        fetch_size, start_cursor=start_cursor, keys_only=True)  # type: List[ndb.Key], Cursor, bool
    match_keys = [JobMatch.create_key(app_user, job_id) for job_id in ids if job_id] + \
                 [key for key in job_matches_keys if key.id() not in ids]
    offer_keys = [JobOffer.create_key(match_key.id()) for match_key in match_keys]
    models = ndb.get_multi(match_keys + offer_keys)  # type: List[Union[JobMatch, JobOffer]]
    job_matches = models[0: len(models) / 2]
    job_offers = models[len(models) / 2:]

    items = []
    to_put = []
    for match, job_offer in zip(job_matches, job_offers):  # type: JobMatch, JobOffer
        if not match:
            # this should only happen when the job was requested using the 'ids' property
            # like when the jobs activity is opened via a button on a news item
            if job_offer.id not in ids:
                logging.warning('Expected JobMatch to exist, creating it anyway...')
            logging.debug('Creating manual JobMatch entry for job %d', job_offer.id)
            match = JobMatch.manually_create(app_user, job_offer.id)
            to_put.append(match)
        timestamp = get_epoch_from_datetime(match.update_date)
        items.append(JobOfferTO.from_job_offer(job_offer, timestamp, language,
                                               get_job_offer_actions(job_offer, match, language)))
    ndb.put_multi(to_put)
    return items, new_cursor.to_websafe_string().decode('utf-8') if new_cursor else None, has_more


def get_job_offer_actions(job_offer, match, language):
    # type: (JobOffer, JobMatch, str) -> List[Union[JobOfferChatActionTO, JobOfferOpenActionTO]]
    actions = []
    if job_offer.source.type == JobOfferSourceType.OCA:
        action = JobOfferChatActionTO()
        action.label = localize(language, 'open_chat')
        action.chat_key = match.chat_key  # possibly None
        action.icon = 'fa-comment'
        actions.append(action)
    return actions


def send_new_jobs_for_activity_types(app_user, activity_types):
    user_profile = get_user_profile(app_user)
    if not user_profile.mobiles:
        return

    request = NewJobsRequestTO()
    request.creation_time = now()
    request.activity_types = activity_types
    mobiles = db.get([get_mobile_key_by_account(mobile_detail.account) for mobile_detail in user_profile.mobiles])
    for mobile in mobiles:
        ios_push_id = None
        if mobile.is_ios:
            ios_push_id = mobile.iOSPushId

        kwargs = {}
        if ios_push_id:
            kwargs[CAPI_KEYWORD_ARG_PRIORITY] = PRIORITY_HIGH
        newJobs(new_jobs_response_handler, logError, app_user, request=request, MOBILE_ACCOUNT=mobile, **kwargs)


def get_job_chat_info(app_user, job_id):
    # type: (users.User, int) -> GetJobChatInfoResponseTO
    lang = get_user_profile(app_user).language
    response = GetJobChatInfoResponseTO()
    response.anonymous = JobChatAnonymousTO()
    response.job_id = job_id
    response.anonymous.enabled = True
    response.anonymous.default_value = False
    response.default_text = ''
    response.info_text = localize(lang, 'job_info_text')
    return response


def create_job_chat(app_user, request):
    # type: (users.User, CreateJobChatRequestTO) -> CreateJobChatResponseTO
    keys = [JobMatch.create_key(app_user, request.job_id),
            JobOffer.create_key(request.job_id)]
    job_match, job_offer = ndb.get_multi(keys)  # type: JobMatch, JobOffer
    if not job_match.chat_key:
        # If you ever want to create a separate service for jobs, you'll have to create a service api callback for this
        from solutions.common.jobs.solicitations import create_job_solicitation
        message_key = create_job_solicitation(app_user, job_offer, request)
        job_match.chat_key = message_key
        job_match.put()
    response = CreateJobChatResponseTO()
    response.message_key = job_match.chat_key
    return response
