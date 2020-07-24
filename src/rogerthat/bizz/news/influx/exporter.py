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
from datetime import datetime

from dateutil.relativedelta import relativedelta
from google.appengine.ext import deferred, ndb
from typing import Iterable

from rogerthat.bizz.news.influx import get_influxdb_client, get_age_field_key
from rogerthat.consts import NEWS_STATS_QUEUE
from rogerthat.models.news import NewsItemStatisticsExporter, NewsItemActionStatistics
from rogerthat.utils.cloud_tasks import create_task, schedule_tasks


@ndb.transactional()
def run():
    key = NewsItemStatisticsExporter.create_key('influx')
    settings = key.get()
    if not settings:
        logging.info('NewsItemStatisticsExporter not set for type "influx"')
        return

    start = settings.exported_until
    end_ = datetime.utcnow()
    minute = end_.minute
    # Always round down minute to nearest 5 minutes
    while minute % 5 != 0:
        minute -= 1

    end = datetime(year=end_.year, month=end_.month, day=end_.day, hour=end_.hour, minute=minute)
    settings.exported_until = end
    settings.put()
    deferred.defer(_run_scheduler, start, end, _transactional=True, _queue=NEWS_STATS_QUEUE)


def _run_scheduler(start, end):
    tasks = []
    while True:
        end_tmp = start + relativedelta(minutes=5)
        if end_tmp < end:
            tasks.append(create_task(_run, start, end_tmp, _countdown=5))
            start = end_tmp
        else:
            tasks.append(create_task(_run, start, end, _countdown=5))
            break

    schedule_tasks(tasks, NEWS_STATS_QUEUE)


def _get_gender_field_key(gender):
    if gender == 'unknown':
        return 'gender-unknown'
    return gender


def _create_item_stats_key(s):
    # type: (NewsItemActionStatistics) -> str
    return '%s_%d_%s' % (s.get_app_id(), s.news_id, s.action)


def _create_global_stats_key(s):
    # type: (NewsItemActionStatistics) -> str
    return '%s_%s' % (s.get_app_id(), s.action)


def fill_fields_for_stats(all_stats, stats_key, statistic):
    # type: (dict, str, NewsItemActionStatistics) -> None
    if stats_key not in all_stats:
        all_stats[stats_key] = {
            'app_id': statistic.get_app_id(),
            'news_id': statistic.news_id,
            'action': statistic.action,
            'fields': {
                'total': 0,
            }
        }
    fields = all_stats[stats_key]['fields']

    if statistic.age:
        age_key = get_age_field_key(statistic.age)
        if age_key not in fields:
            fields[age_key] = 1
        else:
            fields[age_key] += 1
    if statistic.gender:
        gender_key = _get_gender_field_key(statistic.gender)
        if gender_key not in fields:
            fields[gender_key] = 1
        else:
            fields[gender_key] += 1
    fields['total'] += 1


def _run(start, end, params=None):
    time_diff = (end - start)
    if time_diff.total_seconds() != 300.0:
        raise Exception('Start & end where more or less then 5 minutes apart')

    item_stats = {}
    global_stats = {}

    qry = NewsItemActionStatistics.list_between(start, end)  # type: Iterable[NewsItemActionStatistics]
    for statistic in qry:
        fill_fields_for_stats(item_stats, _create_item_stats_key(statistic), statistic)
        fill_fields_for_stats(global_stats, _create_global_stats_key(statistic), statistic)

    time_str = end.isoformat() + 'Z'
    entries = [{
        'measurement': 'item.%s' % statistic['news_id'],
        'time': time_str,
        'tags': {
            'app': statistic['app_id'],
            'action': statistic['action']
        },
        'fields': statistic['fields'],
    } for statistic in item_stats.itervalues()]
    for statistic in global_stats.itervalues():
        entries.append({
            'measurement': 'global',
            'time': time_str,
            'tags': {
                'app': statistic['app_id'],
                'action': statistic['action']
            },
            'fields': statistic['fields'],
        })

    if entries:
        logging.info('Writing %d entries to influxdb', len(entries))
        client = get_influxdb_client(params=params)
        success = client.write_points(entries, 'u')
        if not success:
            raise Exception('Failed to save to influx db')
