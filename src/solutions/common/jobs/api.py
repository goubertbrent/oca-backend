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

from mcfw.consts import REST_TYPE_TO
from mcfw.restapi import rest
from mcfw.rpc import arguments, returns
from rogerthat.rpc import users
from solutions.common.jobs.bizz import create_job_offer, list_job_offers, update_job_offer, get_job_offer
from solutions.common.jobs.notifications import get_jobs_settings, update_jobs_settings
from solutions.common.jobs.solicitations import get_solicitations, get_solicitation_messages, send_solicitation_message
from solutions.common.jobs.to import EditJobOfferTO, JobOfferListTO, JobOfferDetailsTO, JobSolicitationMessageListTO, \
    JobSolicitationListTO, JobSolicitationMessageTO, NewSolicitationMessageTO, JobsSettingsTO


@rest('/common/jobs', 'get', type=REST_TYPE_TO)
@returns(JobOfferListTO)
@arguments()
def rest_list_jobs():
    # type: () -> JobOfferListTO
    service_user = users.get_current_user()
    offers = list_job_offers(service_user)
    return JobOfferListTO(results=[JobOfferDetailsTO.from_models(job, stats) for job, stats in offers])


@rest('/common/jobs', 'post', type=REST_TYPE_TO)
@returns(JobOfferDetailsTO)
@arguments(data=EditJobOfferTO)
def rest_create_job(data):
    # type: (EditJobOfferTO) -> JobOfferDetailsTO
    service_user = users.get_current_user()
    job, stats = create_job_offer(service_user, data)
    return JobOfferDetailsTO.from_models(job, stats)


@rest('/common/jobs/settings', 'get', type=REST_TYPE_TO)
@returns(JobsSettingsTO)
@arguments()
def rest_get_jobs_settings():
    # type: () -> JobsSettingsTO
    service_user = users.get_current_user()
    return JobsSettingsTO.from_model(get_jobs_settings(service_user))


@rest('/common/jobs/settings', 'put', type=REST_TYPE_TO)
@returns(JobsSettingsTO)
@arguments(data=JobsSettingsTO)
def rest_update_jobs_settings(data):
    # type: (JobsSettingsTO) -> JobsSettingsTO
    service_user = users.get_current_user()
    return JobsSettingsTO.from_model(update_jobs_settings(service_user, data))


@rest('/common/jobs/<job_id:\d+>', 'get', type=REST_TYPE_TO)
@returns(JobOfferDetailsTO)
@arguments(job_id=(int, long))
def rest_get_job(job_id):
    # type: (int) -> JobOfferDetailsTO
    service_user = users.get_current_user()
    job, stats = get_job_offer(service_user, job_id)
    return JobOfferDetailsTO.from_models(job, stats)


@rest('/common/jobs/<job_id:\d+>', 'put', type=REST_TYPE_TO)
@returns(JobOfferDetailsTO)
@arguments(job_id=(int, long), data=EditJobOfferTO)
def rest_update_job(job_id, data):
    # type: (int ,EditJobOfferTO) -> JobOfferDetailsTO
    service_user = users.get_current_user()
    job, stats = update_job_offer(service_user, job_id, data)
    return JobOfferDetailsTO.from_models(job, stats)


@rest('/common/jobs/<job_id:\d+>/solicitations', 'get', type=REST_TYPE_TO)
@returns(JobSolicitationListTO)
@arguments(job_id=(int, long))
def rest_get_solicitations(job_id):
    # type: (int) -> JobSolicitationListTO
    return JobSolicitationListTO(results=get_solicitations(users.get_current_user(), job_id))


@rest('/common/jobs/<job_id:\d+>/solicitations/<solicitation_id:\d+>/messages', 'get', type=REST_TYPE_TO)
@returns(JobSolicitationMessageListTO)
@arguments(job_id=(int, long), solicitation_id=(int, long))
def rest_get_solicitation_messages(job_id, solicitation_id):
    # type: (int, int) -> JobSolicitationMessageListTO
    messages = get_solicitation_messages(users.get_current_user(), job_id, solicitation_id)
    return JobSolicitationMessageListTO(results=[JobSolicitationMessageTO.from_model(m) for m in messages])


@rest('/common/jobs/<job_id:\d+>/solicitations/<solicitation_id:\d+>/messages', 'post', type=REST_TYPE_TO)
@returns(JobSolicitationMessageTO)
@arguments(job_id=(int, long), solicitation_id=(int, long), data=NewSolicitationMessageTO)
def rest_send_solicitation_messages(job_id, solicitation_id, data):
    # type: (int, int, NewSolicitationMessageTO) -> JobSolicitationMessageListTO
    message = send_solicitation_message(users.get_current_user(), job_id, solicitation_id, data.message, True)
    return JobSolicitationMessageTO.from_model(message)
