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

import webapp2

from shop.jobs import clean_unverified_signups
from shop.jobs.export_reseller_invoices import export_reseller_invoices_this_week
from shop.jobs.recurrentbilling import schedule_recurrent_billing
from solutions.common.bizz.joyn import find_all_joyn_matches


class RecurrentBilling(webapp2.RequestHandler):

    def get(self):
        schedule_recurrent_billing()


class ExportResellerInvoicesHandler(webapp2.RequestHandler):
    def get(self):
        export_reseller_invoices_this_week()


class CleanupUnverifiedSignupRequests(webapp2.RequestHandler):

    def get(self):
        clean_unverified_signups.job()


class MatchJoynMerchantsHandler(webapp2.RequestHandler):

    def get(self):
        find_all_joyn_matches()
