# -*- coding: utf-8 -*-
# Copyright 2020 Green Valley Belgium NV
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
# @@license_version:1.7@@

from datetime import date
from dateutil.relativedelta import relativedelta
import time

from rogerthat.bizz.job import run_job
from rogerthat.consts import MIGRATION_QUEUE
from google.appengine.ext import db
from google.appengine.ext.deferred import deferred
from solutions.common.bizz.loyalty import create_loyalty_statistics_for_service
from solutions.common.models import SolutionSettings
from solutions.common.models.loyalty import SolutionLoyaltyLottery


def create_all_exports():
    run_job(_qry, [], _worker, [])

def _qry():
    return SolutionSettings.all().filter('modules =', 'loyalty')

def _worker(sln_settings):
    def get_month(off):
        today = date.today()
        d = today - relativedelta(months=off)
        return date(d.year, d.month, 1)

    offset = 1
    while offset < 24:  # Goes back till december 2 year back
        first_day_of_month = int(time.mktime(get_month(offset).timetuple()))
        offset += 1
        first_day_of_previous_month = int(time.mktime(get_month(offset).timetuple()))
        deferred.defer(create_loyalty_statistics_for_service, sln_settings, first_day_of_previous_month,
                       first_day_of_month, _queue=MIGRATION_QUEUE)


def put_all_lottery():
    lottery = SolutionLoyaltyLottery.all()
    to_put = list()
    for l in lottery:
        to_put.append(l)
    db.put(to_put)
