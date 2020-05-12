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

from rogerthat.bizz.job import run_job
from rogerthat.dal import put_and_invalidate_cache
from rogerthat.rpc import users
from shop.models import Customer
from solutions.common.dal import get_solution_settings


def job():
    run_job(_all_customers, [], _update_login, [])

def _all_customers():
    return Customer.all()

def _update_login(customer):
    if customer.user_email != customer.service_email:
        service_user = users.User(customer.service_email)
        sln_settings = get_solution_settings(service_user)
        sln_settings.login = users.User(customer.user_email)
        put_and_invalidate_cache(sln_settings)
