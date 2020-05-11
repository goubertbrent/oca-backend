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

from google.appengine.ext.deferred.deferred import TaskHandler
import webapp2

from mcfw.restapi import rest_functions
from rogerthat.bizz.maps import MapNotificationsHandler
from rogerthat.bizz.rtemail import EmailHandler
from rogerthat.cron.apn_expiration_check import ApnExpirationCheckHandler
from rogerthat.cron.birthday import BirthdayMessagesCronHandler
from rogerthat.cron.jobs import SyncVDABJobsHandler, SendJobNotificationsHandler, \
    CleanupJobsHandeler
from rogerthat.cron.news import NewsUnstickHandler, NewsStatisticsHandler, \
    NewsServiceSetupHandler, NewsGroupVisibilityHandler
from rogerthat.cron.oauth import RemoveStatesHandler
from rogerthat.cron.rpc import Cleanup
from rogerthat.cron.rpc_api_result_retention import CleanupRpcAPIResultHandler
from rogerthat.cron.rpc_capi_call_retention import CleanupRpcCAPICallHandler
from rogerthat.cron.rpc_outstanding_gcm_kicks import Reschedule
from rogerthat.cron.service_api_callback_retention import ProcessServiceAPICallbackHandler
from rogerthat.cron.service_api_result_retention import CleanupServiceAPIResultHandler
from rogerthat.cron.statistics import StatisticsHandler, ServiceStatisticsEmailHandler, AppStatisticsCache, \
    DailyStatisticsHandler
from rogerthat.cron.user import CleanupUserContextHandler
from rogerthat.pages.admin import debugging, mobile_errors, installation_logs
from rogerthat.pages.admin.activation_logs import ActivationLogsHandler
from rogerthat.pages.admin.debugging import UserTools
from rogerthat.pages.admin.explorer import ExplorerPage
from rogerthat.pages.admin.installation_logs import InstallationLogsHandler
from rogerthat.pages.admin.js_embedding import JSEmbeddingTools, DeployJSEmbeddingHandler, SaveJSEmbeddingHandler
from rogerthat.pages.admin.mobile_errors import MobileErrorHandler
from rogerthat.pages.admin.services import ConvertToService, ServiceTools, CreateTrialService, ReleaseTrialService, \
    SetServiceMonitoring, SetServiceCategory
from rogerthat.pages.admin.settings import ServerSettingsHandler
from rogerthat.restapi import explorer, admin
from rogerthat.wsgi import RogerthatWSGIApplication


class WarmupRequestHandler(webapp2.RequestHandler):
    # noinspection PyUnresolvedReferences

    def get(self):
        from rogerthat import models  # @UnusedImport
        from rogerthat.bizz import branding, service, friends, limit, location, messaging, profile  # @UnusedImport
        from rogerthat.bizz import qrtemplate, registration, session, system, user  # @UnusedImport
        from rogerthat.rpc import rpc, http, calls, service as srv, users  # @UnusedImport
        # do not remove the imports, unless you have a very good reason


handlers = [
    ('/cron/rpc/cleanup', Cleanup),
    ('/cron/rpc/cleanup_rpc_api_result', CleanupRpcAPIResultHandler),
    ('/cron/rpc/cleanup_rpc_capi_call', CleanupRpcCAPICallHandler),
    ('/cron/rpc/cleanup_service_api_result', CleanupServiceAPIResultHandler),
    ('/cron/rpc/process_service_api_callback', ProcessServiceAPICallbackHandler),
    ('/cron/rpc/outstanding_kicks', Reschedule),
    ('/cron/rpc/statistics', StatisticsHandler),
    ('/cron/rpc/service_statistics_email', ServiceStatisticsEmailHandler),
    ('/cron/apn_expiration_check', ApnExpirationCheckHandler),
    ('/cron/app_statistics_cache', AppStatisticsCache),
    ('/cron/news/statistics', NewsStatisticsHandler),
    ('/cron/news/group_visibility', NewsGroupVisibilityHandler),
    ('/cron/news/unstick', NewsUnstickHandler),
    ('/cron/news/service_setup', NewsServiceSetupHandler),
    ('/cron/birthday_messages', BirthdayMessagesCronHandler),
    ('/cron/daily_statistics', DailyStatisticsHandler),
    ('/cron/jobs/notifications', SendJobNotificationsHandler),
    ('/cron/jobs/cleanup', CleanupJobsHandeler),
    ('/cron/jobs/vdab/sync', SyncVDABJobsHandler),
    ('/cron/clean-oauth', RemoveStatesHandler),
    ('/cron/maps/notifications', MapNotificationsHandler),
    ('/cron/user/cleanup/context', CleanupUserContextHandler),
    ('/mobiadmin/explorer', ExplorerPage),
    ('/mobiadmin/services', ServiceTools),
    ('/mobiadmin/release_trial_service', ReleaseTrialService),
    ('/mobiadmin/create_trial_service', CreateTrialService),
    ('/mobiadmin/convert_to_service', ConvertToService),
    ('/mobiadmin/set_service_category', SetServiceCategory),
    ('/mobiadmin/set_service_monitoring', SetServiceMonitoring),
    ('/mobiadmin/installation_logs', InstallationLogsHandler),
    ('/mobiadmin/activation_logs', ActivationLogsHandler),
    ('/mobiadmin/client_errors', MobileErrorHandler),
    ('/mobiadmin/settings', ServerSettingsHandler),
    ('/mobiadmin/debugging', UserTools),
    ('/mobiadmin/js_embedding', JSEmbeddingTools),
    ('/mobiadmin/save_js_embedding', SaveJSEmbeddingHandler),
    ('/mobiadmin/deploy_js_embedding', DeployJSEmbeddingHandler),
    ('/_ah/queue/deferred', TaskHandler),
    ('/_ah/warmup', WarmupRequestHandler),
    EmailHandler.mapping()
]

handlers.extend(rest_functions(explorer))
handlers.extend(rest_functions(admin))
handlers.extend(rest_functions(debugging))
handlers.extend(rest_functions(installation_logs))
handlers.extend(rest_functions(mobile_errors))

app = RogerthatWSGIApplication(handlers, True, name="main_admin", google_authenticated=True)
