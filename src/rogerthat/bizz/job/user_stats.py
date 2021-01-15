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

import base64
import datetime
import json
import logging
from collections import defaultdict, namedtuple
from contextlib import closing

import cloudstorage
from dateutil.relativedelta import relativedelta
from mapreduce import mapreduce_pipeline, context
from pipeline import pipeline
from pipeline.common import List

from mcfw.properties import azzert
from mcfw.rpc import returns, arguments
from rogerthat.bizz.job.send_unread_messages import CleanupGoogleCloudStorageFiles
from rogerthat.consts import MIGRATION_QUEUE, DEBUG, PIPELINE_BUCKET
from rogerthat.models import Message
from rogerthat.models.properties.messaging import MessageMemberStatusTO
from rogerthat.settings import get_server_settings
from rogerthat.utils import is_flag_set, guid, send_mail
from rogerthat.utils.app import get_app_user_tuple_by_email

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


Stats = namedtuple('Stats', 'total received read acked')
Interval = namedtuple('Interval', 'days months')

@returns(tuple)
@arguments(year=int, week=int, week_count=int)
def get_week_range(year, week, week_count=1):
    min_date = datetime.date(year, 1, 1) + relativedelta(weeks=week)
    min_date -= relativedelta(days=min_date.weekday())
    max_date = min_date + relativedelta(weeks=week_count) - relativedelta(seconds=1)
    return min_date, max_date


@returns(tuple)
@arguments(year=int, month=int, month_count=int)
def get_month_range(year, month, month_count=1):
    min_date = datetime.date(year, month, 1)
    max_date = min_date + relativedelta(months=month_count) - relativedelta(seconds=1)
    return min_date, max_date


@returns(unicode)
@arguments(min_time=long, max_time=long, interval=Interval, skip_messages_sent_by_js_mfr=bool)
def start_job(min_time, max_time, interval=None, skip_messages_sent_by_js_mfr=False):
    key = 'user_stats_%s_%s' % (min_time, max_time)
    key += guid()
    if interval is None:
        interval = Interval(days=1, months=0)
    counter = MessageStatsPipeline(key, min_time, max_time, interval, skip_messages_sent_by_js_mfr)
    task = counter.start(idempotence_key=key, return_task=True)
    task.add(queue_name=MIGRATION_QUEUE)

    redirect_url = "%s/status?root=%s" % (counter.base_path, counter.pipeline_id)
    logging.info("UserMessageStats pipeline url: %s", redirect_url)
    return get_server_settings().baseUrl + redirect_url


@returns(unicode)
@arguments(score=long, max_score=long)
def percent(score, max_score):
    return u'%s%%' % (int(round(100.0 * score / max_score)) if max_score else 0)


@returns(int)
@arguments(timestamp=long, min_time=long, interval=Interval)
def get_interval_index(timestamp, min_time, interval):
    azzert(timestamp >= min_time)
    azzert(interval.months or interval.days)

    date = datetime.datetime.utcfromtimestamp(timestamp)
    min_date = datetime.datetime.utcfromtimestamp(min_time)
    if interval.months:
        months_diff = 12 * (date.year - min_date.year) + date.month - min_date.month
        return months_diff / interval.months
    if interval.days:
        days_diff = (date - min_date).days
        return days_diff / interval.days


@returns(unicode)
@arguments(i=int, min_date=(datetime.datetime, datetime.date), max_date=(datetime.datetime, datetime.date),
           interval=Interval)
def get_period_str(i, min_date, max_date, interval):
    interval = relativedelta(days=interval.days, months=interval.months)
    from_date = min_date + relativedelta(days=interval.days * i, months=interval.months * i)
    to_date = min(max_date, from_date + interval - relativedelta(seconds=1))
    from_date_str = from_date.strftime('%d/%m/%Y')
    to_date_str = to_date.strftime('%d/%m/%Y')
    if from_date_str == to_date_str:
        return from_date_str
    return u'%s - %s' % (from_date_str, to_date_str)


def mapper(message):
    params = context.get().mapreduce_spec.mapper.params
    if params['skip_messages_sent_by_js_mfr'] and is_flag_set(Message.FLAG_SENT_BY_JS_MFR, message.flags):
        return

    min_time, max_time, interval = params['min_time'], params['max_time'], Interval(*params['interval'])

    for i, member in enumerate(message.members):
        if member == message.sender:
            continue

        ms = message.get_member_statuses()[i]

        received = is_flag_set(MessageMemberStatusTO.STATUS_RECEIVED, ms.status) \
            and min_time <= ms.received_timestamp <= max_time
        read = received and is_flag_set(MessageMemberStatusTO.STATUS_READ, ms.status)
        acked = is_flag_set(MessageMemberStatusTO.STATUS_ACKED, ms.status) and min_time <= ms.acked_timestamp <= max_time

        stats = Stats(total=1, received=int(received), read=int(read), acked=int(acked))
        index = get_interval_index(message.creationTimestamp, min_time, interval)
        if DEBUG:
            logging.debug('MAPPER: %s, %s, %s', member.email(), index, stats)
        yield member.email(), (str(index), list(stats))


def _combine(lists):
    '''Eg. [ [4,3,2,1], [4,3,2,1], [4,3,2,1] ] --> [12,9,6,3]'''
    return map(sum, zip(*lists))


def _combine_interval_stats(new_values, prev_stats_dict):
    for v in new_values:
        index, new_stats = eval(v) if isinstance(v, basestring) else v
        prev_stats = prev_stats_dict.get(index)
        if prev_stats:
            prev_stats_dict[index] = _combine([prev_stats, new_stats])
        else:
            prev_stats_dict[index] = new_stats

    return prev_stats_dict


def combiner(key, new_values, previously_combined_values):
    '''
    key: the app_user email
    new_values: newly collected list with tuples: [(index, Stats)]
    previously_combined_values: previously combined list with tuples: [(index, Stats)]
    '''
    if DEBUG:
        logging.debug('COMBINER %s new_values: %s', key, new_values)
        logging.debug('COMBINER %s previously_combined_values: %s', key, previously_combined_values)
    prev_stats = dict(previously_combined_values)  # {index: Stats}
    combined = _combine_interval_stats(new_values, prev_stats)
    if DEBUG:
        logging.debug('COMBINER %s combined: %s', key, combined)
    for i in combined.iteritems():
        yield i


def reducer(key, values):
    '''
    key: the identifier of the team group
    values: collected list with tuples: [(index, Stats)]
    '''
    combined_stats = _combine_interval_stats(values, dict())  # Eg. {"0": [2,1], "3": [9,8]}
    app_user, app_id = get_app_user_tuple_by_email(key)
    json_line = json.dumps(dict(email=app_user.email(),
                                app_id=app_id,
                                stats=combined_stats))
    if DEBUG:
        logging.debug('REDUCER %s: %s', key, json_line)
    yield '%s\n' % json_line


class MessageStatsPipeline(pipeline.Pipeline):
    def run(self, key, min_time, max_time, interval, skip_messages_sent_by_js_mfr):
        params = dict(mapper_spec='rogerthat.bizz.job.user_stats.mapper',
                      mapper_params=dict(bucket_name=PIPELINE_BUCKET,
                                         entity_kind='rogerthat.models.Message',
                                         filters=[('creationTimestamp', '>=', min_time),
                                                  ('creationTimestamp', '<=', max_time)],
                                         min_time=min_time,
                                         max_time=max_time,
                                         interval=interval,
                                         skip_messages_sent_by_js_mfr=skip_messages_sent_by_js_mfr),
                      combiner_spec='rogerthat.bizz.job.user_stats.combiner',
                      reducer_spec='rogerthat.bizz.job.user_stats.reducer',
                      reducer_params=dict(output_writer=dict(bucket_name=PIPELINE_BUCKET),
                                          min_time=min_time,
                                          max_time=max_time,
                                          interval=interval),
                      input_reader_spec='mapreduce.input_readers.DatastoreInputReader',
                      output_writer_spec='mapreduce.output_writers.GoogleCloudStorageConsistentOutputWriter',
                      shards=2 if DEBUG else 10)

        output = yield mapreduce_pipeline.MapreducePipeline(key, **params)

        process_output_pipeline = yield ProcessOutputPipeline(output, min_time, max_time, interval,
                                                              skip_messages_sent_by_js_mfr)
        with pipeline.After(process_output_pipeline):
            yield CleanupGoogleCloudStorageFiles(output)

    def finalized(self):
        if self.was_aborted:
            logging.error("%s was aborted", self, _suppress=False)
            return
        logging.info("%s was finished", self)


class ProcessOutputPipeline(pipeline.Pipeline):

    def run(self, output, min_time, max_time, interval, skip_messages_sent_by_js_mfr):
        results = list()
        for filename in output:
            results.append((yield ProcessFilePipeline(filename, min_time, max_time, interval)))
        yield List(*results)

    def finalized(self):
        if DEBUG:
            logging.debug('ProcessOutputPipeline: self.outputs.default.value = %s', self.outputs.default.value)
        _, min_time, max_time, interval, skip_messages_sent_by_js_mfr = self.args
        interval = Interval(*interval)
        result_length = get_interval_index(max_time, min_time, interval) + 1
        factory = lambda: [Stats(0, 0, 0, 0) for _ in xrange(result_length)]
        # Doing a final combine
        final_stats_per_app = defaultdict(factory)
        for stats_per_app_to_be_added in self.outputs.default.value:
            for app_id, stats_list in stats_per_app_to_be_added.iteritems():
                # Generate the results per app
                for i, stats in enumerate(stats_list):
                    final_stats_per_app[app_id][i] = _combine([final_stats_per_app[app_id][i], stats])

        if DEBUG:
            logging.debug('ProcessOutputPipeline: final_stats_per_app = %s', final_stats_per_app)

        self.send_mail(final_stats_per_app, min_time, max_time, interval, skip_messages_sent_by_js_mfr)

    def send_mail(self, final_stats_per_app, min_time, max_time, interval, skip_messages_sent_by_js_mfr):
        min_date = datetime.datetime.utcfromtimestamp(min_time)
        max_date = datetime.datetime.utcfromtimestamp(max_time)
        min_date_str = min_date.strftime('%d %b %Y')
        max_date_str = max_date.strftime('%d %b %Y')

        with closing(StringIO()) as s:
            s.write('User stats from %s until %s with %s interval'
                    % (min_date_str, max_date_str,
                       ('%s month(s)' % interval.months) if interval.months else ('%s day(s)' % interval.days)))
            if skip_messages_sent_by_js_mfr:
                s.write(' (messages sent by JS_MFR are skipped)')
            s.write('.\nSee attached document for details per app.\n\nSummary:\n')

            # TOTAL STATS PER PERIOD
            result_length = get_interval_index(max_time, min_time, interval) + 1
            total_stats_list = [Stats(0, 0, 0, 0) for _ in xrange(result_length)]
            for stats_list in final_stats_per_app.itervalues():
                for i, stats in enumerate(total_stats_list):
                    total_stats_list[i] = _combine([total_stats_list[i], stats_list[i]])

            if DEBUG:
                logging.warn('ProcessOutputPipeline: total_stats_list = %s', total_stats_list)

            for i, stats in enumerate(total_stats_list):
                stats = Stats(*stats)
                s.write('''
%s
    total: %s
    received: %s/%s (%s of total)
    read: %s/%s (%s of received, %s of total)
    acked: %s/%s (%s of read, %s of received, %s of total)
''' % (get_period_str(i, min_date, max_date, interval), stats.total,
       stats.received, stats.total, percent(stats.received, stats.total),
       stats.read, stats.received, percent(stats.read, stats.received), percent(stats.read, stats.total),
       stats.acked, stats.read, percent(stats.acked, stats.read), percent(stats.acked, stats.received), percent(stats.acked, stats.total)))

            body = s.getvalue()

        server_settings = get_server_settings()
        mail_receivers = server_settings.supportWorkers
        subject = u'Rogerthat user stats: %s - %s' % (min_date_str, max_date_str)
        attachments = [self.create_xls_attachment(final_stats_per_app, total_stats_list, min_date, max_date, interval)]
        send_mail(server_settings.dashboardEmail, mail_receivers, subject, body, attachments=attachments)

    def create_xls_attachment(self, final_stats_per_app, total_stats_list, min_date, max_date, interval):
        import xlwt
        book = xlwt.Workbook(encoding='utf-8')

        for app_id, stats_list in [('Total', total_stats_list)] + sorted(final_stats_per_app.iteritems()):
            sheet = book.add_sheet(app_id)
            for col, label in enumerate(('period', 'total', 'received', 'read', 'acked',
                                         'received/total', 'read/received', 'read/total',
                                         'acked/read', 'acked/received', 'acked/total')):
                sheet.write(0, col, label)
            for i, stats in enumerate(stats_list):
                stats = Stats(*stats)
                for col, text in enumerate((get_period_str(i, min_date, max_date, interval),
                                           stats.total,
                                           stats.received,
                                           stats.read,
                                           stats.acked,
                                           percent(stats.received, stats.total),
                                           percent(stats.read, stats.received),
                                           percent(stats.read, stats.total),
                                           percent(stats.acked, stats.read),
                                           percent(stats.acked, stats.received),
                                           percent(stats.acked, stats.total))):
                    sheet.write(i + 1, col, text)

        with closing(StringIO()) as output:
            book.save(output)
            output.seek(0)
            return ('%s - %s.xls' % (min_date.strftime('%d %b %Y'), max_date.strftime('%d %b %Y')),
                    base64.b64encode(output.getvalue()))


class ProcessFilePipeline(pipeline.Pipeline):
    def run(self, filename, min_time, max_time, interval):
        interval = Interval(*interval)
        result_length = get_interval_index(max_time, min_time, interval) + 1
        factory = lambda: [Stats(0, 0, 0, 0) for _ in xrange(result_length)]
        # amount of unique users that (have received/read/acked) a message
        stats_per_app = defaultdict(factory)  # {app_id: [ [2,1], [0,0], [0,0], [9,8], [0,0] ]}
        with cloudstorage.open(filename, "r") as f:
            for json_line in f:
                d = json.loads(json_line)
                # Flatten the stats dict into a list
                # Example with result_length=5: {"0": [2,1], "3": [9,8]} --> [[2,1], [0,0], [0,0], [9,8], [0,0]]
                stats_list = factory()
                for index_str, stats in d['stats'].iteritems():
                    stats_list[int(index_str)] = Stats(*stats)

                # Generate the results per app
                for i, stats in enumerate(stats_list):
                    stats_per_app[d['app_id']][i] = _combine([stats_per_app[d['app_id']][i], map(bool, stats)])
        logging.debug('ProcessFilePipeline: %s', stats_per_app)
        return stats_per_app
