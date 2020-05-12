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

from rogerthat.rpc.service import ServiceApiException


class LookAndFeelNotFoundException(ServiceApiException):
    def __init__(self, look_and_feel_id):
        message = "The look and feel with id '%d' cannot be found" % look_and_feel_id
        super(LookAndFeelNotFoundException, self).__init__(self.BASE_CODE_LOOK_AND_FEEL + 1, message, look_and_feel_id=look_and_feel_id)


class StyleNotFoundInNavigationItemsException(ServiceApiException):
    def __init__(self, style):
        message = "Style '%s' needs to be in the homescreen.items or toolbar.items" % style
        super(StyleNotFoundInNavigationItemsException, self).__init__(self.BASE_CODE_LOOK_AND_FEEL + 2, message, style=style)
