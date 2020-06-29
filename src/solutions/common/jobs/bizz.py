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

from __future__ import unicode_literals

from datetime import datetime

from dateutil.parser import parse as parse_date
from google.appengine.ext.ndb import put_multi, get_multi, GeoPt
from typing import List, Tuple

from mcfw.exceptions import HttpNotFoundException, HttpBadRequestException
from rogerthat.bizz.jobs.bizz import create_or_update_job_offer
from rogerthat.dal import parent_ndb_key
from rogerthat.dal.service import get_service_identity
from rogerthat.models import NdbApp
from rogerthat.models.jobs import JobOfferSourceType
from rogerthat.rpc import users
from rogerthat.to.jobs import CreateJobOfferTO, JobOfferSourceTO
from rogerthat.utils.location import geo_code, GeoCodeException
from rogerthat.utils.service import create_service_identity_user
from solutions import SOLUTION_COMMON, translate
from solutions.common.dal import get_solution_settings
from solutions.common.jobs.models import OcaJobOffer, JobOfferStatistics, JobOfferStatusChange, JobStatus, \
    CONTRACT_TYPE_TRANSLATIONS
from solutions.common.jobs.to import EditJobOfferTO
from solutions.common.restapi import get_branding_settings


class GeoCodeErrorException(HttpBadRequestException):
    def __init__(self, language):
        msg = translate(language, 'could_not_resolve_job_address')
        super(GeoCodeErrorException, self).__init__(msg)


class JobOfferNotFoundException(HttpNotFoundException):
    def __init__(self, language, job_id):
        msg = translate(language, 'job_offer_not_found')
        super(JobOfferNotFoundException, self).__init__(msg, {'id': job_id})


def list_job_offers(service_user):
    # type: (users.User) -> List[Tuple[OcaJobOffer, JobOfferStatistics]]
    offers = [offer for offer in OcaJobOffer.list_by_user(service_user) if offer.status != JobStatus.DELETED]
    stats_keys = [JobOfferStatistics.create_key(service_user, offer.id) for offer in offers]
    stats_models = get_multi(stats_keys)
    return [(offer, stats) for offer, stats in zip(offers, stats_models)]


def get_job_offer(service_user, job_id):
    # type: (users.User, int) -> Tuple[OcaJobOffer, JobOfferStatistics]
    job_offer, stats = get_multi([OcaJobOffer.create_key(service_user, job_id),
                                  JobOfferStatistics.create_key(service_user, job_id)])
    if not job_offer:
        lang = get_solution_settings().main_language
        raise JobOfferNotFoundException(lang, job_id)
    return job_offer, stats


def create_job_offer(service_user, data):
    # type: (users.User, EditJobOfferTO) -> Tuple[OcaJobOffer, JobOfferStatistics]
    language = get_solution_settings(service_user).main_language
    job_id = OcaJobOffer.allocate_ids(1, parent=parent_ndb_key(service_user, SOLUTION_COMMON))[0]
    job_offer = OcaJobOffer(key=OcaJobOffer.create_key(service_user, job_id))
    _set_job_properties(language, job_offer, data)
    stats = JobOfferStatistics(key=JobOfferStatistics.create_key(service_user, job_id))
    stats.status_changes.append(JobOfferStatusChange(status=JobStatus.NEW, date=datetime.now()))
    put_multi([job_offer, stats])
    return job_offer, stats


def update_job_offer(service_user, job_id, data):
    # type: (users.User, int, EditJobOfferTO) -> Tuple[OcaJobOffer, JobOfferStatistics]
    branding_settings = get_branding_settings()
    data.employer.name = data.employer.name.strip()
    data.contact_information.email = data.contact_information.email.strip()
    data.contact_information.phone_number = data.contact_information.phone_number.strip()
    data.location.city = data.location.city.strip()
    data.location.postal_code = data.location.postal_code.strip()
    data.location.street_number = data.location.street_number.strip()
    data.location.street = data.location.street.strip()
    data.function.title = data.function.title.strip()
    data.function.description = data.function.description.strip()
    data.profile = data.profile.strip()

    language = get_solution_settings(service_user).main_language
    job_offer, stats = get_job_offer(service_user, job_id)
    status_changed = job_offer.status != data.status
    if status_changed:
        stats.status_changes.append(JobOfferStatusChange(status=data.status, date=datetime.now()))
    _set_job_properties(language, job_offer, data)
    put_multi([job_offer, stats])
    updated_data = EditJobOfferTO.from_model(job_offer)
    rt_data = CreateJobOfferTO()

    source = JobOfferSourceTO()
    source.avatar_url = branding_settings.avatar_url
    source.type = JobOfferSourceType.OCA
    source.id = unicode(job_offer.id)
    source.name = translate(language, 'our-city-app')

    rt_data.source = source
    rt_data.visible = job_offer.status == JobStatus.ONGOING
    rt_data.function = updated_data.function
    rt_data.job_domains = updated_data.job_domains
    rt_data.location = updated_data.location
    rt_data.contract = updated_data.contract
    rt_data.employer = updated_data.employer
    rt_data.details = _get_details_from_job_offer(job_offer, language)

    demo_app_ids = []
    si =  get_service_identity(create_service_identity_user(service_user))
    default_app = NdbApp.create_key(si.defaultAppId).get()
    if default_app.demo:
        demo_app_ids.append(si.defaultAppId)

    offer, created = create_or_update_job_offer(service_user.email(), demo_app_ids, rt_data)
    if created or not job_offer.internal_id:
        job_offer.internal_id = offer.id
        job_offer.put()
    return job_offer, stats


def _set_job_properties(language, model, data):
    # type: (str, OcaJobOffer, EditJobOfferTO) -> OcaJobOffer
    model.job_domains = data.job_domains
    model.function = data.function.to_model()
    model.employer = data.employer.to_model()
    new_location = data.location.to_model()
    if not model.location or model.location.to_dict() != new_location.to_dict():
        address_str = u'%s %s, %s %s ' % (new_location.street, new_location.street_number,
                                          new_location.postal_code, new_location.city)
        try:
            geocode_result = geo_code(address_str, {'components': 'country:%s' % new_location.country_code})
        except GeoCodeException:
            raise GeoCodeErrorException(language)
        new_location.geo_location = GeoPt(geocode_result['geometry']['location']['lat'],
                                          geocode_result['geometry']['location']['lng'])
    model.location = new_location
    model.contract = data.contract.to_model()
    model.details = data.details
    model.start_date = parse_date(data.start_date) if data.start_date else None
    model.status = data.status
    model.match = data.match.to_model()
    model.contact_information = data.contact_information.to_model()
    model.profile = data.profile
    return model


def _get_details_from_job_offer(job_offer, language):
    # type: (OcaJobOffer, str) -> unicode
    lines = [
        translate(language, 'name_in_city_searching_for', name='**%s**' % job_offer.employer.name,
                  city='**%s**' % job_offer.location.city),
        '## %s ' % job_offer.function.title,
        '%s: %s' % (translate(language, 'oca.contract_type'),
                    translate(language, CONTRACT_TYPE_TRANSLATIONS[job_offer.contract.type])),
        '### %s' % translate(language, 'oca.function_description'),
        job_offer.function.description,
        '',
        '### %s' % translate(language, 'profile'),
        job_offer.profile,
        '',
        job_offer.details,
        '',
        '### %s' % translate(language, 'place_of_employment'),
        job_offer.employer.name,
        """{street} {nr}
{postal_code} {city}
""".format(street=job_offer.location.street, nr=job_offer.location.street_number,
           postal_code=job_offer.location.postal_code, city=job_offer.location.city),
        '',
        '### %s' % translate(language, 'how_and_where_apply'),
        '**{by_email}**: [{email}](tel://{email})'.format(by_email=translate(language, 'by_email'),
                                                          email=job_offer.contact_information.email),
        '**{by_phone}**: [{phone}](tel://{phone})'.format(by_phone=translate(language, 'by_phone'),
                                                          phone=job_offer.contact_information.phone_number),
    ]
    return '\n'.join(lines)
