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
from google.appengine.ext import ndb
from typing import List, Union

from mcfw.properties import unicode_property, typed_property, bool_property, long_property, unicode_list_property, \
    float_property, long_list_property, object_factory
from mcfw.utils import Enum
from rogerthat.models.jobs import JobOffer, JobOfferContract, JobOfferFunction, JobOfferEmployer, JobOfferLocation, \
    JobOfferSource
from rogerthat.to import TO, convert_to_unicode


class JobOfferFunctionTO(TO):
    title = unicode_property('title')
    description = unicode_property('description')

    def to_model(self):
        model = JobOfferFunction()
        model.title = self.title
        model.description = self.description
        return model


class JobOfferEmployerTO(TO):
    name = unicode_property('name')

    def to_model(self):
        model = JobOfferEmployer()
        model.name = self.name
        return model


class LatLonTO(TO):
    lat = float_property('lat')
    lon = float_property('lon')


class JobOfferLocationTO(TO):
    city = unicode_property('city')
    geo_location = typed_property('geo_location', LatLonTO)  # type: LatLonTO
    street = unicode_property('street')
    street_number = unicode_property('street_number')
    country_code = unicode_property('country_code')
    postal_code = unicode_property('postal_code')

    def to_model(self):
        model = JobOfferLocation()
        model.city = convert_to_unicode(self.city)
        model.geo_location = ndb.GeoPt(self.geo_location.lat, self.geo_location.lon) if self.geo_location else None
        model.street = convert_to_unicode(self.street)
        model.street_number = convert_to_unicode(self.street_number)
        model.country_code = convert_to_unicode(self.country_code)
        model.postal_code = convert_to_unicode(self.postal_code)
        return model


class JobOfferContractTO(TO):
    type = unicode_property('1')

    @classmethod
    def from_model(cls, model, language):
        # type: (JobOfferContract, str) -> JobOfferContractTO
        from rogerthat.bizz.jobs.translations import localize as localize_jobs
        to = cls()
        to.type = localize_jobs(language, model.type) if model.type else None
        return to

    def to_model(self):
        model = JobOfferContract()
        model.type = self.type
        return model


class JobOfferActionType(Enum):
    OPEN = 0
    CHAT = 1


class BaseJobOfferAction(TO):
    type = long_property('type')
    label = unicode_property('label', default=None)
    icon = unicode_property('icon', default=None)


class JobOfferOpenActionTO(BaseJobOfferAction):
    type = long_property('type', default=JobOfferActionType.OPEN)
    action = unicode_property('action')  # Any supported url (open:// etc should work too)


class JobOfferChatActionTO(BaseJobOfferAction):
    type = long_property('type', default=JobOfferActionType.CHAT)
    chat_key = unicode_property('chat_key', default=None)


JOB_OFFER_ACTION_MAPPING = {
    JobOfferActionType.OPEN: JobOfferOpenActionTO,
    JobOfferActionType.CHAT: JobOfferChatActionTO,
}


class JobOfferActionTO(object_factory, BaseJobOfferAction):

    def __init__(self):
        super(JobOfferActionTO, self).__init__('type', JOB_OFFER_ACTION_MAPPING, JobOfferActionType)


class JobOfferSourceTO(TO):
    avatar_url = unicode_property('avatar_url', default=None)
    name = unicode_property('name')
    id = unicode_property('id')
    type = unicode_property('type')

    def to_model(self):
        # type: () -> JobOfferSource
        model = JobOfferSource()
        model.avatar_url = self.avatar_url
        model.name = self.name
        model.id = self.id
        model.type = self.type
        return model


class JobOfferTO(TO):
    ACTIVITY_TYPE_NEW = u'new'
    ACTIVITY_TYPE_HISTORY = u'history'
    ACTIVITY_TYPE_STARRED = u'starred'

    job_id = long_property('job_id')
    source = typed_property('source', JobOfferSourceTO)  # type: JobOfferSourceTO
    timestamp = long_property('timestamp')
    function = typed_property('function', JobOfferFunctionTO)  # type: JobOfferFunctionTO
    employer = typed_property('employer', JobOfferEmployerTO)  # type: JobOfferEmployerTO
    location = typed_property('location', JobOfferLocationTO)  # type: JobOfferLocationTO
    contract = typed_property('contract', JobOfferContractTO)  # type: JobOfferContractTO
    details = unicode_property('details')
    actions = typed_property('actions', JobOfferActionTO(), True)

    @classmethod
    def from_job_offer(cls, model, timestamp, language, actions):
        # type: (JobOffer, int, unicode, List[Union[JobOfferChatActionTO, JobOfferOpenActionTO]]) -> JobOfferTO
        to = cls()
        to.job_id = model.id
        to.timestamp = timestamp
        to.source = JobOfferSourceTO.from_model(model.source)
        to.function = JobOfferFunctionTO.from_model(model.info.function)
        to.employer = JobOfferEmployerTO.from_model(model.info.employer)
        to.location = JobOfferLocationTO.from_model(model.info.location)
        to.contract = JobOfferContractTO.from_model(model.info.contract, language)
        to.details = model.info.details
        to.actions = actions
        return to


class CreateJobOfferTO(TO):
    source = typed_property('source', JobOfferSourceTO)  # type: JobOfferSourceTO
    job_domains = unicode_list_property('job_domains')
    function = typed_property('function', JobOfferFunctionTO)  # type: JobOfferFunctionTO
    employer = typed_property('employer', JobOfferEmployerTO)  # type: JobOfferEmployerTO
    location = typed_property('location', JobOfferLocationTO)  # type: JobOfferLocationTO
    contract = typed_property('contract', JobOfferContractTO)  # type: JobOfferContractTO
    details = unicode_property('details')
    visible = bool_property('visible')


class JobCriteriaGeoLocationTO(TO):
    latitude = float_property('latitude')
    longitude = float_property('longitude')


class JobCriteriaLocationTO(TO):
    address = unicode_property('1')
    geo = typed_property('2', JobCriteriaGeoLocationTO)  # type: JobCriteriaGeoLocationTO
    distance = long_property('3')


class JobKeyLabelTO(TO):
    key = unicode_property('1')
    label = unicode_property('2')
    enabled = bool_property('3')


class JobCriteriaNotificationsTO(TO):
    timezone = unicode_property('1')
    how_often = unicode_property('2')
    delivery_day = unicode_property('3')
    delivery_time = long_property('4')


class SaveJobsCriteriaTO(TO):
    location = typed_property('location', JobCriteriaLocationTO)  # type: JobCriteriaLocationTO
    contract_types = unicode_list_property('contract_types')
    job_domains = unicode_list_property('job_domains')
    keywords = unicode_list_property('keywords')
    notifications = typed_property('notifications', JobCriteriaNotificationsTO)  # type: JobCriteriaNotificationsTO


class GetJobsCriteriaRequestTO(TO):
    pass


class GetJobsCriteriaResponseTO(TO):
    active = bool_property('active', default=True)
    location = typed_property('location', JobCriteriaLocationTO, default=None)  # type: JobCriteriaLocationTO
    contract_types = typed_property('contract_types', JobKeyLabelTO, True, default=[])  # type: List[JobKeyLabelTO]
    job_domains = typed_property('job_domains', JobKeyLabelTO, True, default=[])  # type: List[JobKeyLabelTO]
    keywords = unicode_list_property('keywords', default=[])
    notifications = typed_property('notifications', JobCriteriaNotificationsTO, default=None)  # type: JobCriteriaNotificationsTO


class SaveJobsCriteriaRequestTO(TO):
    active = bool_property('active', default=True)
    criteria = typed_property('criteria', SaveJobsCriteriaTO, default=None)


class SaveJobsCriteriaResponseTO(TO):
    active = bool_property('active', default=True)
    new_profile = bool_property('new_profile', default=True)


class GetJobsRequestTO(TO):
    activity_type = unicode_property('1')
    cursor = unicode_property('2', default=None)
    ids = long_list_property('ids', default=[])


class JobOfferProviderTO(TO):
    image_url = unicode_property('image_url', default=None)


class JobsInfoTO(TO):
    title = unicode_property('title')
    description = unicode_property('description')
    providers = typed_property('providers', JobOfferProviderTO, True, default=[])


class GetJobsResponseTO(TO):
    is_profile_active = bool_property('is_profile_active')
    items = typed_property('2', JobOfferTO, True)
    cursor = unicode_property('3', default=None)
    has_more = bool_property('4', default=False)
    info = typed_property('info', JobsInfoTO, default=None)  # type: JobsInfoTO


class BulkSaveJobsRequestTO(TO):
    ids = long_list_property('ids')
    status = long_property('status')


class BulkSaveJobsResponseTO(TO):
    ids = long_list_property('ids')


class JobChatAnonymousTO(TO):
    enabled = bool_property('enabled', default=True)
    default_value = bool_property('default_value', default=False)


class GetJobChatInfoResponseTO(TO):
    job_id = long_property('job_id')
    info_text = unicode_property('info_text', default=None)
    default_text = unicode_property('default_text', default=None)
    anonymous = typed_property('anonymous', JobChatAnonymousTO, default=None)


class GetJobChatInfoRequestTO(TO):
    job_id = long_property('id')


class CreateJobChatRequestTO(TO):
    job_id = long_property('job_id')
    anonymous = bool_property('anonymous', default=False)
    message = unicode_property('message')


class CreateJobChatResponseTO(TO):
    message_key = unicode_property('message_key')


class NewJobsRequestTO(TO):
    creation_time = long_property('1')
    activity_types = unicode_list_property('2')


class NewJobsResponseTO(TO):
    pass
