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

import mc_unittest
from rogerthat.bizz.profile import create_user_profile
from rogerthat.bizz.system import update_app_asset_response
from rogerthat.capi.system import updateAppAsset
from rogerthat.dal.mobile import get_mobile_settings_cached
from rogerthat.models.properties.profiles import MobileDetails
from rogerthat.rpc import users
from rogerthat.rpc.models import Mobile
from rogerthat.rpc.rpc import logError
from rogerthat.to.app import UpdateAppAssetRequestTO


class Test(mc_unittest.TestCase):

    def testSendNews(self):
        self.set_datastore_hr_probability(1)

        scale_x = 1
        request = UpdateAppAssetRequestTO(u"kind", u"url", scale_x)

        app_user = users.User('geert@example.com')

        user_profile = create_user_profile(app_user, 'geert', language='en')
        mobile = users.get_current_mobile()
        user_profile.mobiles = MobileDetails()
        user_profile.mobiles.addNew(mobile.account, Mobile.TYPE_ANDROID_HTTP, None, u"rogerthat")
        user_profile.put()

        ms = get_mobile_settings_cached(mobile)
        ms.majorVersion = 0
        ms.minorVersion = 2447
        ms.put()

        updateAppAsset(update_app_asset_response, logError, app_user, request=request)

        ms.minorVersion = 2449
        ms.put()

        updateAppAsset(update_app_asset_response, logError, app_user, request=request)
