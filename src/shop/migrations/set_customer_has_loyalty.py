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

from google.appengine.ext import db

from rogerthat.bizz.job import run_job
from rogerthat.dal import put_and_invalidate_cache

from shop.models import Customer
from solutions.common.bizz import SolutionModule
from solutions.common.dal import get_solution_settings


def all_customers():
    return Customer.all(keys_only=True)


def job():
    run_job(all_customers, [], set_customer_has_loyalty, [])


def set_customer_has_loyalty(customer_key):
    customer = db.get(customer_key)
    if not customer or not customer.service_email:
        return

    sln_settings = get_solution_settings(customer.service_user)
    has_loyalty = SolutionModule.LOYALTY in sln_settings.modules
    if customer.has_loyalty != has_loyalty:
        customer.has_loyalty = has_loyalty
        put_and_invalidate_cache(customer)
