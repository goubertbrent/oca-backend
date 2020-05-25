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

from google.appengine.ext import deferred
import webapp2

from rogerthat.bizz.jobs.cleanup import cleanup_inactive_users
from rogerthat.bizz.jobs.notifications import schedule_reminders
from rogerthat.bizz.jobs.vdab import sync_jobs


class SendJobNotificationsHandler(webapp2.RequestHandler):

    def get(self):
        schedule_reminders()


class CleanupJobsHandeler(webapp2.RequestHandler):

    def get(self):
        cleanup_inactive_users()


class SyncVDABJobsHandler(webapp2.RequestHandler):

    def get(self):
        deferred.defer(sync_jobs)