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

import mc_unittest
from rogerthat.bizz.location import get_location_response_handler
from rogerthat.capi.location import getLocation
from rogerthat.rpc import users
from rogerthat.rpc.rpc import logError
from rogerthat.to.location import GetLocationRequestTO


class Test(mc_unittest.TestCase):


    def testGetLocation(self):
        request = GetLocationRequestTO()
        request.friend = users.get_current_user().email()
        mobile = users.get_current_mobile()
        request.high_prio = False
        request.target = GetLocationRequestTO.TARGET_MOBILE if mobile else GetLocationRequestTO.TARGET_WEB
        getLocation(get_location_response_handler, logError, users.get_current_user(), request=request)
