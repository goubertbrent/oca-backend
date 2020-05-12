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

from typing import List

from mcfw.properties import long_property, unicode_list_property, typed_property, unicode_property, long_list_property, \
    bool_property
from rogerthat.to import TO
from rogerthat.to.jobs import JobOfferFunctionTO, JobOfferEmployerTO, JobOfferLocationTO, JobOfferContractTO
from rogerthat.utils import date_to_iso_format
from solutions.common.jobs.models import JobOfferContactInformation, JobMatched, JobOfferStatistics, OcaJobOffer, \
    JobSolicitation, JobSolicitationMessage


class JobMatchTO(TO):
    source = long_property('source')
    platform = unicode_property('platform')

    def to_model(self):
        model = JobMatched()
        model.source = self.source
        model.platform = self.platform
        return model


class JobContactInformationTO(TO):
    email = unicode_property('email')
    phone_number = unicode_property('phone_number')

    def to_model(self):
        model = JobOfferContactInformation()
        model.email = self.email
        model.phone_number = self.phone_number
        return model


class EditJobOfferTO(TO):
    job_domains = unicode_list_property('job_domains')
    function = typed_property('function', JobOfferFunctionTO)  # type: JobOfferFunctionTO
    employer = typed_property('employer', JobOfferEmployerTO)  # type: JobOfferEmployerTO
    location = typed_property('location', JobOfferLocationTO)  # type: JobOfferLocationTO
    contract = typed_property('contract', JobOfferContractTO)  # type: JobOfferContractTO
    details = unicode_property('details')
    start_date = unicode_property('start_date', default=None)
    status = long_property('status')
    match = typed_property('match', JobMatchTO)
    contact_information = typed_property('contact_information', JobContactInformationTO)  # type: JobContactInformationTO
    profile = unicode_property('profile')


class OcaJobOfferTO(EditJobOfferTO):
    id = long_property('id')
    internal_id = long_property('internal_id')

    @classmethod
    def from_model(cls, m):
        # type: (OcaJobOffer) -> OcaJobOfferTO
        to = super(OcaJobOfferTO, cls).from_model(m)
        to.id = m.id
        to.internal_id = m.internal_id
        return to


class JobOfferStatusChangeTO(TO):
    status = long_property('status')
    data = unicode_property('date')


class JobOfferStatisticsTO(TO):
    id = long_property('id')
    status_changes = typed_property('status_changes', JobOfferStatusChangeTO)
    unread_solicitations = long_list_property('unread_solicitations')
    publish_date = unicode_property('publish_date')


class JobOfferDetailsTO(TO):
    offer = typed_property('offer', OcaJobOfferTO)
    statistics = typed_property('statistics', JobOfferStatisticsTO)

    @classmethod
    def from_models(cls, job, stats):
        # type: (OcaJobOffer, JobOfferStatistics) -> JobOfferDetailsTO
        return cls(offer=OcaJobOfferTO.from_model(job), statistics=JobOfferStatisticsTO.from_model(stats))


class JobOfferListTO(TO):
    results = typed_property('results', JobOfferDetailsTO, True)  # type: List[JobOfferDetailsTO]


class NewSolicitationMessageTO(TO):
    message = unicode_property('message')


class JobSolicitationMessageTO(TO):
    id = long_property('id')
    reply = bool_property('reply')
    create_date = unicode_property('create_date')
    message = unicode_property('message')


class JobUserInfoTO(TO):
    name = unicode_property('name')
    email = unicode_property('email')
    avatar_url = unicode_property('avatar_url')


class JobSolicitationTO(TO):
    id = long_property('id')
    create_date = unicode_property('create_date')
    update_date = unicode_property('update_date')
    status = long_property('status')
    last_message = typed_property('last_message', JobSolicitationMessageTO)
    user_info = typed_property('user_info', JobUserInfoTO)

    @classmethod
    def from_model(cls, solicitation, last_message, user_info):
        # type: (JobSolicitation, JobSolicitationMessage, JobUserInfoTO) -> JobSolicitationTO
        to = cls.from_partial_model(solicitation, last_message)
        to.user_info = user_info
        return to

    @classmethod
    def from_partial_model(cls, solicitation, last_message):
        # type: (JobSolicitation, JobSolicitationMessage) -> JobSolicitationTO
        to = cls()
        to.id = solicitation.id
        to.create_date = date_to_iso_format(solicitation.create_date)
        to.update_date = date_to_iso_format(solicitation.update_date)
        to.status = solicitation.status
        to.last_message = JobSolicitationMessageTO.from_model(last_message)
        return to


class JobSolicitationListTO(TO):
    results = typed_property('results', JobSolicitationTO, True)


class JobSolicitationMessageListTO(TO):
    results = typed_property('results', JobSolicitationMessageTO, True)


class JobsSettingsTO(TO):
    notifications = long_list_property('notifications')
    emails = unicode_list_property('emails')
