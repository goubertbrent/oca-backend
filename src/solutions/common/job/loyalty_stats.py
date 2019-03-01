# -*- coding: utf-8 -*-
# Copyright 2018 Mobicage NV
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

import datetime
import logging
import time

import cloudstorage
from mapreduce import mapreduce_pipeline
from pipeline import pipeline
from pipeline.common import List

from rogerthat.bizz.statistics import get_country_code_from_app_id
from rogerthat.consts import STATS_QUEUE, DEBUG, PIPELINE_BUCKET
from rogerthat.models import App
from rogerthat.settings import get_server_settings
from rogerthat.utils import guid, log_offload
from rogerthat.utils.app import get_app_id_from_app_user


def start_job():
    current_date = datetime.datetime.now()
    key = 'loyalty_stats_%s_%s' % (current_date.strftime('%Y-%m-%d'), guid())
    counter = LoyaltyCardsPipeline(PIPELINE_BUCKET, key, time.mktime(current_date.timetuple()))
    task = counter.start(idempotence_key=key, return_task=True)
    task.add(queue_name=STATS_QUEUE)

    redirect_url = '%s/status?root=%s' % (counter.base_path, counter.pipeline_id)
    logging.info('LoyaltyCardsPipeline pipeline url: %s', redirect_url)
    return get_server_settings().baseUrl + redirect_url


def mapper(loyalty_card):
    # type: (CustomLoyaltyCard) -> GeneratorType

    app_id = get_app_id_from_app_user(loyalty_card.app_user)
    yield app_id, 1


def combiner(key, new_values, previously_combined_values):
    # type: (str, list[int], list[int]) -> GeneratorType
    if DEBUG:
        logging.debug('COMBINER %s new_values: %s', key, new_values)
        logging.debug('COMBINER %s previously_combined_values: %s', key, previously_combined_values)
    combined = len(new_values) + sum(previously_combined_values)
    if DEBUG:
        logging.debug('COMBINER %s combined: %s', key, combined)
    yield combined


def reducer(app_id, values):
    # type: (str, list[int]) -> GeneratorType
    total_in_app = sum(values)
    if DEBUG:
        logging.debug('REDUCER %s: %s', app_id, total_in_app)
    yield '%s:%d\n' % (app_id, total_in_app)


class LoyaltyCardsPipeline(pipeline.Pipeline):

    def run(self, bucket_name, key, current_date):
        # type: (str, str, long) -> GeneratorType
        shards = max(1, round(App.all().count() / 100))
        logging.info('Starting %s with %d shards', self.__class__.__name__, shards)
        params = {
            'mapper_spec': 'solutions.common.job.loyalty_stats.mapper',
            'mapper_params': {
                'bucket_name': bucket_name,
                'entity_kind': 'solutions.common.models.loyalty.CustomLoyaltyCard',
                'filters': []
            },
            'combiner_spec': 'solutions.common.job.loyalty_stats.combiner',
            'reducer_spec': 'solutions.common.job.loyalty_stats.reducer',
            'reducer_params': {
                'output_writer': {
                    'bucket_name': bucket_name
                }
            },
            'input_reader_spec': 'mapreduce.input_readers.DatastoreInputReader',
            'output_writer_spec': 'mapreduce.output_writers.GoogleCloudStorageConsistentOutputWriter',
            'shards': shards
        }

        output = yield mapreduce_pipeline.MapreducePipeline(key, **params)

        process_output_pipeline = yield ProcessOutputPipeline(output, current_date)
        with pipeline.After(process_output_pipeline):
            yield CleanupGoogleCloudStorageFiles(output)

    def finalized(self):
        if self.was_aborted:
            logging.error('%s was aborted', self, _suppress=False)
            return
        logging.info('%s was finished', self)


class ProcessOutputPipeline(pipeline.Pipeline):

    def run(self, output, current_date):
        results = []
        for filename in output:
            results.append((yield ProcessFilePipeline(filename)))
        yield List(*results)

    def finalized(self):
        if DEBUG:
            logging.debug('ProcessOutputPipeline: self.outputs.default.value = %s', self.outputs.default.value)
        # list of dicts with key app_id, value dict of organization type, amount
        _, timestamp = self.args
        # One list per shard.
        outputs = self.outputs.default.value  # type: list[list[dict]]
        for output in outputs:
            log_offload.create_log(None, 'oca.custom_loyalty_cards', output, None, timestamp=timestamp)


class ProcessFilePipeline(pipeline.Pipeline):

    def run(self, filename):
        stats_per_app = {}
        with cloudstorage.open(filename, "r") as f:
            for line in f:
                app_id, amount = line.strip().split(':')
                amount = int(amount)
                if app_id in stats_per_app:
                    amount += stats_per_app[app_id]
                stats_per_app[app_id] = amount
        if DEBUG:
            logging.debug('ProcessFilePipeline: %s', stats_per_app)
        return [{'app_id': app_id, 'country': get_country_code_from_app_id(app_id), 'amount': amount}
                for app_id, amount in stats_per_app.iteritems()]


class CleanupGoogleCloudStorageFiles(pipeline.Pipeline):

    def run(self, output):
        for filename in output:
            cloudstorage.delete(filename)
