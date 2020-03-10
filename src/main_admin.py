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
import admin.explorer.api
from admin.explorer.handlers import ExplorerHandler
from mcfw.restapi import rest_functions
from rogerthat.wsgi import RogerthatWSGIApplication
from shop.cron import RecurrentBilling, ExportResellerInvoicesHandler, \
    CleanupUnverifiedSignupRequests
from solution_server_settings.handlers import SolutionServerSettingsHandler
from solutions.common.cron.associations import CreateNonProfitStatistics
from solutions.common.cron.budget import BudgetCheckHandler
from solutions.common.cron.city_vouchers import SolutionCityVouchersExportHandler, \
    SolutionCityVoucherExpiredReminderHandler
from solutions.common.cron.events.events import CleanupSolutionEvents, SolutionSyncGoogleCalendarEvents, \
    ReIndexPeriodicEventsHandler
from solutions.common.cron.events.uitdatabank import CityAppSolutionEventsUitdatabank
from solutions.common.cron.forms import FinishFormsCron
from solutions.common.cron.loyalty import LootLotteryCronHandler, SolutionLoyaltyExportHandler
from solutions.common.cron.news.rss import SolutionRssScraper
from solutions.common.cron.paddle import SyncPaddleInfoHandler
from solutions.common.cron.sandwich import SandwichAutoBroadcastCronHandler
from solutions.common.cron.statistics import DailyStatisticsHandler
from solutions.common.handlers.admin.launcher import OSAAppsPage, PostOSAAppHandler
from solutions.common.handlers.admin.services import ServiceTools


handlers = [
    ('/admin/cron/rpc/cleanup_solution_events', CleanupSolutionEvents),
    ('/admin/cron/rpc/re_index_periodic_events', ReIndexPeriodicEventsHandler),
    ('/admin/cron/rpc/solution_sync_google_calendar_events', SolutionSyncGoogleCalendarEvents),
    ('/admin/cron/rpc/solution_cityapp_events_uitdatabank', CityAppSolutionEventsUitdatabank),
    ('/admin/cron/rpc/shop_export_reseller_invoices', ExportResellerInvoicesHandler),
    ('/admin/cron/rpc/solution_module_sandwich_auto_broadcast', SandwichAutoBroadcastCronHandler),
    ('/admin/cron/rpc/solution_loyalty_lottery_loot', LootLotteryCronHandler),
    ('/admin/cron/rpc/solution_loyalty_export', SolutionLoyaltyExportHandler),
    ('/admin/cron/rpc/solution_expired_vouchers_reminder', SolutionCityVoucherExpiredReminderHandler),
    ('/admin/cron/rpc/solution_city_vouchers', SolutionCityVouchersExportHandler),
    ('/admin/cron/rpc/city_association_statistics', CreateNonProfitStatistics),
    ('/admin/cron/rpc/solution_rss_scraper', SolutionRssScraper),
    ('/admin/cron/rpc/solution_city_vouchers', SolutionCityVouchersExportHandler),
    ('/admin/cron/rpc/solutions_news_budget_updater', BudgetCheckHandler),
    ('/admin/cron/shop/recurrent_billing', RecurrentBilling),
    ('/admin/cron/shop/clean_unverified_signup_requests', CleanupUnverifiedSignupRequests),
    ('/admin/cron/daily_statistics', DailyStatisticsHandler),
    ('/admin/cron/finish_forms', FinishFormsCron),
    ('/admin/cron/paddle', SyncPaddleInfoHandler),
    ('/admin/services', ServiceTools),
    ('/admin/osa/launcher/apps', OSAAppsPage),
    ('/admin/osa/launcher/app/post', PostOSAAppHandler),
    ('/admin/settings', SolutionServerSettingsHandler),
    ('/admin/explorer', ExplorerHandler),
]

handlers.extend(rest_functions(admin.explorer.api))

app = RogerthatWSGIApplication(handlers, True, name="main_admin", google_authenticated=True)
