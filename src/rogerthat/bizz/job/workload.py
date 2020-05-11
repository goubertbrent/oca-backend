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

import importlib
import logging

import cloudstorage
from google.appengine.ext import db
from mapreduce import mapreduce_pipeline
from mapreduce.input_readers import DatastoreInputReader
from pipeline import pipeline

from add_1_monkey_patches import suppressing
from rogerthat.consts import HIGH_LOAD_WORKER_QUEUE
from rogerthat.utils import guid


class WorkloadPipeline(pipeline.Pipeline):

    def __init__(self, *args, **kwargs):
        super(WorkloadPipeline, self).__init__(*args, **kwargs)
        self.max_attempts = 31


def run_workload(mapper_params, reducer_params, worker_function, worker_function_args,
                 finalize_function, finalize_function_args, worker_queue=HIGH_LOAD_WORKER_QUEUE):
    worker_function_str = '%s.%s' % (worker_function.__module__, worker_function.__name__)
    finalize_function_str = '%s.%s' % (finalize_function.__module__, finalize_function.__name__)
    key = "run_workload-%s" % (guid())
    counter = RunWorkloadPipeline(key, mapper_params, reducer_params, worker_function_str, worker_function_args,
                                  finalize_function_str, finalize_function_args)
    task = counter.start(idempotence_key=key, return_task=True)
    task.add(queue_name=worker_queue, transactional=db.is_in_transaction())
    redirect_url = "%s/status?root=%s" % (counter.base_path, counter.pipeline_id)
    logging.info("run_workload pipeline url: %s", redirect_url)


def workload_map(m):
    if not m:
        logging.info("Skipped stale record.")
        return
    key = m.key()
    yield (key, key)


def workload_combine(key, values, previously_combined_values):
    yield values + previously_combined_values


def workload_reduce(key, values):
    yield "%s\n" % key


class CustomDatastoreInputReader(DatastoreInputReader):

    @classmethod
    def _validate_filters(cls, filters, model_class):
        pass


class RunWorkloadPipeline(WorkloadPipeline):

    def run(self, key, mapper_params, reducer_params, worker_function, worker_function_args, finalize_function, finalize_function_args):
        output = yield mapreduce_pipeline.MapreducePipeline(key,
            mapper_spec="rogerthat.bizz.job.workload.workload_map",
            mapper_params=mapper_params,
            combiner_spec="rogerthat.bizz.job.workload.workload_combine",
            reducer_spec="rogerthat.bizz.job.workload.workload_reduce",
            reducer_params=reducer_params,
            input_reader_spec="rogerthat.bizz.job.workload.CustomDatastoreInputReader",
            output_writer_spec="mapreduce.output_writers.GoogleCloudStorageConsistentOutputWriter")

        outputs_pipeline = yield RunWorkloadOuputsPipeline(output, worker_function, worker_function_args)
        with pipeline.After(outputs_pipeline):
            logging.info('with pipeline.After(outputs_pipeline):')
            yield CleanupGoogleCloudStorageFiles(output)
            yield RunWorkloadFinalizePipeline(finalize_function, finalize_function_args)

    def finalized(self):
        if self.was_aborted:
            logging.error("RunWorkloadPipeline was aborted", _suppress=False)
            return
        logging.info("RunWorkloadPipeline was finished")


class RunWorkloadOuputsPipeline(WorkloadPipeline):

    def run(self, output, worker_function, worker_function_args):
        for filename in output:
            yield RunWorkloadOuputPipeline(filename, worker_function, worker_function_args)


class RunWorkloadOuputPipeline(WorkloadPipeline):

    def run(self, filename, worker_function, worker_function_args):
        with cloudstorage.open(filename, "r") as f:
            for m_key in f:
                yield RunWorkloadWorkerPipeline(m_key, worker_function, worker_function_args)


class RunWorkloadWorkerPipeline(WorkloadPipeline):

    def run(self, m_key, worker_function, worker_function_args):
        with suppressing():
            module_name, module_function = worker_function.rsplit('.', 1)
            module = importlib.import_module(module_name)
            getattr(module, module_function)(m_key, *worker_function_args)
        return


class RunWorkloadFinalizePipeline(WorkloadPipeline):

    def run(self, finalize_function, finalize_function_args):
        with suppressing():
            module_name, module_function = finalize_function.rsplit('.', 1)
            module = importlib.import_module(module_name)
            getattr(module, module_function)(*finalize_function_args)
        return


class CleanupGoogleCloudStorageFiles(WorkloadPipeline):

    def run(self, output):
        logging.info('CleanupGoogleCloudStorageFiles')
        for filename in output:
            cloudstorage.delete(filename)
