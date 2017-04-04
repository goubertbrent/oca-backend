# -*- coding: utf-8 -*-
# Copyright 2017 Mobicage NV
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
# @@license_version:1.3@@

from rogerthat.dal import generator
from rogerthat.rpc import users
from rogerthat.utils import now
from google.appengine.ext import db
from mcfw.rpc import arguments, returns
from solutions.djmatic.models import DjMaticProfile, JukeboxAppBranding, DjmaticOverviewLog


@returns([DjmaticOverviewLog])
@arguments(min_timestamp=int, max_timestamp=int)
def get_djmatic_overview_log(min_timestamp, max_timestamp):
    qry = DjmaticOverviewLog.gql("WHERE timestamp > :min_timestamp AND timestamp < :max_timestamp ORDER BY timestamp DESC")
    qry.bind(min_timestamp=min_timestamp, max_timestamp=max_timestamp)
    return generator(qry.run())

@returns(DjMaticProfile)
@arguments(service_user=users.User)
def get_djmatic_profile(service_user):
    return DjMaticProfile.get(DjMaticProfile.create_key(service_user))

@returns(db.GqlQuery)
@arguments()
def get_all_djmatic_profile_keys_query():
    return db.GqlQuery("SELECT __key__ FROM DjMaticProfile")

@returns(JukeboxAppBranding)
@arguments()
def get_jukebox_app_branding():
    return JukeboxAppBranding.get(JukeboxAppBranding.create_key())

@returns(DjMaticProfile)
@arguments(player_id=unicode)
def get_djmatic_profile_via_player_id(player_id):
    qry = DjMaticProfile.gql("WHERE player_id = :player_id")
    qry.bind(player_id=player_id)
    return qry.get()

@returns(tuple)
@arguments(cursor=unicode, batch_size=(int, long))
def get_djmatic_trial_profiles_over_30_days(cursor, batch_size=20):
    qry = DjMaticProfile.gql("WHERE status = :status AND start_trial_time < :epoch ORDER BY start_trial_time ASC")
    qry.bind(status=DjMaticProfile.STATUS_TRIAL, epoch=now() - 30 * 86400)
    qry.with_cursor(cursor)
    profiles = qry.fetch(batch_size)
    if not profiles:
        return [], None, False
    cursor_ = qry.cursor()
    return profiles, unicode(cursor_), True
