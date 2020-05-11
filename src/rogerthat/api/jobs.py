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

from mcfw.rpc import returns, arguments
from rogerthat.bizz.jobs import save_job_criteria, get_jobs_for_activity_type, \
    get_job_criteria, bulk_save_jobs, get_job_chat_info, create_job_chat
from rogerthat.rpc import users
from rogerthat.rpc.rpc import expose
from rogerthat.to.jobs import SaveJobsCriteriaRequestTO, SaveJobsCriteriaResponseTO, \
    GetJobsRequestTO, GetJobsResponseTO, GetJobsCriteriaResponseTO, \
    GetJobsCriteriaRequestTO, BulkSaveJobsResponseTO, BulkSaveJobsRequestTO, GetJobChatInfoResponseTO, \
    GetJobChatInfoRequestTO, CreateJobChatResponseTO, CreateJobChatRequestTO


@expose(('api',))
@returns(GetJobsCriteriaResponseTO)
@arguments(request=GetJobsCriteriaRequestTO)
def getJobsCriteria(request):
    app_user = users.get_current_user()
    return get_job_criteria(app_user)


@expose(('api',))
@returns(SaveJobsCriteriaResponseTO)
@arguments(request=SaveJobsCriteriaRequestTO)
def saveJobsCriteria(request):
    app_user = users.get_current_user()
    return save_job_criteria(app_user, request)


@expose(('api',))
@returns(GetJobsResponseTO)
@arguments(request=GetJobsRequestTO)
def getJobs(request):
    app_user = users.get_current_user()
    return get_jobs_for_activity_type(app_user, request.activity_type, request.cursor, request.ids)


@expose(('api',))
@returns(BulkSaveJobsResponseTO)
@arguments(request=BulkSaveJobsRequestTO)
def bulkSaveJobs(request):
    # type: (BulkSaveJobsRequestTO) -> BulkSaveJobsResponseTO
    app_user = users.get_current_user()
    ids = bulk_save_jobs(app_user, request.ids, request.status)
    return BulkSaveJobsResponseTO(ids=ids)


@expose(('api',))
@returns(GetJobChatInfoResponseTO)
@arguments(request=GetJobChatInfoRequestTO)
def getJobChatInfo(request):
    # type: (GetJobChatInfoRequestTO) -> GetJobChatInfoResponseTO
    app_user = users.get_current_user()
    return get_job_chat_info(app_user, request.job_id)


@expose(('api',))
@returns(CreateJobChatResponseTO)
@arguments(request=CreateJobChatRequestTO)
def createJobChat(request):
    # type: (CreateJobChatRequestTO) -> CreateJobChatResponseTO
    app_user = users.get_current_user()
    return create_job_chat(app_user, request)
