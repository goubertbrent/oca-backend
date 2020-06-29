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

import logging

from google.appengine.ext import db

from rogerthat.bizz.job import run_job
from rogerthat.utils import now
from shop.models import CustomerSignup, CustomerSignupStatus


def all_pending_signups():
    return CustomerSignup.all(keys_only=True).filter('status', CustomerSignupStatus.PENDING)


def remove_if_expired(signup_key, current_timestamp):
    signup = CustomerSignup.get(signup_key)
    timestamp = signup.timestamp
    # Delete signups which have not verified their email after a certain time
    # If they have verified their email, inbox_message_key will be set
    diff = (current_timestamp - timestamp)
    if not signup.inbox_message_key and (diff > CustomerSignup.EXPIRE_TIME):
        logging.info('Deleting CustomerSignup:\n%s', db.to_dict(signup))
        db.delete(signup)


def job():
    run_job(all_pending_signups, [], remove_if_expired, [now()])
