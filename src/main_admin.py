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

from rogerthat.wsgi import RogerthatWSGIApplication
from shop.cron import RecurrentBilling, NotifyExtentionNeededHandler, \
    ExportResellerInvoicesHandler, CleanupUnverifiedSignupRequests, MatchJoynMerchantsHandler
from solution_server_settings.handlers import SolutionServerSettingsHandler
from solutions.common.cron.associations import CreateNonProfitStatistics
from solutions.common.cron.budget import BudgetCheckHandler
from solutions.common.cron.city_vouchers import SolutionCityVouchersExportHandler, \
    SolutionCityVoucherExpiredReminderHandler
from solutions.common.cron.events import SolutionEventsScraper
from solutions.common.cron.events.events import CleanupSolutionEvents, ReminderSolutionEvents, \
    SolutionSyncGoogleCalendarEvents, UpdateSolutionEventStartDate, SolutionEventsDataPublisher
from solutions.common.cron.events.uitdatabank import CityAppSolutionEventsUitdatabank
from solutions.common.cron.forms import FinishFormsCron
from solutions.common.cron.loyalty import LootLotteryCronHandler, SolutionLoyaltyExportHandler
from solutions.common.cron.news import SolutionNewsScraper
from solutions.common.cron.news.rss import SolutionRssScraper
from solutions.common.cron.sandwich import SandwichAutoBroadcastCronHandler
from solutions.common.cron.statistics import DailyStatisticsHandler
from solutions.common.handlers.admin.launcher import OSAAppsPage, PostOSAAppHandler
from solutions.common.handlers.admin.services import ServiceTools

handlers = [
    ('/admin/cron/rpc/cleanup_solution_events', CleanupSolutionEvents),
    ('/admin/cron/rpc/reminder_solution_events', ReminderSolutionEvents),
    ('/admin/cron/rpc/update_first_start_solution_events', UpdateSolutionEventStartDate),
    ('/admin/cron/rpc/solution_sync_google_calendar_events', SolutionSyncGoogleCalendarEvents),
    ('/admin/cron/rpc/solution_events_publish_data', SolutionEventsDataPublisher),
    ('/admin/cron/rpc/solution_cityapp_events_uitdatabank', CityAppSolutionEventsUitdatabank),
    ('/admin/cron/rpc/shop_notify_extention_needed', NotifyExtentionNeededHandler),
    ('/admin/cron/rpc/shop_export_reseller_invoices', ExportResellerInvoicesHandler),
    ('/admin/cron/rpc/solution_module_sandwich_auto_broadcast', SandwichAutoBroadcastCronHandler),
    ('/admin/cron/rpc/solution_loyalty_lottery_loot', LootLotteryCronHandler),
    ('/admin/cron/rpc/solution_loyalty_export', SolutionLoyaltyExportHandler),
    ('/admin/cron/rpc/solution_expired_vouchers_reminder', SolutionCityVoucherExpiredReminderHandler),
    ('/admin/cron/rpc/solution_city_vouchers', SolutionCityVouchersExportHandler),
    ('/admin/cron/rpc/city_association_statistics', CreateNonProfitStatistics),
    ('/admin/cron/rpc/solution_events_scraper', SolutionEventsScraper),
    ('/admin/cron/rpc/solution_news_scraper', SolutionNewsScraper),
    ('/admin/cron/rpc/solution_rss_scraper', SolutionRssScraper),
    ('/admin/cron/rpc/solution_city_vouchers', SolutionCityVouchersExportHandler),
    ('/admin/cron/rpc/solutions_news_budget_updater', BudgetCheckHandler),
    ('/admin/cron/shop/recurrent_billing', RecurrentBilling),
    ('/admin/cron/shop/clean_unverified_signup_requests', CleanupUnverifiedSignupRequests),
    ('/admin/cron/daily_statistics', DailyStatisticsHandler),
    ('/admin/cron/match_joyn', MatchJoynMerchantsHandler),
    ('/admin/cron/finish_forms', FinishFormsCron),
    ('/admin/services', ServiceTools),
    ('/admin/osa/launcher/apps', OSAAppsPage),
    ('/admin/osa/launcher/app/post', PostOSAAppHandler),
    ('/admin/settings', SolutionServerSettingsHandler),
]

app = RogerthatWSGIApplication(handlers, True, name="main_admin", google_authenticated=True)
