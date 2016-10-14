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

import logging

from rogerthat.bizz.job import run_job
from rogerthat.models import ServiceIdentityStatistic, ServiceIdentity
from rogerthat.utils import now
from rogerthat.utils.service import create_service_identity_user
from google.appengine.ext import webapp, db
from solutions.djmatic.models import DjMaticProfile

class CheckDjmaticTrialMode(webapp.RequestHandler):

    def get(self):
        run_job(_get_djmatic_created_profiles, [], _calculate_connected_users, [])

def _get_djmatic_created_profiles():
    return DjMaticProfile.all(keys_only=True).filter("status =", DjMaticProfile.STATUS_CREATED)

def _calculate_connected_users(profile_key):
    djmatic_profile = db.get(profile_key)
    sid_key = ServiceIdentityStatistic.create_key(create_service_identity_user(djmatic_profile.service_user,
                                                                               identity=ServiceIdentity.DEFAULT))
    sid = db.get(sid_key)
    if sid and sid.number_of_users >= 10:
        logging.info("convert DjMaticProfile: %s to TRIAL mode", djmatic_profile.service_user)
        now_ = now()
        djmatic_profile.status = DjMaticProfile.STATUS_TRIAL
        djmatic_profile.start_trial_time = now_
        djmatic_profile.status_history.append(DjMaticProfile.STATUS_TRIAL)
        djmatic_profile.status_history_epoch.append(now_)
        djmatic_profile.put()
        logging.debug("Updated DJMaticProfile: %s", db.to_dict(djmatic_profile))
