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

from google.appengine.ext import ndb

from rogerthat.bizz.job import run_job
from rogerthat.models.forms import Form
from solutions.common.bizz.forms import update_form_statistics
from solutions.common.bizz.forms.statistics import get_random_shard_number
from solutions.common.models.forms import FormSubmission, FormStatisticsShardConfig


def rebuild_form_statistics(dry_run=True, batch_timeout=1):
    to_delete = []
    for form_key in Form.query().fetch(keys_only=True):
        form_id = form_key.id()
        to_delete.append(FormStatisticsShardConfig.create_key(form_id))
        to_delete.extend(FormStatisticsShardConfig.get_all_keys(form_id))
    if dry_run:
        return len(to_delete), to_delete
    ndb.delete_multi(to_delete)
    run_job(_get_submissions, [], _put_stats, [], batch_timeout=batch_timeout)


def _get_submissions():
    return FormSubmission().query()


def _put_stats(submission_key):
    submission = submission_key.get()
    update_form_statistics(submission, get_random_shard_number(submission.form_id))
