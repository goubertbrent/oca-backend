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

from rogerthat.bizz.job import re_index_app_users, re_index_service_identities
from rogerthat.consts import DATASWITCH_QUEUE
from shop.jobs.prospects import re_index_all_prospects
from shop.jobs.re_index_questions import re_index_all_questions
from shop.migrations import re_index_all_customers
from solutions.common.bizz.city_vouchers import re_index_all_vouchers_all_apps


def re_index_everything():
    # Re-indexes everything that uses the search index api.
    # rogerthat
    re_index_app_users.job(DATASWITCH_QUEUE)
    re_index_service_identities.job(DATASWITCH_QUEUE)

    # solutions / shop
    re_index_all_prospects(DATASWITCH_QUEUE)
    re_index_all_customers(DATASWITCH_QUEUE)
    re_index_all_questions(DATASWITCH_QUEUE)
    re_index_all_vouchers_all_apps(DATASWITCH_QUEUE)
