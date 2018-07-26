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

import time
from datetime import date

from dateutil.relativedelta import relativedelta
from google.appengine.ext import deferred

from rogerthat.rpc import users
from solutions.common.bizz.loyalty import create_loyalty_statistics_for_service
from solutions.common.models import SolutionSettings
from solutions.common.models.loyalty import SolutionLoyaltyExport


def job():
    countdown = 0
    for old_export in SolutionLoyaltyExport.all():
        date_int = old_export.year_month
        year = date_int / 100
        month = date_int % 100
        first_day_of_month = int(time.mktime(date(year, month, day=1).timetuple()))
        first_day_of_next_month = int(time.mktime(get_next_month(year, month).timetuple()))
        service_user_email = old_export.parent_key().name()
        sln_settings = SolutionSettings.get(SolutionSettings.create_key(users.User(service_user_email)))
        deferred.defer(create_loyalty_statistics_for_service, sln_settings, first_day_of_month,
                       first_day_of_next_month, _countdown=countdown)
        countdown += 15


def get_next_month(year, month):
    d = date(year=year, month=month, day=1) + relativedelta(months=1)
    return date(d.year, d.month, 1)
