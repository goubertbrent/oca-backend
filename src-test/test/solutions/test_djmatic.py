# -*- coding: utf-8 -*-
# Copyright 2016 Mobicage NV
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
# @@license_version:1.1@@

import os
from test import set_current_user

from google.appengine.api import urlfetch
import webapp2

from rogerthat.rpc import users
from rogerthat.utils.zip_utils import rename_file_in_zip_blob
import mc_unittest
from solutions.common.bizz import common_provision
from solutions.djmatic.bizz import create_djmatic_service
from solutions.djmatic.handlers import DJMaticHomeHandler
from solutions.djmatic.models import DjMaticProfile, JukeboxAppBranding
from rogerthat_tests.mobicage.bizz import test_branding


class DynObject(object):
    pass

class DJMaticTestCase(mc_unittest.TestCase):

    def test(self):
        self.set_datastore_hr_probability(1)

        print 'Test DJMatic service creation'
        email = u'test.djmatic@djmatic'
        create_djmatic_service(email, u'name', u'https://mobicage.dj-matic.com/default_template.zip',
                               u'#363636', u'secret', u'player_id', DjMaticProfile.PLAYER_TYPE_BOXY)

        # Create fake JukeBox APP Branding
        filename = os.path.join(os.path.dirname(test_branding.__file__), "nuntiuz.zip")
        with open(filename, 'rb') as f:
            blob = rename_file_in_zip_blob(f.read(), "branding.html", "app.html")
        JukeboxAppBranding(key=JukeboxAppBranding.create_key(), blob=blob).put()

        service_user = users.User(email)
        set_current_user(service_user)

        def new_fetch(*args, **kwargs):
            response = DynObject()
            response.content = u"Mocked response.content"
            response.status_code = 200
            return response

        original_fetch = urlfetch.fetch
        urlfetch.fetch = new_fetch
        try:
            print 'Test provisioning'
            common_provision(service_user)
        finally:
            urlfetch.fetch = original_fetch

        print 'Test rendering the home page'
        DJMaticHomeHandler(None, webapp2.Response()).get()
