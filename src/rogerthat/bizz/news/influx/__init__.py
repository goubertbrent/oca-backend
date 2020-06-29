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
import time
from datetime import datetime

from dateutil.relativedelta import relativedelta
from influxdb import InfluxDBClient
from influxdb.resultset import ResultSet

from rogerthat.consts import DEBUG
from rogerthat.models.news import NewsItemActionStatistics, NewsItemAction
from rogerthat.models.properties.news import NewsItemStatistics
from rogerthat.rpc import users
from rogerthat.settings import get_server_settings
from rogerthat.to.news import NewsItemStatisticsTO, NewsItemAppStatisticsTO


def get_influxdb_datetime(time_str):
    # type: (str) -> datetime
    if len(time_str) == 20:
        return datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ")
    else:
        return datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S.%fZ")


def get_influxdb_client(database=None, params=None):
    ss = get_server_settings()
    if not ss.news_statistics_influxdb_host:
        return None

    if params:
        return InfluxDBClient(host=params['host'],
                              port=params['port'],
                              ssl=params['ssl'],
                              verify_ssl=params['verify_ssl'],
                              database=params['database'],
                              username=params['username'],
                              password=params['password'])

    return InfluxDBClient(host=ss.news_statistics_influxdb_host,
                          port=ss.news_statistics_influxdb_port,
                          ssl=not DEBUG,
                          verify_ssl=not DEBUG,
                          database=database or ss.news_statistics_influxdb_database,
                          username=ss.news_statistics_influxdb_username,
                          password=ss.news_statistics_influxdb_password)


def get_news_reach(news_id):
    qry = 'select sum("amount") from "item_%s" where "action" = \'reached\';' % news_id
    result_set = get_influxdb_client().query(qry)
    reach = 0
    if result_set:
        for p in result_set.get_points('item_%s' % news_id):
            reach += p['sum']
    return reach


def get_news_items_statistics(news_items, include_details=False):
    stats_per_news_item = {}
    statements = []
    qry = ''
    qry_start_time = time.time()

    # Keys only queries since we only need the emails here
    stats_queries = {
        item.id: NewsItemActionStatistics.list_by_action(item.id, NewsItemAction.ROGERED)
            .fetch_async(keys_only=True)
        for item in news_items
    }

    for news_item in news_items:
        qry += 'select app_id, action, age, gender, amount from "item_%s";' % news_item.id
        statements.append(news_item)

    if qry:
        result_sets = get_influxdb_client().query(qry)
        qry_end_time = time.time()
        logging.debug('%d statistics queries took %ss', len(statements), qry_end_time - qry_start_time)
        # In case there is only one result set the above method returns the resultset instead of a list
        if not isinstance(result_sets, list):
            result_sets = [result_sets]
        for statement_id, news_item in enumerate(statements):
            for result_set in result_sets:
                if result_set.raw['statement_id'] == statement_id:
                    rogered_users = [users.User(stats_key.parent().id().decode('utf8')).email()
                                     for stats_key in stats_queries[news_item.id].get_result()]
                    stats_per_news_item[news_item.id] = transform_news_statistics_resulset(result_set, news_item.id,
                                                                                           news_item.timestamp,
                                                                                           rogered_users,
                                                                                           include_details)
        logging.debug('Waiting for query and transforming resultset took %ss', time.time() - qry_end_time)

    return stats_per_news_item


def transform_news_statistics_resulset(result, news_id, timestamp, users_that_rogered, include_details):
    # type: (ResultSet, long ,long, list[unicode], bool) -> NewsItemStatisticsTO
    creation_date = datetime.utcfromtimestamp(timestamp)
    action_types = [NewsItemAction.REACHED, NewsItemAction.ROGERED, NewsItemAction.ACTION, NewsItemAction.FOLLOWED]

    def fill_for_app_id(d, app_id):
        d[app_id] = {}
        for action in action_types:
            d[app_id][action] = {
                'age': NewsItemStatistics.default_age_dict(),
                'gender': NewsItemStatistics.default_gender_dict(),
                'time': [],
                'total': 0
            }

    s_dict = {}

    for p in result.get_points('item_%s' % news_id):
        app_id, ts, action, amount = p['app_id'], p['time'], p['action'], p['amount']
        if action not in action_types:
            continue
        if app_id not in s_dict:
            fill_for_app_id(s_dict, app_id)

        action_date = get_influxdb_datetime(ts)
        hour_index = NewsItemStatistics.get_time_index(creation_date, action_date)
        if hour_index < 0:
            logging.debug('hour_index:%s news_id:%s creation_date:%s > action_date:%s', hour_index, news_id, creation_date, action_date)
        current_time_size = len(s_dict[app_id][action_types[0]]['time'])
        diff = hour_index - current_time_size + 1
        for _ in xrange(diff):
            for act in action_types:
                s_dict[app_id][act]['time'].append(0)
        action_stats = s_dict[app_id][action]
        age_label = p['age']
        if age_label in action_stats['age']:
            action_stats['age'][age_label] += amount
        else:
            logging.warn('Unexpected age label %s for news item %s, ignoring', age_label, news_id)
        action_stats['gender'][p['gender']] += amount
        action_stats['time'][hour_index] += amount

    result = NewsItemStatisticsTO(news_id, users_that_rogered=users_that_rogered)
    for app_id, s in s_dict.iteritems():
        if include_details:
            statistics_in_app = NewsItemAppStatisticsTO(
                app_id=app_id,
                reached=create_detail_statistics(s[NewsItemAction.REACHED], creation_date),
                rogered=create_detail_statistics(s[NewsItemAction.ROGERED], creation_date),
                action=create_detail_statistics(s[NewsItemAction.ACTION], creation_date),
                followed=create_detail_statistics(s[NewsItemAction.FOLLOWED], creation_date)
            )
            result.details.append(statistics_in_app)
            result.total_action += statistics_in_app.action['total']
            result.total_reached += statistics_in_app.reached['total']
            result.total_followed += statistics_in_app.followed['total']
        else:
            reached, followed, action = get_simple_stats(s)
            result.total_reached += reached
            result.total_followed += followed
            result.total_action += action
    return result


def create_detail_statistics(stats_for_action, creation_date):
    # type: (dict, datetime) -> dict
    time_list = []
    age_list = []
    gender_list = []
    for i, _ in enumerate(NewsItemStatistics.default_age_stats()):
        start_age = i * 5
        end_age = start_age + 5
        age_label = u'%s - %s' % (start_age, end_age)
        age_list.append({'key': age_label, 'value': stats_for_action['age'].get(age_label, 0)})
    for i, _ in enumerate(NewsItemStatistics.default_gender_stats()):
        gender_label = NewsItemStatistics.gender_translation_key(i)
        gender_list.append({'key': gender_label, 'value': stats_for_action['gender'].get(gender_label, 0)})
    result = {
        'age': age_list,
        'gender': gender_list,
        'time': time_list,
        'total': sum(stats_for_action['gender'].values())
    }
    for hours_from_creation, time_value in enumerate(stats_for_action['time']):
        if not time_value:
            continue
        dt = creation_date + relativedelta(hours=hours_from_creation)
        time_list.append({'timestamp': long(time.mktime(dt.utctimetuple())), 'amount': time_value})
    return result


def get_simple_stats(s):
    action_count = 0
    reached = 0
    followed = 0
    for action in [NewsItemAction.REACHED, NewsItemAction.ACTION, NewsItemAction.FOLLOWED]:
        stats_for_action = s[action]
        amount = sum(stats_for_action['gender'].values())
        if action == NewsItemAction.REACHED:
            reached += amount
        elif action == NewsItemAction.ACTION:
            action_count += amount
        elif action == NewsItemAction.FOLLOWED:
            followed += amount
    return reached, followed, action_count
