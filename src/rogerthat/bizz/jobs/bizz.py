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


from rogerthat.bizz.jobs.workers import create_job_offer_matches,\
    remove_job_offer_matches, re_index_job_offer
from rogerthat.models.jobs import JobOffer, JobOfferInfo
from rogerthat.utils import try_or_defer


def _set_job_offer_properties(model, data):
    # type: (JobOffer, CreateJobOfferTO) -> JobOffer
    model.source = data.source.to_model()
    model.visible = data.visible
    model.invisible_reason = None
    model.job_domains = data.job_domains
    info = JobOfferInfo()
    info.function = data.function.to_model()
    info.employer = data.employer.to_model()
    info.location = data.location.to_model()
    info.contract = data.contract.to_model()
    info.details = data.details
    model.info = info
    return model


def create_or_update_job_offer(service_email, demo_app_ids, data):
    # type: (unicode, CreateJobOfferTO) -> Tuple[JobOffer, bool]
    job_offer = JobOffer.get_by_source(data.source.type, data.source.id)
    created = False
    if not job_offer:
        job_offer = JobOffer()
        created = True
    job_offer.service_email = service_email
    job_offer.demo_app_ids = demo_app_ids
    _set_job_offer_properties(job_offer, data)
    job_offer.put()
    if job_offer.visible:
        try_or_defer(create_job_offer_matches, job_offer.id)
    else:
        try_or_defer(remove_job_offer_matches, job_offer.id)
    try_or_defer(re_index_job_offer, job_offer.id)
    return job_offer, created
