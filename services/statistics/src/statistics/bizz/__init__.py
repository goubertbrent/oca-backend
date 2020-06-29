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

import datetime
import json
import logging

from dateutil.relativedelta import relativedelta
from google.appengine.api import users
from google.appengine.ext import deferred, ndb

from mcfw.properties import azzert
from statistics.bizz.exporter import export_day
from statistics.models.stats import NdbServiceLog, StatsExportDaily, \
    StatsExportDailyData, StatsExport, StatsExportDailyAppStats
from utils.cloud_tasks import create_task, schedule_tasks


MIGRATION_QUEUE = "migration-queue"

def do_parse_all():
    max_date = datetime.date.today() - relativedelta(days=1)
    for m in StatsExport.query():
        deferred.defer(_parse_day, m.service_user, m.start_date, max_date, _queue=MIGRATION_QUEUE)
        m.start_date = max_date
        m.put()


def _parse_day(service_user, start_day, max_day, cursor=None):
    end_day = start_day + relativedelta(days=1)
    if end_day > max_day:
        return
    logging.debug("start_day: %s", start_day)
        
    start_milliseconds = get_milliseconds_from_datetime(start_day)
    end_milliseconds = get_milliseconds_from_datetime(end_day)

    qry =  NdbServiceLog.query().filter(NdbServiceLog.user == service_user)
    qry = qry.filter(NdbServiceLog.timestamp > start_milliseconds)
    qry = qry.filter(NdbServiceLog.timestamp <= end_milliseconds)
    
    default_app_id = StatsExport.create_key(service_user).get().default_app_id
    models, new_cursor, has_more = qry.fetch_page(500, start_cursor=cursor)
    tags_dict = {}
    for m in models:
        if m.type != NdbServiceLog.TYPE_CALLBACK:
            continue
        if m.status != NdbServiceLog.STATUS_SUCCESS:
            continue
        if m.function in (None,
                          'messaging.chat_deleted',
                          'messaging.form_update',
                          'messaging.new_chat_message',
                          'messaging.update',
                          'friend.update',
                          'app.installation_progress',
                          'test.test'):
            continue
        
        data = json.loads(m.request)
        service_identity = data['params'].get('service_identity')
        if not service_identity:
            service_identity = u'+default+'
            
        user_details = data['params'].get('user_details')
        app_id = default_app_id
        if user_details:
            user_app_id = user_details[0].get('app_id')
            if user_app_id:
                app_id = user_app_id
        
        tags = get_tags(data)
        if not tags:
            logging.warn("Don't know how to parse function '%s'", m.function)
            logging.debug(m)
            continue
        
        for tag in tags:
            if service_identity not in tags_dict:
                tags_dict[service_identity] = {}
            if app_id not in tags_dict[service_identity]:
                tags_dict[service_identity][app_id] = {}
            if tag not in tags_dict[service_identity][app_id]:
                tags_dict[service_identity][app_id][tag] = 0
            tags_dict[service_identity][app_id][tag] += 1
    
    to_put = []
    for service_identity in tags_dict:
        key = StatsExportDaily.create_key(start_day.year, start_day.month, start_day.day, service_user, service_identity)
        if cursor:
            m = key.get() or StatsExportDaily(key=key, date=start_day, app_stats=[])
        else:
            m = StatsExportDaily(key=key, date=start_day, app_stats=[])
        
        for app_id in tags_dict[service_identity]:
            app_stats = m.get_app_stats(app_id)
            if not app_stats:
                app_stats = StatsExportDailyAppStats(app_id=app_id, data=[])
                m.app_stats.append(app_stats)

            for tag in tags_dict[service_identity][app_id]:
                tag_data = app_stats.get_tag_data(tag)
                if not tag_data:
                    tag_data = StatsExportDailyData(tag=tag, count=0)
                    app_stats.data.append(tag_data)

                tag_data.count += tags_dict[service_identity][app_id][tag]
        to_put.append(m)

    ndb.put_multi(to_put)
        
    if has_more:
        deferred.defer(_parse_day, service_user, start_day, max_day, new_cursor, _queue=MIGRATION_QUEUE, _countdown=1)
    else:
        next_start_day = start_day + relativedelta(days=1)
        deferred.defer(_parse_day, service_user, next_start_day, max_day, _queue=MIGRATION_QUEUE, _countdown=1)
        deferred.defer(export_day, service_user, start_day, _countdown=3)
        
    
def get_tags(data):
    method = data['method']
    tags = [method]
    if method in ('friend.register',
                  'friend.register_result',
                  'friend.invited',
                  'friend.invite_result',
                  'friend.broke_up'):
        pass
    elif method in ('system.api_call',):
        tags.append('%s#%s' % (method,
                               data['params']['tag']))
        tags.append('%s#%s#%s' % (method,
                                  data['params']['tag'],
                                  data['params']['method']))

    elif method in ('messaging.poke',):
        tags.append('%s#%s' % (method,
                               data['params']['tag']))
    
    elif method in ('messaging.flow_member_result',):
        tags.append('%s#%s' % (method,
                               data['params']['tag']))
        
    elif method in ('forms.submitted',):
        tags.append('%s#%s' % (method,
                               data['params']['form']['id']))
    else:
        return []
    return tags


def get_milliseconds_from_datetime(datetime_):
    if isinstance(datetime_, datetime.datetime):
        epoch = datetime.datetime.utcfromtimestamp(0)
    elif isinstance(datetime_, datetime.date):
        epoch = datetime.date.fromtimestamp(0)
    else:
        azzert(False, "Provided value should be a datetime.datetime or datetime.date instance")
    delta = datetime_ - epoch
    return ((delta.days * 86400 + delta.seconds)*10**6 + delta.microseconds) / 10**3
