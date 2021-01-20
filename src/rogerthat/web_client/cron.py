# -*- coding: utf-8 -*-
# Copyright 2020 Green Valley NV
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
import logging
from datetime import datetime

from dateutil.relativedelta import relativedelta
from google.appengine.ext import ndb
from webapp2 import RequestHandler

from rogerthat.web_client.models import WebClientSession, SESSION_EXPIRE_TIME


class CleanupWebSessionsHandler(RequestHandler):
    def get(self):
        expire_date = datetime.now() - relativedelta(seconds=SESSION_EXPIRE_TIME)
        has_results = True
        total = 0
        start_cursor = None
        while has_results:
            results, start_cursor, has_results = WebClientSession \
                .list_timed_out(expire_date) \
                .fetch_page(1000, start_cursor=start_cursor, keys_only=True)
            total += len(results)
            ndb.delete_multi(results)
        logging.info('Deleted %s expired web sessions', total)
