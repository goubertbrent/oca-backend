# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
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


import urllib

from google.appengine.api.app_identity import app_identity
from google.appengine.ext import ndb

from rogerthat.models import NdbModel


class LastScriptRun(NdbModel):
    def _get_url(self):
        project_id = app_identity.get_application_id()
        params = {
            'project': project_id,
        }
        if self.task_id:
            params['advancedFilter'] = """resource.type=gae_app
protoPayload.taskName=%s""" % self.task_id
        else:
            params['advancedFilter'] = """resource.type=gae_app
protoPayload.requestId=%s""" % self.request_id
        return u'https://console.cloud.google.com/logs/viewer?%s' % urllib.urlencode(params)

    date = ndb.DateTimeProperty()
    user = ndb.UserProperty()
    request_id = ndb.StringProperty()
    succeeded = ndb.BooleanProperty()
    time = ndb.FloatProperty()
    task_id = ndb.StringProperty()
    url = ndb.ComputedProperty(_get_url)


class ScriptFunction(NdbModel):
    name = ndb.StringProperty()
    last_run = ndb.LocalStructuredProperty(LastScriptRun)
    line_number = ndb.IntegerProperty()


class Script(NdbModel):
    author = ndb.UserProperty()
    modified_on = ndb.DateTimeProperty()
    modified_by = ndb.UserProperty()
    created_on = ndb.DateTimeProperty(auto_now_add=True)
    name = ndb.StringProperty()
    source = ndb.TextProperty()
    functions = ndb.LocalStructuredProperty(ScriptFunction, repeated=True)  # type: list[ScriptFunction]
    version = ndb.IntegerProperty(default=0)

    @property
    def id(self):
        return self.key.id()

    @classmethod
    def create_key(cls, code_id):
        return ndb.Key(cls, code_id)

    @classmethod
    def list(cls):
        return cls.query().order(Script.name)
