# -*- coding: utf-8 -*-
# Copyright 2020 Green Valley NV
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
# @@license_version:1.5@@

from google.appengine.ext import ndb, db

from rogerthat.bizz.job import run_job, MODE_BATCH
from rogerthat.models import FriendServiceIdentityConnection, ServiceMenuDef
from rogerthat.utils.models import delete_all_models_by_query
from solutions.common.migrations.publish_all import provision_all
from solutions.common.models import SolutionSettings


def nuke_broadcast_1():
    _cleanup_sln_settings()


def nuke_broadcast_2():
    delete_all_models_by_query(SandwichLastBroadcastDay.query())


def nuke_broadcast_3():
    run_job(_get_broadcast_settings_flow_cache, [], _delete_keys, [], mode=MODE_BATCH, batch_size=250)


def nuke_broadcast_4():
    run_job(_get_broadcast_statistics, [], _delete_keys, [], mode=MODE_BATCH, batch_size=250)


def nuke_broadcast_5():
    run_job(_get_scheduled_broadcasts, [], _delete_keys, [], mode=MODE_BATCH, batch_size=250)


def nuke_broadcast_6():
    run_job(_get_deleted_fsics, [], _delete_keys_db, [], mode=MODE_BATCH, batch_size=250)


def nuke_broadcast_7():
    run_job(_get_service_menu_defs, [], _delete_keys_db, [], mode=MODE_BATCH, batch_size=250)


def nuke_broadcast_8():
    run_job(_get_sln_auto_broadcast, [], _delete_keys, [], mode=MODE_BATCH, batch_size=250)


def nuke_broadcast_9():
    run_job(_get_broadcasts, [], _delete_keys, [], mode=MODE_BATCH, batch_size=250)


def nuke_broadcast_91():
    provision_all(dry_run=False)


def _cleanup_sln_settings():
    run_job(_get_sln_settings, [], _update_sln_settings, [])


def _get_sln_settings():
    return SolutionSettings.all(keys_only=True)


def _update_sln_settings(key):
    settings = db.get(key)  # type: SolutionSettings
    # Remove properties that were removed a long time ago
    for attr in ('broadcast_types', 'broadcast_to_all_locations', 'holiday_out_of_office_message',
                 'holiday_out_of_office_message', 'holidays', 'holiday_active', 'place_types', 'twitter_oauth_token',
                 'twitter_oauth_token_secret', 'put_identity_pending', 'opening_hours', 'menu_item_color',
                 'menu_item_color', 'events_branding_hash', 'event_notifications_enabled', 'search_keywords'):
        if hasattr(settings, attr):
            delattr(settings, attr)
    settings.put()


class SandwichLastBroadcastDay(ndb.Model):
    pass


class BroadcastStatistic(ndb.Model):
    pass


class BroadcastSettingsFlowCache(ndb.Model):
    pass


class SolutionScheduledBroadcast(ndb.Model):
    pass


class SolutionAutoBroadcastTypes(ndb.Model):
    pass


class Broadcast(ndb.Model):
    pass


def _get_broadcast_settings_flow_cache():
    return BroadcastSettingsFlowCache.query()


def _get_broadcast_statistics():
    return BroadcastStatistic.query()


def _get_scheduled_broadcasts():
    return SolutionScheduledBroadcast.query()


def _get_deleted_fsics():
    return FriendServiceIdentityConnection.all(keys_only=True).filter('deleted', True)


def _get_service_menu_defs():
    return ServiceMenuDef.all(keys_only=True).filter('isBroadcastSettings', True)


def _get_sln_auto_broadcast():
    return SolutionAutoBroadcastTypes.query()


def _get_broadcasts():
    return Broadcast.query()


def _delete_keys(keys):
    ndb.delete_multi(keys)


def _delete_keys_db(keys):
    db.delete(keys)
