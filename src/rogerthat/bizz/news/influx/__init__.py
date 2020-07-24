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

from influxdb import InfluxDBClient
from influxdb.resultset import ResultSet
from typing import List

from rogerthat.consts import DEBUG, DAY
from rogerthat.models.news import NewsItemAction, NewsItem
from rogerthat.models.properties.news import NewsItemStatistics
from rogerthat.settings import get_server_settings
from rogerthat.to.news import NewsItemBasicStatisticsTO, NewsItemTimeStatisticsTO, NewsItemBasicStatisticTO, \
    NewsItemTimeValueTO
from rogerthat.utils import now


def get_influxdb_datetime(time_str):
    # type: (str) -> datetime
    if len(time_str) == 20:
        return datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ")
    else:
        return datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S.%fZ")


def get_influxdb_client(database='news', params=None):
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


def get_age_field_key(age):
    return 'age-%s' % age.replace(' ', '')


def get_news_item_time_statistics(news_item):
    # type: (NewsItem) -> NewsItemTimeStatisticsTO
    qry_start_time = time.time()
    start_time = news_item.published_timestamp
    start_time_plus_one_month = start_time + DAY * 30
    end_time = min(start_time_plus_one_month, now())
    qry = 'SELECT sum(total) as value ' \
          'FROM "item.%(news_id)s" ' \
          'WHERE time >= %(start_time)ss AND time <= %(end_time)ss ' \
          'GROUP BY "action", time(1h) fill(0);' % {
              'news_id': news_item.id,
              'start_time': start_time,
              'end_time': end_time,
          }

    try:
        result_set = get_influxdb_client().query(qry)
    except Exception as e:
        if DEBUG:
            logging.error('Error while fetching statistics. Returning empty result', exc_info=True)
            return NewsItemTimeStatisticsTO(id=news_item.id, reached=[], action=[])
        raise e
    qry_end_time = time.time()
    logging.debug('Time statistics queries took %ss', qry_end_time - qry_start_time)
    reached = [NewsItemTimeValueTO(time=point['time'], value=point['value'])
               for point in result_set.get_points(tags={'action': NewsItemAction.REACHED})]
    action = [NewsItemTimeValueTO(time=point['time'], value=point['value'])
              for point in result_set.get_points(tags={'action': NewsItemAction.ACTION})]
    stats = NewsItemTimeStatisticsTO(id=news_item.id, reached=reached, action=action)
    logging.debug('Transforming resultset took %ss', time.time() - qry_end_time)
    return stats


def _get_first_point(result_set, tags):
    # type: (ResultSet, dict) -> dict
    points = list(result_set.get_points(tags=tags))
    return points[0] if points else None


def get_basic_news_item_statistics(news_items):
    # type: (List[NewsItem]) -> List[NewsItemBasicStatisticsTO]
    stats_per_news_item = {}
    statements = []
    qry = ''
    qry_start_time = time.time()
    for news_item in news_items:
        fields_to_select = ['total'] + NewsItemStatistics.get_gender_labels() + [get_age_field_key(l) for l in
                                                                                 NewsItemStatistics.get_age_labels()]
        fields = ['sum("%s") as "%s"' % (field, field) for field in fields_to_select]
        qry += 'SELECT %(fields)s' \
               'FROM "item.%(news_id)s" ' \
               'WHERE ("action" = \'%(reached)s\' OR "action" = \'%(action)s\') ' \
               'GROUP BY "action";' % {
                   'fields': ', '.join(fields),
                   'news_id': news_item.id,
                   'reached': NewsItemAction.REACHED,
                   'action': NewsItemAction.ACTION
               }
        statements.append(news_item)
    if qry:
        try:
            result_sets = get_influxdb_client().query(qry)
        except Exception as e:
            if DEBUG:
                logging.error('Error while fetching statistics. Returning empty result', exc_info=True)
                zero_stats = NewsItemBasicStatisticTO(total=0, gender=[], age=[])
                return [NewsItemBasicStatisticsTO(id=news_item.id, reached=zero_stats, action=zero_stats)
                        for news_item in news_items]
            raise e
        qry_end_time = time.time()
        logging.debug('basic: %d statistics queries took %ss', len(statements), qry_end_time - qry_start_time)
        # In case there is only one result set the above method returns the resultset instead of a list
        if not isinstance(result_sets, list):
            result_sets = [result_sets]
        for statement_id, news_item in enumerate(statements):
            for result_set in result_sets:  # type: ResultSet
                if result_set.raw['statement_id'] == statement_id:
                    reached_stats = _get_first_point(result_set, {'action': NewsItemAction.REACHED})
                    action_stats = _get_first_point(result_set, {'action': NewsItemAction.ACTION})
                    stats_per_news_item[news_item.id] = NewsItemBasicStatisticsTO(
                        id=news_item.id,
                        reached=NewsItemBasicStatisticTO.from_point(reached_stats),
                        action=NewsItemBasicStatisticTO.from_point(action_stats),
                    )
        logging.debug('basic: Transforming resultset took %ss', time.time() - qry_end_time)
    return [stats_per_news_item[news_item.id] for news_item in news_items]
