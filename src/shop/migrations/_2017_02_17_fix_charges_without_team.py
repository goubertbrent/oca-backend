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

import logging

from rogerthat.bizz.job import run_job
from rogerthat.consts import MIGRATION_QUEUE
from shop.models import Charge, Customer


def job():
    run_job(_get_charges, [], _fix_charge, [], worker_queue=MIGRATION_QUEUE)


def _get_charges():
    return Charge.all(keys_only=True).filter('team_id', None)


def _fix_charge(charge_key):
    charge = Charge.get(charge_key)
    charge.team_id = Customer.get(charge.customer_key).team_id
    if not charge.team_id:
        logging.error('Cannot fix charge {}: No team set on customer {}'.format(charge.id, charge.customer_id))
    charge.put()
