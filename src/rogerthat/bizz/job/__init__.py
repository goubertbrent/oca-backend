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

import inspect

from google.appengine.api import taskqueue
from google.appengine.datastore import datastore_rpc
from google.appengine.ext import db, ndb
from google.appengine.ext.deferred import deferred

from mcfw.properties import azzert
from mcfw.utils import chunks
from rogerthat.consts import HIGH_LOAD_CONTROLLER_QUEUE, HIGH_LOAD_WORKER_QUEUE

MODE_SINGLE = 1
MODE_BATCH = 2


def run_job(qry_function, qry_function_args, worker_function, worker_function_args, mode=MODE_SINGLE,
            batch_size=50, batch_timeout=0, qry_transactional=False, worker_queue=HIGH_LOAD_WORKER_QUEUE,
            controller_queue=HIGH_LOAD_CONTROLLER_QUEUE):
    qry_function_args = qry_function_args or []
    worker_function_args = worker_function_args or []
    azzert(inspect.isfunction(qry_function), 'Only functions allowed for argument qry_function')
    azzert(inspect.isfunction(worker_function), 'Only functions allowed for argument worker_function')
    azzert(mode in (MODE_SINGLE, MODE_BATCH))
    azzert(isinstance(qry_function_args, list), 'qry_function_args must be a list')
    azzert(isinstance(worker_function_args, list), 'worker_function_args must be a list')
    azzert(batch_size <= 500)
    # batch_size shouldn't be too high in case your keys are large, else you might go over the max task size of 100KB
    deferred.defer(_run_qry, qry_function, qry_function_args, worker_function, worker_function_args, mode, batch_size,
                   batch_timeout, qry_transactional=qry_transactional, worker_queue=worker_queue,
                   controller_queue=controller_queue, _transactional=db.is_in_transaction(), _queue=controller_queue)


def _exec_qry(qry_function, qry_function_args, cursor, fetch_size):
    qry = qry_function(*qry_function_args)
    if isinstance(qry, ndb.Query):
        items, new_cursor, has_more = qry.fetch_page(fetch_size, start_cursor=cursor, keys_only=True)
    else:
        qry.with_cursor(cursor)
        items = qry.fetch(fetch_size)
        new_cursor = qry.cursor()
        has_more = len(items) == fetch_size  # might not always be true but it's a good guess
    return items, new_cursor, has_more


def _run_qry(qry_function, qry_function_args, worker_function, worker_function_args, mode, batch_size, batch_timeout,
             batch_timeout_counter=0, qry_transactional=False, cursor=None, worker_queue=HIGH_LOAD_WORKER_QUEUE,
             controller_queue=HIGH_LOAD_CONTROLLER_QUEUE):
    if mode == MODE_SINGLE:
        fetch_size = taskqueue.MAX_TASKS_PER_ADD
    else:
        fetch_size = min(int(taskqueue.MAX_TASKS_PER_ADD * batch_size), datastore_rpc.BaseConnection.MAX_GET_KEYS)
    if qry_transactional:
        items, new_cursor, has_more = db.run_in_transaction(_exec_qry, qry_function, qry_function_args, cursor,
                                                            fetch_size)
    else:
        items, new_cursor, has_more = _exec_qry(qry_function, qry_function_args, cursor, fetch_size)

    if not items:
        return
    tasks = []
    taskargs = {
        'url': deferred._DEFAULT_URL,
        'headers': deferred._TASKQUEUE_HEADERS,
    }
    count_down = batch_timeout_counter
    if mode == MODE_SINGLE:
        for item in items:
            pickled = deferred.serialize(worker_function, item, *worker_function_args)
            tasks.append(taskqueue.Task(payload=pickled, countdown=count_down, **taskargs))
            count_down += batch_timeout
    else:
        for keys in chunks(items, batch_size):
            pickled = deferred.serialize(worker_function, keys, *worker_function_args)
            tasks.append(taskqueue.Task(payload=pickled, countdown=count_down, **taskargs))
            count_down += batch_timeout

    taskqueue.Queue(worker_queue).add(tasks)
    if has_more:
        deferred.defer(_run_qry, qry_function, qry_function_args, worker_function, worker_function_args, mode,
                       batch_size, batch_timeout, count_down, qry_transactional, new_cursor, worker_queue=worker_queue,
                       controller_queue=controller_queue, _queue=controller_queue)
