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

from google.appengine.ext import ndb, webapp

from rogerthat.bizz.job import run_job
from rogerthat.rpc import users
from rogerthat.utils import today
from solutions.common.models.polls import Poll, PollAnswer, PollStatus
from solutions.common.bizz.polls import stop_poll


class PollAutoCloseHandler(webapp.RequestHandler):

    def get(self):
        auto_close_polls()


def finished_polls_query(day_date):
    return Poll.query(
        Poll.status == PollStatus.RUNNING,
        Poll.ends_on <= datetime.datetime.utcfromtimestamp(day_date)
    )


def auto_close_poll(poll_key, dry_run=False):
    logging.debug('Auto-closing poll: %s', poll_key)
    if not dry_run:
        service_user, poll_id = users.User(unicode(poll_key.parent().id())), poll_key.id()
        stop_poll(service_user, poll_id)


def auto_close_polls(dry_run=False):
    _today = today()
    run_job(finished_polls_query, [_today], auto_close_poll, [dry_run])
