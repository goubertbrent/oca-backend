# -*- coding: utf-8 -*-
# Copyright 2017 GIG Technology NV
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

import datetime
import time

from rogerthat.utils import today
from shop.business.invoice import export_reseller_invoices


def export_reseller_invoices_this_week():
    current_date = datetime.datetime.utcfromtimestamp(today())
    current_weekday = current_date.weekday()
    beginning_of_current_week = current_date - datetime.timedelta(days=current_weekday)
    start_of_last_week = datetime.timedelta(weeks=1)
    last_week = beginning_of_current_week - start_of_last_week
    start_timestamp = time.mktime(last_week.utctimetuple())
    end_timestamp = time.mktime(beginning_of_current_week.utctimetuple())
    export_reseller_invoices(int(start_timestamp), int(end_timestamp), True)
