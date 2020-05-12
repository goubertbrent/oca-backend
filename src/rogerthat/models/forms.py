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

from rogerthat.dal import parent_ndb_key
from rogerthat.models import NdbModel


class Form(NdbModel):
    title = ndb.StringProperty()
    update_date = ndb.DateTimeProperty(auto_now=True, indexed=False)
    creation_date = ndb.DateTimeProperty(auto_now_add=True)
    version = ndb.IntegerProperty(default=0, indexed=False)
    sections = ndb.JsonProperty()
    submission_section = ndb.JsonProperty()
    max_submissions = ndb.IntegerProperty(indexed=False, default=-1)
    service = ndb.StringProperty()

    @property
    def id(self):
        return self.key.id()

    @classmethod
    def create_key(cls, id_):
        # Not using model ancestors here as to not hinder write performance of FormSubmission
        return ndb.Key(cls, id_)

    @classmethod
    def list_by_service(cls, service_email):
        return sorted(cls.query(cls.service == service_email), key=lambda form: form.creation_date)


class Submission(NdbModel):
    date = ndb.DateTimeProperty(indexed=False, auto_now_add=True)


class FormSubmissions(NdbModel):
    form_id = ndb.IntegerProperty()
    submissions = ndb.StructuredProperty(Submission, repeated=True)  # type: list[Submission]

    @classmethod
    def create_key(cls, form_id, app_user):
        return ndb.Key(cls, form_id, parent=parent_ndb_key(app_user))

    @classmethod
    def list_by_form(cls, form_id):
        return cls.query(cls.form_id == form_id)
