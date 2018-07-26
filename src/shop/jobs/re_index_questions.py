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

from rogerthat.bizz.job import run_job
from rogerthat.consts import HIGH_LOAD_WORKER_QUEUE
from solutions.common.bizz.qanda import re_index_question
from solutions.common.models.qanda import Question


def _all_questions():
    return Question.all(keys_only=True)


def re_index_all_questions(queue=HIGH_LOAD_WORKER_QUEUE):
    run_job(_all_questions, [], re_index_question, [], worker_queue=queue)
