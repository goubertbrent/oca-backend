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
import time

import cloudstorage
from mapreduce import mapreduce_pipeline
from pipeline import pipeline
from pipeline.common import List

from rogerthat.consts import STATS_QUEUE, DEBUG, PIPELINE_BUCKET
from rogerthat.dal.profile import get_service_profile
from rogerthat.models import App, ServiceProfile
from rogerthat.settings import get_server_settings
from rogerthat.utils import guid, log_offload


def start_job():
    current_date = datetime.datetime.now()
    key = 'service_stats_%s_%s' % (current_date.strftime('%Y-%m-%d'), guid())
    counter = ServiceStatsPipeline(PIPELINE_BUCKET, key, time.mktime(current_date.timetuple()))
    task = counter.start(idempotence_key=key, return_task=True)
    task.add(queue_name=STATS_QUEUE)

    redirect_url = '%s/status?root=%s' % (counter.base_path, counter.pipeline_id)
    logging.info('ServiceStats pipeline url: %s', redirect_url)
    return get_server_settings().baseUrl + redirect_url


def mapper(service_identity):
    # type: (ServiceIdentity) -> GeneratorType
    service_profile = get_service_profile(service_identity.service_user)
    if not service_profile:
        logging.error('No service profile found for service identity %s', service_identity.service_user)
    if service_profile.expiredAt > 0:
        return
    else:
        yield service_identity.app_id, str((service_profile.organizationType, 1))  # must return a string


def _combine(new_values, previous_combined_values):
    # type: (list[tuple[int, int]], list[tuple[int, int]]) -> dict[int, int]
    combined = dict(previous_combined_values)
    for v in new_values:
        # mapper returns a string
        organization_type, count = eval(v) if isinstance(v, basestring) else v
        if organization_type not in combined:
            combined[organization_type] = 0
        combined[organization_type] += count
    return combined


def combiner(key, new_values, previously_combined_values):
    # type: (str, list[tuple[int, int]], list[tuple[int, int]]) -> GeneratorType
    if DEBUG:
        logging.debug('COMBINER %s new_values: %s', key, new_values)
        logging.debug('COMBINER %s previously_combined_values: %s', key, previously_combined_values)
    combined = _combine(new_values, previously_combined_values)
    if DEBUG:
        logging.debug('COMBINER %s combined: %s', key, combined)
    for i in combined.iteritems():
        yield i


def reducer(app_id, values):
    # type: (str, list[tuple[int, int]]) -> GeneratorType
    combined = _combine(values, [])
    stats = {ServiceProfile.localized_singular_organization_type(organization_type, 'en', app_id): count
             for organization_type, count in combined.iteritems()}
    json_line = json.dumps({'app_id': app_id, 'stats': stats})
    if DEBUG:
        logging.debug('REDUCER %s: %s', app_id, json_line)
    yield '%s\n' % json_line


class ServiceStatsPipeline(pipeline.Pipeline):

    def run(self, bucket_name, key, current_date):
        # type: (str, str, long) -> GeneratorType
        shards = max(2, int(App.all(keys_only=True).count() / 100))  # A maximum of 100 apps will be logged per shard
        logging.info('Starting ServiceStatsPipeline with %d shards', shards)
        params = {
            'mapper_spec': 'rogerthat.bizz.job.service_stats.mapper',
            'mapper_params': {
                'bucket_name': bucket_name,
                'entity_kind': 'rogerthat.models.ServiceIdentity',
                'filters': []
            },
            'combiner_spec': 'rogerthat.bizz.job.service_stats.combiner',
            'reducer_spec': 'rogerthat.bizz.job.service_stats.reducer',
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
        outputs = self.outputs.default.value  # type: list[dict[int, int]]
        for output in outputs:
            log_offload.create_log(None, 'rogerthat.total_services', output, None, timestamp=timestamp)


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
