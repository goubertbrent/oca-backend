# -*- coding: utf-8 -*-
# Copyright 2017 Mobicage NV
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
# @@license_version:1.2@@

from google.appengine.ext import deferred
from rogerthat.bizz.job import run_job
from rogerthat.consts import MIGRATION_QUEUE
from rogerthat.rpc import users
from solutions.common.bizz.qanda import re_index_question
from solutions.common.dal import get_solution_settings
from solutions.common.models.qanda import Question


def job():
    run_job(_qry, [], _worker, [], worker_queue=MIGRATION_QUEUE)

def _qry():
    return Question.all()

def _worker(question):
    sln_settings = get_solution_settings(users.User(question.author))
    question.language = sln_settings.main_language if sln_settings else u'nl'
    question.put()

    deferred.defer(re_index_question, question.key(), _queue=MIGRATION_QUEUE)
