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
from types import NoneType

from rogerthat.settings import get_server_settings
from rogerthat.utils import now
from google.appengine.api import users as gae_users, xmpp
from google.appengine.ext import deferred
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from solutions.common.bizz import common_provision
from solutions.common.dal import get_solution_settings
from solutions.djmatic.dal import get_djmatic_profile_via_player_id, get_djmatic_trial_profiles_over_30_days
from solutions.djmatic.models import DjmaticOverviewLog
from solutions.djmatic.to import DjmaticProfileTO, DjmaticTrialsTO


@rest("/djmatic_overview/get_djmatic_status", "post")
@returns(DjmaticProfileTO)
@arguments(player_id=unicode)
def get_djmatic_status(player_id):
    djmatic_profile = get_djmatic_profile_via_player_id(player_id)
    if djmatic_profile:
        return DjmaticProfileTO.fromDjmaticProfile(djmatic_profile)
    else:
        return None

@rest("/djmatic_overview/update_djmatic_status", "post")
@returns(NoneType)
@arguments(status=unicode, player_id=unicode)
def update_djmatic_status(status, player_id):
    djmatic_profile = get_djmatic_profile_via_player_id(player_id)
    if djmatic_profile:
        now_ = now()
        user = gae_users.get_current_user()
        status_from = djmatic_profile.status_string(djmatic_profile.status)
        status_to = djmatic_profile.status_string(int(status))
        settings = get_solution_settings(djmatic_profile.service_user)
        DjmaticOverviewLog(timestamp=now_, email=user.email(), player_id=player_id, description="%s >>> %s" %
                           (status_from, status_to)).put()

        server_settings = get_server_settings()
        xmpp.send_message(server_settings.xmppInfoMembers, "DJ-Matic: %s - %s (%s days created, %s days trial) updated from: %s to: %s" %
                          (settings.name, player_id, djmatic_profile.days_created, djmatic_profile.days, status_from, status_to))

        djmatic_profile.status = int(status)

        djmatic_profile.status_history.append(int(status))
        djmatic_profile.status_history_epoch.append(now_)

        if not djmatic_profile.start_trial_time:
            djmatic_profile.start_trial_time = now_

        djmatic_profile.put()
        deferred.defer(common_provision, djmatic_profile.service_user)
    else:
        logging.warn("DJMATIC profile does not exists: %s" % player_id)


@rest("/djmatic_overview/load_trials", "post")
@returns(DjmaticTrialsTO)
@arguments(cursor=unicode)
def load_trials(cursor):
    if not cursor:
        cursor = None

    to = DjmaticTrialsTO()
    trials, to.cursor, to.has_more = get_djmatic_trial_profiles_over_30_days(cursor)
    to.djmatic_profiles = [DjmaticProfileTO.fromDjmaticProfile(trial) for trial in trials]
    return to
