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

from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.bizz.jobs import send_new_jobs_for_activity_types
from rogerthat.rpc import users
from rogerthat.to.jobs import JobOfferTO


@rest('/workers/jobs/v1/callback/users/<user_id:[^/]+>/matches', 'put', silent=True, silent_result=True)
@returns(dict)
@arguments(user_id=unicode)
def rest_callback_created_matches(user_id):
    app_user = users.User(user_id)
    send_new_jobs_for_activity_types(app_user, [JobOfferTO.ACTIVITY_TYPE_NEW])
    return {'success': True}