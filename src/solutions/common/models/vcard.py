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
# @@license_version:1.5@@


from google.appengine.ext import ndb

from rogerthat.models.common import NdbModel


class VCardInfo(NdbModel):
    first_name = ndb.StringProperty(indexed=False)
    last_name = ndb.StringProperty(indexed=False)
    phone_number = ndb.StringProperty(indexed=False)
    email_address = ndb.StringProperty(indexed=False)
    job_title = ndb.StringProperty(indexed=False)
    
    url = ndb.TextProperty()
    image_url = ndb.TextProperty()
    vcard_url = ndb.TextProperty()
    
    @property
    def name(self):
        return u'%s %s' % (self.first_name, self.last_name)
    
    
    @classmethod
    def create_key(cls, user_id):
        return ndb.Key(cls, user_id)