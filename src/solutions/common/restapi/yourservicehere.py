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

from mcfw.properties import azzert
from mcfw.rpc import arguments, returns
from rogerthat.rpc import users
from rogerthat.rpc.service import service_api
from rogerthat.to.profile import TrialServiceTO
from solution_server_settings import get_solution_server_settings


@service_api(function=u"service.trial_signup")
@returns(TrialServiceTO)
@arguments(user=unicode, service_name=unicode, service_description=unicode)
def signup(user, service_name, service_description):
    solution_server_settings = get_solution_server_settings()
    azzert(users.get_current_user() == users.User(solution_server_settings.solution_trial_service_email))

    user = users.User(user)
    from rogerthat.bizz.service.yourservicehere import signup as trial_signup
    return trial_signup(user, service_name, service_description, True)
