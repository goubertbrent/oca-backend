# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
# NOTICE: THIS FILE HAS BEEN MODIFIED BY GREEN VALLEY BELGIUM NV IN ACCORDANCE WITH THE APACHE LICENSE VERSION 2.0
# Copyright 2018 GIG Technology NV
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
# @@license_version:1.6@@

import webapp2
from google.appengine.ext.deferred import deferred

from rogerthat.bizz import log_analysis
from rogerthat.bizz.app import prepare_app_statistics_cache
from rogerthat.bizz.job.email_statistics import schedule_email_statistics
from rogerthat.bizz.job.service_stats import start_job
from rogerthat.bizz.statistics import generate_all_stats


class StatisticsHandler(webapp2.RequestHandler):

    def get(self):
        log_analysis.run()


class ServiceStatisticsEmailHandler(webapp2.RequestHandler):

    def get(self):
        schedule_email_statistics()


class AppStatisticsCache(webapp2.RequestHandler):
    def get(self):
        deferred.defer(prepare_app_statistics_cache)


class DailyStatisticsHandler(webapp2.RequestHandler):
    def get(self):
        generate_all_stats()
        start_job()
