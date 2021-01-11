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

from setup_devserver import init_env

init_env()

from rogerthat.bizz.communities.communities import _populate_community
from rogerthat.bizz.communities.models import Community, AppFeatures
from rogerthat.bizz.communities.to import BaseCommunityTO
import base64
import os
import pprint
import sys
import traceback
import unittest

from google.appengine.ext import db

from mcfw.cache import _tlocal
from rogerthat.bizz.qrtemplate import store_template
from rogerthat.bizz.service import create_qr_template_key_name
from rogerthat.bizz.system import DEFAULT_QR_CODE_OVERLAY, DEFAULT_QR_CODE_COLOR, HAND_ONLY_QR_CODE_OVERLAY
from rogerthat.dal import put_and_invalidate_cache, app
from rogerthat.models import App
from rogerthat.utils import now, guid

from solution_server_settings import get_solution_server_settings


class TestCase(unittest.TestCase):
    communities = []

    def log(self, *logs):
        sys.stdout.write("\n" + traceback.format_stack()[-2].splitlines()[0] + "\n")
        for logitem in logs:
            if isinstance(logitem, db.Model):
                sys.stdout.write("  db.model: %s.%s key_name %s key_id %s parent_key name %s" % (
                    logitem.__class__.__module__, logitem.__class__.__name__, logitem.key().name(),
                    logitem.key().id(), logitem.parent_key().name()))
                logitem = db.to_dict(logitem)
            sys.stdout.write('\n  ' + '\n  '.join(pprint.pformat(logitem, 2, 120, None).splitlines()))
        sys.stdout.write("\n\n")

    def set_datastore_hr_probability(self, datastore_hr_probability):
        self.tearDown()
        self.setUp(datastore_hr_probability)

    def clear_request_cache(self):
        _tlocal.request_cache = dict()

    def setUp(self, datastore_hr_probability=0):
        from rogerthat.bizz.profile import create_user_profile
        from rogerthat.settings import get_server_settings
        from rogerthat.rpc import users
        from google.appengine.datastore import datastore_stub_util
        from google.appengine.ext import testbed
        from rogerthat_tests import register_tst_mobile

        os.environ['HTTP_HOST'] = 'localhost:8080'

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.datastore_hr_policy = datastore_stub_util.PseudoRandomHRConsistencyPolicy(
            probability=datastore_hr_probability)
        self.testbed.init_datastore_v3_stub(consistency_policy=self.datastore_hr_policy)
        self.testbed.init_taskqueue_stub(root_path=os.path.join(os.path.dirname(__file__), '..', 'src'))
        self.task_queue_stub = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)
        self.testbed.init_channel_stub()
        self.testbed.init_search_stub()
        self.testbed.init_blobstore_stub()

        ss = get_server_settings()
        ss.baseUrl = "http://localhost:8080"  # not used
        ss.mobidickAddress = "http://1.2.3.4:8090"  # not used
        ss.jabberEndPoints = ["jabber.mobicage.com:8084"]  # Development jabber server
        ss.jabberSecret = "leeg"
        ss.userCodeCipher = "dGVzdCAlcyB0ZXN0"
        ss.dashboardEmail = "dashboard@example.com"
        ss.supportEmail = "support@example.com"
        ss.supportWorkers = ["test@example.com"]
        ss.staticPinCodes = ["0666", "test@example.com"]
        ss.userEncryptCipherPart1 = base64.b64encode('userEncryptCipherPart1')
        ss.userEncryptCipherPart2 = base64.b64encode('userEncryptCipherPart2')

        sss = get_solution_server_settings()
        sss.shop_bizz_admin_emails = ["test@example.com"]
        sss.shop_no_reply_email = "norepy@example.com"

        apps_to_be_created = {App.APP_TYPE_ROGERTHAT: {App.APP_ID_ROGERTHAT: 'Rogerthat'},
                              App.APP_TYPE_CONTENT_BRANDING: {App.APP_ID_OSA_LOYALTY: 'OSA Terminal'},
                              App.APP_TYPE_CITY_APP: {'be-loc': 'Lochristi',
                                                      'be-berlare': 'Berlare',
                                                      'be-beveren': 'Beveren',
                                                      'be-neerpelt': 'Neerpelt',
                                                      'be-sint-truiden': 'Sint-Truiden',
                                                      'es-madrid': 'Madrid'}}

        apps = {}
        qrtemplate_keys = self.setup_qr_templates()
        communities = []

        default_app_features = [AppFeatures.EVENTS_SHOW_MERCHANTS, AppFeatures.JOBS, AppFeatures.NEWS_VIDEO,
                                AppFeatures.NEWS_LOCATION_FILTER, AppFeatures.NEWS_REGIONAL]
        for app_type, apps_dict in apps_to_be_created.iteritems():
            for app_id, app_name in apps_dict.iteritems():
                new_app = App(key=App.create_key(app_id))
                new_app.name = app_name
                new_app.type = app_type
                new_app.core_branding_hash = None
                new_app.facebook_app_id = None
                new_app.ios_app_id = 'com.mobicage.%s' % app_id
                new_app.android_app_id = new_app.ios_app_id
                new_app.is_default = False
                new_app.visible = True
                new_app.secure = True
                new_app.creation_time = now()
                new_app.mdp_client_id = guid()
                new_app.mdp_client_secret = guid()
                new_app.qrtemplate_keys = qrtemplate_keys
                new_app.country = app_id.split('-')[0].upper() if app_type == App.APP_TYPE_CITY_APP else 'BE'
                apps[app_id] = new_app
                community_to = BaseCommunityTO()
                community_to.auto_connected_services = []
                community_to.country = new_app.country
                community_to.default_app = app_id
                community_to.demo = False
                community_to.embedded_apps = []
                community_to.features = default_app_features
                community_to.customization_features = []
                community_to.main_service = None
                community_to.name = app_name
                community_to.signup_enabled = False
                community = _populate_community(Community(), community_to)
                community.put()
                new_app.community_ids = [community.id]
                communities.append(community)
        self.communities = communities

        rogerthat_app = apps[App.APP_ID_ROGERTHAT]
        rogerthat_app.admin_services = ['app_admin@rogerth.at']
        rogerthat_app.is_default = True
        rogerthat_app.facebook_app_id = 188033791211994

        app.get_default_app = lambda: rogerthat_app

        to_put = apps.values() + [ss, sss]
        put_and_invalidate_cache(*to_put)

        users.get_current_user = lambda: users.User('g.audenaert@gmail.com')
        user = users.get_current_user()
        create_user_profile(user, "Geert Audenaert", language='nl')
        m = register_tst_mobile(user.email())
        users.get_current_mobile = lambda: m

    def setup_qr_templates(self):
        qrtemplate_keys = []
        description = "DEFAULT"
        key_name = create_qr_template_key_name('test', description)
        store_template(None, DEFAULT_QR_CODE_OVERLAY, description, "".join(("%X" % c).rjust(2, '0')
                                                                           for c in DEFAULT_QR_CODE_COLOR), key_name)
        qrtemplate_keys.append(key_name)
        description = "HAND"
        key_name = create_qr_template_key_name('test', description)
        store_template(None, HAND_ONLY_QR_CODE_OVERLAY, description, "".join(("%X" % c).rjust(2, '0')
                                                                             for c in DEFAULT_QR_CODE_COLOR), key_name)
        qrtemplate_keys.append(key_name)
        return qrtemplate_keys

    def tearDown(self):
        self.testbed.deactivate()
