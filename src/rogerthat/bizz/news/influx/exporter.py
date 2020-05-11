# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
# NOTICE: THIS FILE HAS BEEN MODIFIED BY GREEN VALLEY BELGIUM NV IN ACCORDANCE WITH THE APACHE LICENSE VERSION 2.0
# Copyright 2018 GIG Technology NV
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
# @@license_version:1.6@@

from datetime import datetime
import hashlib
import logging

from dateutil.relativedelta import relativedelta
from google.appengine.ext import deferred, ndb

from rogerthat.bizz.news.influx import get_influxdb_client
from rogerthat.consts import NEWS_STATS_QUEUE
from rogerthat.models.news import NewsItemStatisticsExporter, \
    NewsItemActionStatistics
from rogerthat.utils.app import get_app_id_from_app_user
from rogerthat.utils.cloud_tasks import create_task, schedule_tasks


@ndb.transactional()
def run():
    key = NewsItemStatisticsExporter.create_key('action')
    settings = key.get()
    if not settings:
        logging.info('NewsItemStatisticsExporter not set for type "action"')
        return

    start = settings.exported_until
    end_ = datetime.utcnow()
    end = datetime(year=end_.year, month=end_.month, day=end_.day, hour=end_.hour, minute=end_.minute)
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


def _run(start, end, params=None):

    def create_item_key(s):
        app_id = get_app_id_from_app_user(s.app_user)
        key = u'%s_%s_%s_%s_%s' % (app_id, s.news_id, s.action, s.gender, s.age)
        return hashlib.sha256(key).hexdigest().upper()

    qry = NewsItemActionStatistics.list_between(start, end)
    item_stats = dict()
    for s in qry:
        key = create_item_key(s)
        if key not in item_stats:
            item_stats[key] = dict(app_id=get_app_id_from_app_user(s.app_user),
                                   news_id=s.news_id,
                                   action=s.action,
                                   gender=s.gender,
                                   age=s.age,
                                   amount=0)

        item_stats[key]['amount'] += 1

    entries = []
    influx_time = start
    for k in sorted(item_stats.iterkeys()):
        s = item_stats[k]
        influx_time += relativedelta(microseconds=2)  # influx has duplicate data when using 1 micro
        time_str = influx_time.isoformat() + 'Z'

        entries.append({
            'measurement': 'item_%s' % s['news_id'],
            'time': time_str,
            'tags': {
                'app_id': s['app_id'],
                'action': s['action'],
            },
            'fields': {
                'f_app_id': s['app_id'],
                'f_action': s['action'],
                'age': s['age'],
                'gender': s['gender'],
                'amount': s['amount'],
            }
        })

        entries.append({
            'measurement': 'global',
            'time': time_str,
            'tags': {
                'app_id': s['app_id'],
                'action': s['action'],
            },
            'fields': {
                'f_app_id': s['app_id'],
                'f_action': s['action'],
                'id': s['news_id'],
                'age': s['age'],
                'gender': s['gender'],
                'amount': s['amount'],
            }
        })

    logging.info('news_exporter -> %s items', len(entries))
    if entries:
        client = get_influxdb_client(params=params)
        success = client.write_points(entries, 'u')
        if not success:
            raise Exception('Failed to save to influx db')
