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

import time
from collections import defaultdict
from datetime import datetime

from dateutil.relativedelta import relativedelta
from google.appengine.ext import ndb
from google.appengine.ext.deferred import deferred

from rogerthat.bizz.communities.models import Community, CommunityUserStats, CountOnDate, CommunityUserStatsHistory
from rogerthat.models import App, NdbUserProfile
from rogerthat.utils import log_offload


def get_country_code_from_app_id(app_id):
    split = app_id.replace('em-', '').split('-')
    if len(split[0]) == 2:
        code = split[0]
    else:
        code = 'be'
    return code.upper()


def generate_app_stats_history(log_type):
    if log_type == 'rogerthat.created_apps':
        stats_func = _generate_created_app_stats
    elif log_type == 'rogerthat.released_apps':
        stats_func = _generate_released_app_stats
    else:
        raise Exception('Invalid log type')
    d = datetime.utcfromtimestamp(1410963082)
    date = datetime(year=d.year, month=d.month, day=d.day)
    all_apps = App.all().fetch(None)
    now = datetime.now()
    while date < now:
        ts = time.mktime(date.timetuple())
        result = stats_func([app for app in all_apps if app.creation_time <= ts])
        log_offload.create_log(None, log_type, result, None, timestamp=ts)
        date = date + relativedelta(days=1)


def _generate_created_app_stats(apps):
    # type: (list[App]) -> dict[str, dict[str, int]]
    result = defaultdict(lambda: defaultdict(lambda: 0))
    for app in apps:
        result[app.type_str][get_country_code_from_app_id(app.app_id)] += 1
    return result


def _generate_released_app_stats(apps):
    # type: (list[App]) -> dict[str, dict[str, int]]
    # All released apps that aren't demo apps
    result = defaultdict(lambda: defaultdict(lambda: 0))
    for app in apps:
        if not app.disabled and app.ios_app_id not in (None, '-1') and not app.demo:
            result[app.type_str][get_country_code_from_app_id(app.app_id)] += 1
    return result


def generate_created_app_stats(apps):
    # type: (list[App]) -> tuple[str, dict[str, dict[str, int]]]
    result = _generate_created_app_stats(apps)
    return 'rogerthat.created_apps', result


def generate_released_app_stats(apps):
    # type: (list[App]) -> tuple[str, dict[str, dict[str, int]]]
    result = _generate_released_app_stats(apps)
    return 'rogerthat.released_apps', result


def generate_users_per_app_stats(app_ids):
    # type: (list[unicode]) -> tuple[str, dict[str, int]]
    rpcs = {app_id: NdbUserProfile.list_by_app(app_id).count_async() for app_id in app_ids}
    result = {app_id: rpc.get_result() for app_id, rpc in rpcs.iteritems()}
    return 'rogerthat.total_users', result


def generate_all_stats():
    apps = App.all().fetch(None)
    d = datetime.now()
    date = datetime(year=d.year, month=d.month, day=d.day)
    results = [
        generate_created_app_stats(apps),
        generate_released_app_stats(apps),
        generate_users_per_app_stats([app.app_id for app in apps if not app.disabled])
    ]
    for type_, result in results:
        log_offload.create_log(None, type_, result, None, timestamp=time.mktime(date.timetuple()))
    deferred.defer(_create_community_stats)


def _create_community_stats():
    community_ids = [key.id() for key in Community.query().fetch(keys_only=True)]
    rpcs = {community_id: NdbUserProfile.list_by_community(community_id).count_async()
            for community_id in community_ids}
    for community_id in community_ids:
        stats_key = CommunityUserStatsHistory.create_key(community_id)
        user_count = rpcs[community_id].get_result()
        stats = CommunityUserStats(key=CommunityUserStats.create_key(community_id))
        stats.count = user_count
        history = stats_key.get() or CommunityUserStatsHistory(key=stats_key)
        history.stats.append(CountOnDate(count=user_count))
        # Intentionally saving in for loop as the history model might get quite large
        ndb.put_multi([stats, history])
