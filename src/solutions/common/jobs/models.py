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

from google.appengine.ext import ndb
from typing import List

from mcfw.utils import Enum
from rogerthat.dal import parent_ndb_key
from rogerthat.models import NdbModel
from rogerthat.models.jobs import JobOfferFunction, JobOfferEmployer, JobOfferLocation, JobOfferContract, \
    JobOfferContactInformation
from rogerthat.rpc import users
from solutions import SOLUTION_COMMON


class ContractType(Enum):
    FULLTIME = 'contract_type_001'
    TEMPORARY = 'contract_type_002'
    YOUTH_JOBS = 'contract_type_003'
    FREELANCE = 'contract_type_004'
    FLEXI_JOB = 'contract_type_005'
    SERVICE_CHECK_JOB = 'contract_type_006'
    VOLUNTEER_WORK = 'contract_type_007'


CONTRACT_TYPE_TRANSLATIONS = {
    ContractType.FULLTIME: 'oca.fulltime',
    ContractType.TEMPORARY: 'oca.temporary',
    ContractType.YOUTH_JOBS: 'oca.youth_jobs',
    ContractType.FREELANCE: 'oca.freelance',
    ContractType.FLEXI_JOB: 'oca.flexijob',
    ContractType.SERVICE_CHECK_JOB: 'oca.service_check_job',
    ContractType.VOLUNTEER_WORK: 'oca.volunteer_work',
}


class JobStatus(Enum):
    DELETED = -1
    NEW = 0
    ONGOING = 1
    HIDDEN = 2


class JobMatchSource(Enum):
    NO_MATCH = 0
    OCA = 1
    EXTERN = 2


class JobSolicitationStatus(Enum):
    INITIALIZING = -1  # Waiting for first 'messaging.new_chat_message' callback
    UNREAD = 0  # no new unread messages
    READ = 1  # new unread message by user
    DISABLED = 2  # user left the chat


class JobMatched(NdbModel):
    source = ndb.IntegerProperty()
    platform = ndb.TextProperty()


class OcaJobOffer(NdbModel):
    job_domains = ndb.TextProperty(repeated=True)
    function = ndb.LocalStructuredProperty(JobOfferFunction)  # type: JobOfferFunction
    employer = ndb.LocalStructuredProperty(JobOfferEmployer)  # type: JobOfferEmployer
    location = ndb.LocalStructuredProperty(JobOfferLocation)  # type: JobOfferLocation
    contract = ndb.LocalStructuredProperty(JobOfferContract)  # type: JobOfferContract
    details = ndb.TextProperty()
    start_date = ndb.DateTimeProperty()
    status = ndb.IntegerProperty(choices=JobStatus.all())
    match = ndb.StructuredProperty(JobMatched)
    contact_information = ndb.LocalStructuredProperty(JobOfferContactInformation)  # type: JobOfferContactInformation
    profile = ndb.TextProperty()
    internal_id = ndb.IntegerProperty()

    @property
    def id(self):
        return self.key.id()

    @classmethod
    def create_key(cls, service_user, job_id):
        assert isinstance(job_id, (int, long))
        return ndb.Key(cls, job_id, parent=parent_ndb_key(service_user, SOLUTION_COMMON))

    @classmethod
    def list_by_user(cls, service_user):
        return cls.query(ancestor=parent_ndb_key(service_user, SOLUTION_COMMON))


class JobSolicitationMessage(NdbModel):
    # if True, the message was sent by the service. Otherwise it is send by the user
    reply = ndb.BooleanProperty(indexed=False, default=False)
    create_date = ndb.DateTimeProperty(auto_now_add=True)
    message = ndb.TextProperty()

    @property
    def id(self):
        return self.key.id()

    @property
    def job_key(self):
        # type: () -> ndb.Key
        return self.solicitation_key.parent()

    @property
    def solicitation_key(self):
        # type: () -> ndb.Key
        return self.key.parent()

    @classmethod
    def create_parent_key(cls, service_user, job_id, solicitation_id):
        return JobSolicitation.create_key(service_user, job_id, solicitation_id)

    @classmethod
    def create_key(cls, service_user, job_id, solicitation_id, message_id):
        return ndb.Key(cls, message_id, parent=cls.create_parent_key(service_user, job_id, solicitation_id))

    @classmethod
    def list_by_solicitation(cls, service_user, job_id, solicitation_id):
        return cls.query(ancestor=JobSolicitation.create_key(service_user, job_id, solicitation_id))


class JobOfferStatusChange(NdbModel):
    status = ndb.IntegerProperty(choices=JobStatus.all())
    date = ndb.DateTimeProperty()


class JobSolicitation(NdbModel):
    create_date = ndb.DateTimeProperty(auto_now_add=True)
    update_date = ndb.DateTimeProperty(auto_now=True)
    last_message_key = ndb.KeyProperty()
    user_id = ndb.StringProperty()  # user email
    anonymous = ndb.BooleanProperty()  # If the user wants to share his info with the service (name/email/avatar)
    status = ndb.IntegerProperty(choices=JobSolicitationStatus.all())
    chat_key = ndb.StringProperty()

    @property
    def id(self):
        return self.key.id()

    @property
    def job_key(self):
        # type: () -> ndb.Key
        return self.key.parent()

    @property
    def app_user(self):
        # type: () -> users.User
        return users.User(self.user_id)

    @property
    def service_user(self):
        # type: () -> users.User
        return users.User(self.key.parent().parent().id())

    @classmethod
    def create_parent_key(cls, service_user, job_id):
        return OcaJobOffer.create_key(service_user, job_id)

    @classmethod
    def create_key(cls, service_user, job_id, solicitation_id):
        return ndb.Key(cls, solicitation_id, parent=cls.create_parent_key(service_user, job_id))

    @classmethod
    def list_by_job(cls, service_user, job_id):
        return cls.query(ancestor=OcaJobOffer.create_key(service_user, job_id))

    @classmethod
    def list_by_job_and_user(cls, service_user, job_id, user_id):
        return cls.list_by_job(service_user, job_id).filter(cls.user_id == user_id)

    @classmethod
    def list_unseen_by_service(cls, service_user, min_date, max_date):
        return cls.query(ancestor=parent_ndb_key(service_user, SOLUTION_COMMON)) \
            .filter(cls.status == JobSolicitationStatus.UNREAD) \
            .filter(cls.update_date > min_date) \
            .filter(cls.update_date < max_date) \
            .order(-cls.update_date)


class JobOfferStatistics(NdbModel):
    status_changes = ndb.StructuredProperty(JobOfferStatusChange, repeated=True,
                                            indexed=False)  # type: List[JobOfferStatusChange]
    unread_solicitations = ndb.KeyProperty(JobSolicitation, repeated=True)

    @property
    def id(self):
        return self.key.id()

    @property
    def publish_date(self):
        last_status = self.status_changes[-1]
        if last_status.status == JobStatus.ONGOING:
            return last_status.date
        return None

    @classmethod
    def create_key(cls, service_user, job_id):
        return ndb.Key(cls, job_id, parent=parent_ndb_key(service_user, SOLUTION_COMMON))

    def add_unread(self, key):
        if key not in self.unread_solicitations:
            self.unread_solicitations.append(key)
            return True
        return False

    def remove_unread(self, key):
        if key in self.unread_solicitations:
            self.unread_solicitations.remove(key)
            return True
        return False


class JobNotificationType(Enum):
    NEW_SOLICITATION = 0
    HOURLY_SUMMARY = 1


class JobsSettings(NdbModel):
    notifications = ndb.IntegerProperty(repeated=True, choices=JobNotificationType.all())
    emails = ndb.StringProperty(repeated=True)

    @property
    def service_user(self):
        return users.User(self.key.parent().id())

    @classmethod
    def create_key(cls, service_user):
        return ndb.Key(cls, service_user.email(), parent=parent_ndb_key(service_user, SOLUTION_COMMON))

    @classmethod
    def list_with_hourly_summary_enabled(cls):
        return cls.query().filter(cls.notifications == JobNotificationType.HOURLY_SUMMARY)
