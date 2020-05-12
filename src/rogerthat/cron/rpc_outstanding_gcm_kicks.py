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

from google.appengine.ext import webapp, deferred, db

from rogerthat.rpc.models import OutStandingFirebaseKick
from rogerthat.rpc.rpc import firebase, PRIORITY_HIGH
from rogerthat.utils import now


class Reschedule(webapp.RequestHandler):

    def get(self):
        purge_timestamp = now()
        deferred.defer(fcm_kick, purge_timestamp)


def fcm_kick(from_):
    logging.info("Getting outstanding FCM kicks from datastore")
    outstanding_kicks = OutStandingFirebaseKick.all(keys_only=True).filter("timestamp <=", from_ - 300).order("timestamp")
    results = outstanding_kicks.fetch(1000)
    if not results:
        return
    logging.info("Bulk kicking registration_ids")
    registration_ids = list()
    for key in results:
        registration_ids.append(key.name())
    firebase.kick(registration_ids, PRIORITY_HIGH)
    db.delete(results)
    logging.info("Continue in 5 seconds ...")
    deferred.defer(fcm_kick, from_, _countdown=5)
