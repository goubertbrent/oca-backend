# -*- coding: utf-8 -*-
# Copyright 2020 Green Valley NV
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#z
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# @@license_version:1.5@@
from datetime import datetime

import webapp2
from google.appengine.ext import ndb, db
from google.appengine.ext.deferred import deferred
from typing import List

from rogerthat.bizz.communities.homescreen import HomeScreenTestUser, update_mobiles
from rogerthat.dal import put_and_invalidate_cache
from rogerthat.dal.profile import get_user_profiles
from rogerthat.models import UserProfile
from rogerthat.rpc import users
from rogerthat.utils.cloud_tasks import schedule_tasks, create_task


class HomeScreenTestUsersHandler(webapp2.RequestHandler):
    def get(self):
        now = datetime.now()
        models = HomeScreenTestUser.list_expired(now).fetch()  # type: List[HomeScreenTestUser]
        profiles = get_user_profiles([users.User(model.user_email) for model in models])
        for profile, test_user in zip(profiles, models):  # type: UserProfile
            profile.community_id = test_user.community_id
            profile.home_screen_id = test_user.home_screen_id
            profile.version += 1
        put_and_invalidate_cache(*profiles)
        schedule_tasks([create_task(_update_mobile, profile.key()) for profile in profiles])
        ndb.delete_multi([m.key for m in models])


def _update_mobile(profile_key):
    user_profile = db.get(profile_key)  # type: UserProfile
    update_mobiles(user_profile.user, user_profile)
