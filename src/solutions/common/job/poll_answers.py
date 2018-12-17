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
from types import GeneratorType

import cloudstorage
from mapreduce import mapreduce_pipeline
from pipeline import pipeline
from pipeline.common import List
from rogerthat.consts import DEFAULT_QUEUE, DEBUG
from rogerthat.models import App
from rogerthat.settings import get_server_settings
from rogerthat.utils import guid, log_offload
from rogerthat.utils.app import get_app_id_from_app_user
from solutions.common.models.polls import PollAnswer


def start_job(poll_id):
    current_date = datetime.datetime.now()
    key = '%d_poll_answers_%s_%s' % (poll_id, current_date.strftime('%Y-%m-%d'), guid())
    bucket_name = 'oca-mr'
    counter = PollAnswersPipeline(bucket_name, key, time.mktime(current_date.timetuple()))
    task = counter.start(idempotence_key=key, return_task=True)
    task.add(queue_name=DEFAULT_QUEUE)  # TBD

    redirect_url = '%s/status?root=%s' % (counter.base_path, counter.pipeline_id)
    logging.info('PollAnswersPipeline pipeline url: %s', redirect_url)
    return get_server_settings().baseUrl + redirect_url


def mapper(poll_answer):
    # type: (PollAnswer) -> GeneratorType
    for question_answer in poll_answer.question_answers:
        for value in question_answer.values:
            answer_key = '%d_%s' % (question_answer.question_id, value)
            yield answer_key, 1


def combiner(key, new_values, previously_combined_values):
    # type: (str, list[int], list[int]) -> GeneratorType
    if DEBUG:
        logging.debug('COMBINER %s new_values: %s', key, new_values)
        logging.debug('COMBINER %s previously_combined_values: %s', key, previously_combined_values)
    combined = len(new_values) + sum(previously_combined_values)
    if DEBUG:
        logging.debug('COMBINER %s combined: %s', key, combined)
    yield combined


def reducer(answer_key, values):
    # type: (str, list[int]) -> GeneratorType
    total_count = sum(values)
    if DEBUG:
        logging.debug('REDUCER %s: %s', answer_key, total_count)
    yield '%s:%d\n' % (answer_key, total_count)


class PollAnswersPipeline(pipeline.Pipeline):
    def run(self, bucket_name, key, current_date):
        # type: (str, str, long) -> GeneratorType
        poll_id = long(key.split('_')[0])
        params = {
            'mapper_spec': 'solutions.common.job.poll_answers.mapper',
            'mapper_params': {
                'bucket_name': bucket_name,
                'entity_kind': 'solutions.common.models.polls.PollAnswer',
                'filters': [
                    ('poll_id', '=', poll_id)
                ]
            },
            'combiner_spec': 'solutions.common.job.poll_answers.combiner',
            'reducer_spec': 'solutions.common.job.poll_answers.reducer',
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
        # list of dicts with key answer_key, value int count
        outputs = self.outputs.default.value  # type: list[list[dict]]
        import logging
        for output in outputs:
            logging.warning(output)


class ProcessFilePipeline(pipeline.Pipeline):

    def run(self, filename):
        counts_per_answer = {}
        with cloudstorage.open(filename, "r") as f:
            for line in f:
                answer_key, count = line.strip().split(':')
                count = long(count)
                if answer_key in counts_per_answer:
                    count += counts_per_answer[answer_key]
                counts_per_answer[answer_key] = count

        if DEBUG:
            logging.debug('ProcessFilePipeline: %s', counts_per_answer)
        return counts_per_answer


class CleanupGoogleCloudStorageFiles(pipeline.Pipeline):
    def run(self, output):
        for filename in output:
            cloudstorage.delete(filename)
