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
import json
import logging
import time

import cloudstorage
from mapreduce import mapreduce_pipeline
from pipeline import pipeline
from pipeline.common import List
from rogerthat.consts import STATS_QUEUE, DEBUG
from rogerthat.dal.service import get_service_identities
from rogerthat.settings import get_server_settings
from rogerthat.utils import guid, log_offload


def start_job():
    current_date = datetime.datetime.now()
    key = 'module_stats_%s_%s' % (current_date.strftime('%Y-%m-%d'), guid())
    bucket_name = 'oca-mr'
    counter = ModuleStatsPipeline(bucket_name, key, time.mktime(current_date.timetuple()))
    task = counter.start(idempotence_key=key, return_task=True)
    task.add(queue_name=STATS_QUEUE)

    redirect_url = '%s/status?root=%s' % (counter.base_path, counter.pipeline_id)
    logging.info('ModuleStats pipeline url: %s', redirect_url)
    return get_server_settings().baseUrl + redirect_url


def mapper(sln_settings):
    # type: (SolutionSettings) -> GeneratorType
    for service_identity in get_service_identities(sln_settings.service_user):
        yield service_identity.app_id, str(sln_settings.modules)


def _combine(new_values, previous_combined_values):
    # type: (list[list[str]], list[dict[str, int]]) -> dict[str, int]

    combined = {}
    for stats in previous_combined_values:
        for module, count in stats.iteritems():
            if module not in combined:
                combined[module] = count
            else:
                combined[module] += count
    for v in new_values:
        # mapper returns a string
        modules = eval(v) if isinstance(v, basestring) else v
        for module in modules:
            if module not in combined:
                combined[module] = 1
            else:
                combined[module] += 1
    return combined


def combiner(key, new_values, previously_combined_values):
    # type: (str, list[list[str]], list[dict[str, int]]) -> GeneratorType
    if DEBUG:
        logging.debug('combiner %s new_values: %s', key, new_values)
        logging.debug('combiner %s previously_combined_values: %s', key, previously_combined_values)
    combined = _combine(new_values, previously_combined_values)
    if DEBUG:
        logging.debug('combiner %s combined: %s', key, combined)
    yield combined


def reducer(app_id, values):
    # type: (str, list[dict[str, int]]) -> GeneratorType
    if DEBUG:
        logging.info('reducer values: %s', values)
    combined = _combine([], values)
    json_line = json.dumps({'app_id': app_id, 'stats': combined})
    if DEBUG:
        logging.debug('reducer %s: %s', app_id, json_line)
    yield '%s\n' % json_line


class ModuleStatsPipeline(pipeline.Pipeline):

    def run(self, bucket_name, key, current_date):
        # type: (str, str, long) -> GeneratorType
        params = {
            'mapper_spec': 'solutions.common.job.module_statistics.mapper',
            'mapper_params': {
                'bucket_name': bucket_name,
                'entity_kind': 'solutions.common.models.SolutionSettings',
                'filters': []
            },
            'combiner_spec': 'solutions.common.job.module_statistics.combiner',
            'reducer_spec': 'solutions.common.job.module_statistics.reducer',
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
        _, timestamp = self.args
        # list of dicts with key app_id, value dict of module, amount
        outputs = self.outputs.default.value  # type: list[dict[int, int]]
        for output in outputs:
            log_offload.create_log(None, 'oca.active_modules', output, None, timestamp=timestamp)


class ProcessFilePipeline(pipeline.Pipeline):

    def run(self, filename):
        stats_per_app = {}
        with cloudstorage.open(filename, "r") as f:
            for json_line in f:
                d = json.loads(json_line)
                stats_per_app[d['app_id']] = d['stats']
        if DEBUG:
            logging.debug('ProcessFilePipeline: %s', stats_per_app)
        return stats_per_app


class CleanupGoogleCloudStorageFiles(pipeline.Pipeline):

    def run(self, output):
        for filename in output:
            cloudstorage.delete(filename)
