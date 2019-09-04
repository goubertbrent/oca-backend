# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
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
# @@license_version:1.5@@

from google.appengine.ext import db
from rogerthat.bizz.job import run_job

from shop.models import RegioManagerTeam

from solutions.common.models.qanda import Question


def job():
    default_team_id = RegioManagerTeam.get_mobicage().id
    run_job(_qry, [], _worker, [default_team_id])


def _qry():
    return Question.all(keys_only=True)


def _worker(q_key, team_id):
    def trans():
        question = db.get(q_key)
        question.team_id = team_id
        question.put()
    db.run_in_transaction(trans)
