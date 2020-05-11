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

from collections import Callable

from google.appengine.api.taskqueue import taskqueue, Queue, MAX_TASKS_PER_ADD, Task
from google.appengine.ext.deferred import deferred
from typing import List, Any

from mcfw.utils import chunks


def create_task(func, *args, **kwargs):
    # type: (Callable[[Any], Any], *object, **object) -> taskqueue.Task
    name = kwargs.pop('_task_name', None)
    countdown = kwargs.pop('_countdown', None)
    payload = deferred.serialize(func, *args, **kwargs)
    return taskqueue.Task(payload=payload, url=deferred._DEFAULT_URL, headers=deferred._TASKQUEUE_HEADERS,
                          name=name, countdown=countdown)


def schedule_tasks(tasks, queue_name=deferred._DEFAULT_QUEUE):
    # type: (List[Task], str) -> List[Task]
    queue = Queue(queue_name)
    results = []
    for chunk in chunks(tasks, MAX_TASKS_PER_ADD):
        results.extend(queue.add(chunk))
    return results
