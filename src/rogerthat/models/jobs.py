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

from google.appengine.ext import ndb
from typing import List

from mcfw.utils import Enum
from rogerthat.dal import parent_ndb_key
from rogerthat.models.common import NdbModel
from rogerthat.rpc import users


class JobOfferFunction(NdbModel):
    title = ndb.StringProperty()
    description = ndb.TextProperty()


class JobOfferEmployer(NdbModel):
    name = ndb.StringProperty()


class JobOfferLocation(NdbModel):
    geo_location = ndb.GeoPtProperty()  # type: ndb.GeoPt
    city = ndb.StringProperty()
    street = ndb.StringProperty()
    street_number = ndb.StringProperty()
    country_code = ndb.StringProperty()
    postal_code = ndb.StringProperty()


class JobOfferContract(NdbModel):
    type = ndb.StringProperty()


class JobOfferContactInformation(NdbModel):
    email = ndb.TextProperty()
    phone_number = ndb.TextProperty()
    website = ndb.TextProperty()


class JobOfferInfo(NdbModel):
    function = ndb.LocalStructuredProperty(JobOfferFunction)  # type: JobOfferFunction
    employer = ndb.LocalStructuredProperty(JobOfferEmployer)  # type: JobOfferEmployer
    location = ndb.LocalStructuredProperty(JobOfferLocation)  # type: JobOfferLocation
    contract = ndb.LocalStructuredProperty(JobOfferContract)  # type: JobOfferContract
    contact_information = ndb.LocalStructuredProperty(JobOfferContactInformation)  # type: JobOfferContactInformation
    details = ndb.TextProperty()


class JobOfferSourceType(Enum):
    VDAB = 'vdab'
    OCA = 'oca'


class JobOfferSource(NdbModel):
    type = ndb.StringProperty(choices=JobOfferSourceType.all())
    id = ndb.StringProperty()
    name = ndb.TextProperty()
    avatar_url = ndb.TextProperty()


class JobOffer(NdbModel):
    # VDAB reasons
    INVISIBLE_REASON_SKIP = 'skip'
    INVISIBLE_REASON_STATUS = 'status'
    INVISIBLE_REASON_LOCATION_MISSING = 'location_missing'
    INVISIBLE_REASON_LOCATION_UNKNOWN = 'location_unknown'
    INVISIBLE_REASON_LOCATION_COUNTRY = 'location_country'
    INVISIBLE_REASON_LOCATION_LATLON = 'location_latlon'
    INVISIBLE_REASON_DESCRIPTION = 'description'
    INVISIBLE_REASON_DUBBLE = 'dubble'

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True)

    source = ndb.StructuredProperty(JobOfferSource)  # type: JobOfferSource
    service_email = ndb.StringProperty()  # can be None (when created via VDAB)
    demo_app_ids = ndb.TextProperty(repeated=True)
    data = ndb.JsonProperty(compressed=True)

    visible = ndb.BooleanProperty()
    invisible_reason = ndb.TextProperty()

    info = ndb.LocalStructuredProperty(JobOfferInfo)  # type: JobOfferInfo
    job_domains = ndb.TextProperty(repeated=True)

    @property
    def id(self):
        return self.key.id()

    @classmethod
    def create_key(cls, job_id):
        return ndb.Key(cls, job_id)

    @classmethod
    def get_by_source(cls, source, source_id):
        return cls.query() \
            .filter(cls.source.type == source) \
            .filter(cls.source.id == source_id) \
            .get()

    @classmethod
    def list_by_service(cls, service_email):
        return cls.query().filter(cls.service_email == service_email)


class JobNotificationSchedule(Enum):
    NEVER = 'no_notifications'
    # every 30 minutes as to not spam users when multiple new jobs are posted in a short time
    AS_IT_HAPPENS = 'as_it_happens'
    AT_MOST_ONCE_A_DAY = 'at_most_once_a_day'
    AT_MOST_ONCE_A_WEEK = 'at_most_once_a_week'


class JobMatchingCriteriaNotifications(NdbModel):
    timezone = ndb.StringProperty()
    how_often = ndb.StringProperty(choices=JobNotificationSchedule.all())
    delivery_day = ndb.StringProperty()
    delivery_time = ndb.IntegerProperty()


class JobMatchingCriteria(NdbModel):
    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True)
    last_load_request = ndb.DateTimeProperty()

    address = ndb.TextProperty()
    geo_location = ndb.GeoPtProperty(indexed=False)  # type: ndb.GeoPt
    distance = ndb.IntegerProperty(indexed=False)

    # Currently looking for job. Inactive profiles will have their profile and matches deleted after a certain time
    # TODO: actually create this cron
    active = ndb.BooleanProperty(default=True)
    contract_types = ndb.TextProperty(repeated=True)
    job_domains = ndb.StringProperty(repeated=True)
    keywords = ndb.TextProperty(repeated=True)
    notifications = ndb.LocalStructuredProperty(JobMatchingCriteriaNotifications)  # type: JobMatchingCriteriaNotifications

    @property
    def should_send_notifications(self):
        return self.active and self.notifications and self.notifications.how_often != JobNotificationSchedule.NEVER

    @property
    def app_user(self):
        return users.User(self.key.parent().id().decode('utf8'))

    @classmethod
    def create_key(cls, app_user):
        return ndb.Key(cls, app_user.email(), parent=parent_ndb_key(app_user))

    @classmethod
    def list_by_job_domain(cls, job_domain):
        return cls.query().filter(cls.job_domains == job_domain)

    @classmethod
    def list_inactive(cls):
        return cls.query().filter(cls.active == False)
    
    @classmethod
    def list_inactive_loads(cls, d):
        return cls.query(cls.last_load_request < d)


class JobMatchingNotifications(NdbModel):
    job_ids = ndb.IntegerProperty(repeated=True, indexed=False)  # type: List[int]
    schedule_time = ndb.IntegerProperty()

    @property
    def app_user(self):
        return users.User(self.key.parent().id().decode('utf8'))

    @classmethod
    def create_key(cls, app_user):
        return ndb.Key(cls, app_user.email(), parent=parent_ndb_key(app_user))

    @classmethod
    def list_scheduled(cls, schedule_time):
        return cls.query()\
            .filter(cls.schedule_time < schedule_time)\
            .filter(cls.schedule_time > 0)


class JobMatchStatus(Enum):
    PERMANENTLY_DELETED = 0
    DELETED = 1
    NEW = 2
    STARRED = 3


class JobMatch(NdbModel):
    # Score given to matches created via non-automated means (like pressing a button linked to a job on a news item)
    MANUAL_CREATED_SCORE = 1e8

    create_date = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    update_date = ndb.DateTimeProperty(auto_now=True)
    status = ndb.IntegerProperty(choices=JobMatchStatus.all())
    job_id = ndb.IntegerProperty()  # For querying only
    score = ndb.IntegerProperty()  # Based on location and source - higher score => higher in the list
    chat_key = ndb.TextProperty()  # only set if user has send a message already

    @property
    def app_user(self):
        return users.User(self.key.parent().id().decode('utf8'))

    @property
    def can_delete(self):
        return self.status == JobMatchStatus.NEW

    def get_job_id(self):
        return self.key.id()

    @classmethod
    def create_key(cls, app_user, job_id):
        return ndb.Key(cls, job_id, parent=parent_ndb_key(app_user))

    @classmethod
    def list_by_app_user(cls, app_user):
        return cls.query(ancestor=parent_ndb_key(app_user))

    @classmethod
    def list_by_app_user_and_status(cls, app_user, status):
        return cls.list_by_app_user(app_user) \
            .filter(cls.status == status) \
            .order(-cls.update_date)

    @classmethod
    def list_new_by_app_user(cls, app_user):
        return cls.list_by_app_user(app_user) \
            .filter(cls.status == JobMatchStatus.NEW) \
            .order(-cls.score)

    @classmethod
    def list_by_job_id(cls, job_id):
        return cls.query().filter(cls.job_id == job_id)

    @classmethod
    def list_by_job_id_and_status(cls, job_id, status):
        return cls.list_by_job_id(job_id) \
            .filter(cls.status == status)

    @classmethod
    def manually_create(cls, app_user, job_id):
        match = cls(key=JobMatch.create_key(app_user, job_id))
        match.status = JobMatchStatus.NEW
        match.create_date = datetime.now()
        match.update_date = datetime.now()
        match.job_id = job_id
        match.score = cls.MANUAL_CREATED_SCORE
        return match
