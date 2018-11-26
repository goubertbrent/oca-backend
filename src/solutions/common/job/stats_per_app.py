# -*- coding: utf-8 -*-
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
# @@license_version:1.4@@
import json
import logging
import time
from StringIO import StringIO
from datetime import date
from types import GeneratorType

from google.appengine.api import app_identity
from google.appengine.ext import db

import cloudstorage
import xlwt
from dateutil.relativedelta import relativedelta
from mapreduce import mapreduce_pipeline
from mcfw.properties import long_property, unicode_property
from pipeline import pipeline
from pipeline.common import List
from rogerthat.bizz.app import get_app
from rogerthat.bizz.gcs import upload_to_gcs
from rogerthat.bizz.news.influx import get_influxdb_client
from rogerthat.bizz.service.statistics import get_statisticsTO
from rogerthat.consts import STATS_QUEUE, DEBUG
from rogerthat.dal.profile import get_service_profiles, get_service_profile
from rogerthat.dal.service import get_service_identity
from rogerthat.models import ServiceIdentityStatistic, ServiceIdentity, App, ServiceProfile
from rogerthat.models.news import NewsItem
from rogerthat.settings import get_server_settings
from rogerthat.to import TO
from rogerthat.utils import guid, now
from rogerthat.utils.service import remove_slash_default, add_slash_default, get_service_user_from_service_identity_user


def _should_include(day, min_date):
    # type: (date, date) -> bool
    return date(day=day.day, month=day.month, year=day.year) >= min_date


class Stats(TO):
    app_id = unicode_property('app_id')
    app_name = unicode_property('app_name')
    user_count = long_property('user_count')
    button_presses = long_property('button_presses')
    community_services_button_presses = long_property('community_services_button_presses')
    service_count = long_property('service_count')

    def __init__(self):
        self.user_count = 0
        self.button_presses = 0
        self.community_services_button_presses = 0
        self.service_count = 0


def generate(app_id):
    min_date = date.today() - relativedelta(days=30)
    app = get_app(app_id)
    if app.type != App.APP_TYPE_CITY_APP and not app_id.startswith('be-'):
        return ''
    service_identities = [profile for profile in ServiceIdentity.all().filter('appIds', app_id) if
                          profile.defaultAppId == app_id]  # type: list[ServiceIdentity]
    service_profiles = get_service_profiles([profile.service_user for profile in service_identities])

    result = Stats()
    result.app_id = app_id
    result.app_name = app.name
    result.service_count = len(service_identities)
    main_service_emails = [remove_slash_default(profile.user).email() for profile in service_profiles if
                           profile.organizationType == ServiceProfile.ORGANIZATION_TYPE_CITY]
    for profile in service_profiles:
        stats_to = get_statisticsTO(db.get(ServiceIdentityStatistic.create_key(profile.user)))
        button_presses = sum([sum(day.count for day in press.data if _should_include(day, min_date)) for
                              press in stats_to.menu_item_press])
        result.button_presses += button_presses
        if profile.user.email() in main_service_emails:
            # Take maximum
            if stats_to.number_of_users > result.user_count:
                result.user_count = stats_to.number_of_users
            result.community_services_button_presses += button_presses
    return json.dumps(result.to_dict())


def get_news_reads(start_timestamp):
    news_items = [ni for ni in NewsItem.all().filter("timestamp >", start_timestamp)]

    statements = []
    qry = ''

    for news_item in news_items:
        qry += 'select app_id, amount from "item_%s" WHERE action = \'%s\';' % (news_item.id, u'reached')
        statements.append(news_item)

    d = {}
    if qry:
        result_sets = get_influxdb_client(database=u'news_statistics_v2').query(qry)
        if not isinstance(result_sets, list):
            result_sets = [result_sets]
        for statement_id, news_item in enumerate(statements):
            t = 'normal'
            sp = get_service_profile(get_service_user_from_service_identity_user(news_item.sender))
            if not sp:
                continue
            if sp.organizationType == ServiceProfile.ORGANIZATION_TYPE_CITY:
                t = 'city'

            si = get_service_identity(news_item.sender)
            default_app_id = si.app_id
            if default_app_id not in d:
                d[default_app_id] = {'normal': {'count': 0, 'reach': 0}, 'city': {'count': 0, 'reach': 0}}
            d[default_app_id][t]['count'] += 1

            for result_set in result_sets:
                if result_set.raw['statement_id'] == statement_id:
                    for p in result_set.get_points('item_%s' % news_item.id):
                        app_id, amount = p['app_id'], p['amount']
                        if app_id != default_app_id:
                            continue
                        d[default_app_id][t]['reach'] += amount

    return d


def get_loyalty_actions(start_timestamp):
    from solutions.common.models.loyalty import SolutionLoyaltyVisitRevenueDiscount, SolutionLoyaltyVisitLottery, \
        SolutionLoyaltyVisitStamps

    d = {}
    _loyalty_stats(d, SolutionLoyaltyVisitRevenueDiscount.all().filter('redeemed_timestamp >=', start_timestamp))
    _loyalty_stats(d, SolutionLoyaltyVisitLottery.all().filter('redeemed_timestamp >=', start_timestamp))
    _loyalty_stats(d, SolutionLoyaltyVisitStamps.all().filter('redeemed_timestamp >=', start_timestamp))

    return d


def _loyalty_stats(d, qry):
    for m in qry:
        sp = get_service_profile(m.service_user)
        if not sp:
            continue
        t = 'normal'
        if sp.organizationType == ServiceProfile.ORGANIZATION_TYPE_CITY:
            t = 'city'
        si = get_service_identity(add_slash_default(m.service_identity_user))
        default_app_id = si.app_id
        if default_app_id not in d:
            d[default_app_id] = {'normal': 0, 'city': 0}
        d[default_app_id][t] += 1

    return d


def create_excel(data, news_stats, loyalty_stats):
    # type: (list[Stats], dict[str, dict], dict[str, dict]) -> None
    bold_style = xlwt.XFStyle()
    bold_style.font.bold = True
    book = xlwt.Workbook(encoding='utf-8')
    sheet = book.add_sheet('Stats')
    column_count = 11
    row = 0
    col_app, col_users, col_services, col_button_presses_all, col_button_presses, col_news_city_count, col_news_count, \
    col_news_reach, col_news_city_reach, col_loyalty_city_count, col_loyalty_count = range(column_count)
    sheet.write(row, col_app, 'App', bold_style)
    sheet.write(row, col_users, 'Amount of users', bold_style)
    sheet.write(row, col_services, 'Amount of services', bold_style)
    sheet.write(row, col_button_presses_all, 'Button presses (all)', bold_style)
    sheet.write(row, col_button_presses, 'Button presses (main service)', bold_style)
    sheet.write(row, col_news_city_count, 'Sent news (city)', bold_style)
    sheet.write(row, col_news_count, 'Sent news (rest)', bold_style)
    sheet.write(row, col_news_city_reach, 'news reach (city)', bold_style)
    sheet.write(row, col_news_reach, 'news reach(rest)', bold_style)
    sheet.write(row, col_loyalty_city_count, 'Loyalty (city)', bold_style)
    sheet.write(row, col_loyalty_count, 'Loyalty (rest)', bold_style)
    for i in xrange(column_count):
        sheet.col(i).width = 5000
    for result in data:
        row += 1
        sheet.write(row, col_app, result.app_name)
        sheet.write(row, col_users, result.user_count)
        sheet.write(row, col_services, result.service_count)
        sheet.write(row, col_button_presses_all, result.button_presses)
        sheet.write(row, col_button_presses, result.community_services_button_presses)
        sheet.write(row, col_news_city_count, news_stats.get(result.app_id, {}).get('city', {}).get('count', 0))
        sheet.write(row, col_news_count, news_stats.get(result.app_id, {}).get('normal', {}).get('count', 0))
        sheet.write(row, col_news_city_reach, news_stats.get(result.app_id, {}).get('city', {}).get('reach', 0))
        sheet.write(row, col_news_reach, news_stats.get(result.app_id, {}).get('normal', {}).get('reach', 0))
        sheet.write(row, col_loyalty_city_count, loyalty_stats.get(result.app_id, {}).get('city', 0))
        sheet.write(row, col_loyalty_count, loyalty_stats.get(result.app_id, {}).get('normal', 0))
    excel = StringIO()
    book.save(excel)
    result = excel.getvalue()
    file_name = '/%s.appspot.com/stats/app_stats-%s.xlsx' % (app_identity.get_application_id(), now())
    upload_to_gcs(result, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', file_name)


def start_job():
    now_ = date.today()
    min_date = now_ - relativedelta(days=30)
    key = 'app_usage_stats_%s_%s' % (now_.strftime('%Y-%m-%d'), guid())
    bucket_name = 'oca-mr'
    counter = AppUsageStats(bucket_name, key, time.mktime(min_date.timetuple()))
    task = counter.start(idempotence_key=key, return_task=True)
    task.add(queue_name=STATS_QUEUE)

    redirect_url = '%s/status?root=%s' % (counter.base_path, counter.pipeline_id)
    logging.info('AppUsageStats pipeline url: %s', redirect_url)
    return get_server_settings().baseUrl + redirect_url


def mapper(app):
    # type: (App) -> GeneratorType
    yield app.app_id, generate(app.app_id)


def reducer(app_id, values):
    # type: (str, str) -> GeneratorType
    # Values is a list of json encoded data
    if DEBUG:
        logging.info('reducer values: %s', values)
    assert len(values) == 1
    yield '%s\n' % values[0]


class AppUsageStats(pipeline.Pipeline):
    def run(self, bucket_name, key, min_date):
        # type: (str, str, long) -> GeneratorType
        # TODO: Do the query on ServiceIdentity instead of App to improve speed.
        params = {
            'mapper_spec': 'solutions.common.job.stats_per_app.mapper',
            'mapper_params': {
                'bucket_name': bucket_name,
                'entity_kind': 'rogerthat.models.App',
                'filters': []
            },
            'reducer_spec': 'solutions.common.job.stats_per_app.reducer',
            'reducer_params': {
                'output_writer': {
                    'bucket_name': bucket_name
                }
            },
            'input_reader_spec': 'mapreduce.input_readers.DatastoreInputReader',
            'output_writer_spec': 'mapreduce.output_writers.GoogleCloudStorageConsistentOutputWriter',
            'shards': 2 if DEBUG else 10
        }

        output = yield mapreduce_pipeline.MapreducePipeline(key, **params)

        process_output_pipeline = yield ProcessOutputPipeline(output, min_date)
        with pipeline.After(process_output_pipeline):
            yield CleanupGoogleCloudStorageFiles(output)

    def finalized(self):
        if self.was_aborted:
            logging.error('%s was aborted', self, _suppress=False)
            return
        logging.info('%s was finished', self)


class ProcessOutputPipeline(pipeline.Pipeline):

    def run(self, output, min_date):
        results = []
        for filename in output:
            results.append((yield ProcessFilePipeline(filename)))
        yield List(*results)

    def finalized(self):
        if DEBUG:
            logging.debug('ProcessOutputPipeline: self.outputs.default.value = %s', self.outputs.default.value)
        _, timestamp = self.args
        outputs = self.outputs.default.value  # type: list[dict]
        logging.info('OUTPUT: %s', [output for output in outputs])
        result = []
        for output in outputs:
            result.extend([Stats.from_dict(stats) for stats in output])

        min_date = time.mktime((date.today() - relativedelta(days=30)).timetuple())
        logging.debug('Getting stats starting from %s', min_date)
        news_stats = get_news_reads(min_date)
        loyalty_stats = get_loyalty_actions(min_date)
        create_excel(result, news_stats, loyalty_stats)


class ProcessFilePipeline(pipeline.Pipeline):

    def run(self, filename):
        with cloudstorage.open(filename, "r") as f:
            stats = [json.loads(line) for line in f if line.strip()]

        if DEBUG:
            logging.debug('ProcessFilePipeline: %s', stats)
        return stats


class CleanupGoogleCloudStorageFiles(pipeline.Pipeline):
    def run(self, output):
        for filename in output:
            cloudstorage.delete(filename)
