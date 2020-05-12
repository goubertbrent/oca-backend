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

import logging

from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.dal.profile import is_service_identity_user, is_trial_service
from rogerthat.rpc import users
from rogerthat.to.profile import CompleteProfileTO


@rest("/mobi/rest/profile/get", "get")
@returns(CompleteProfileTO)
@arguments()
def get_profile_rest():
    from rogerthat.dal.profile import get_profile_info
    profile_info = get_profile_info(users.get_current_user(), skip_warning=True)
    if not profile_info:
        return None
    return CompleteProfileTO.fromProfileInfo(profile_info)


@rest('/mobi/rest/profile/update', 'post')
@returns(unicode)
@arguments(name=unicode, image=unicode, language=unicode)
def rest_update_profile(name, image, language):
    from rogerthat.bizz.profile import update_service_profile, update_user_profile
    user = users.get_current_user()
    try:
        if is_service_identity_user(user):
            update_service_profile(user, image, is_trial_service(user))
        else:
            update_user_profile(user, name, image, language)

    except Exception as e:
        logging.exception(e)
        return e.message
