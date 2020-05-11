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

from types import NoneType

from rogerthat.rpc import users
from rogerthat.to.system import LogErrorRequestTO
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments


@rest("/unauthenticated/mobi/logging/web_error", "post")
@returns(NoneType)
@arguments(description=unicode, errorMessage=unicode, timestamp=int, user_agent=unicode)
def log_error(description, errorMessage, timestamp, user_agent):
    request = LogErrorRequestTO()
    request.description = description
    request.errorMessage = errorMessage
    request.mobicageVersion = u"web"
    request.platform = 0
    request.platformVersion = user_agent
    request.timestamp = timestamp
    from rogerthat.bizz.system import logErrorBizz
    return logErrorBizz(request, users.get_current_user(), session=users.get_current_session())
