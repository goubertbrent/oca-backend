# -*- coding: utf-8 -*-
# Copyright 2016 Mobicage NV
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
# @@license_version:1.1@@

from add_1_monkey_patches import dummy2
from add_2_zip_imports import dummy
from add_3_solution_handlers import register_solution_callback_api_handlers
from bob.handlers import BobFetchHandler, GetAppsHandler, CreateAppHandler, SetFacebookAppDomain, BobTranslationsHandler, \
    BobPutMainService, BobPutAppTrack
from mcfw.consts import NOT_AUTHENTICATED
from mcfw.restapi import rest_functions
from rogerthat.rpc.service import register_service_api_calls
from rogerthat.wsgi import RogerthatWSGIApplication
from shop.callbacks import ProspectDiscoverCallbackHandler
from shop.handlers import ExportInvoicesHandler, ExportProductsHandler, ProspectCallbackHandler, \
    BeaconsAppValidateUrlHandler, CustomerMapHandler, CustomerMapServicesHandler
from solutions.common.handlers.broadcast import ViewAttachmentHandler
from solutions.common.handlers.callback.twitter import SolutionsCallbackTwitterHandler
from solutions.common.handlers.launcher import GetOSALaucherAppsHandler, GetOSALaucherAppHandler
from solutions.common.handlers.loyalty import LoyaltySlideDownloadHandler, LoyaltyNoMobilesUnsubscribeEmailHandler, \
    LoyaltyLotteryConfirmWinnerHandler
from solutions.common.handlers.menu import ViewMenuItemImageHandler
from solutions.common.restapi import yourservicehere
import solutions.common.restapi
import solutions.djmatic.api
from solutions.djmatic.handlers import DJMaticHomeHandler
from solutions.flex.handlers import FlexHomeHandler


dummy2()
dummy()
register_solution_callback_api_handlers()

handlers = [
    ('/djmatic/', DJMaticHomeHandler),
    ('/flex/', FlexHomeHandler),
    ('/unauthenticated/loyalty/slide', LoyaltySlideDownloadHandler),
    ('/unauthenticated/loyalty/no_mobiles/unsubscribe_email', LoyaltyNoMobilesUnsubscribeEmailHandler),
    ('/unauthenticated/loyalty/no_mobiles/lottery_winner', LoyaltyLotteryConfirmWinnerHandler),
    ('/unauthenticated/osa/launcher/apps', GetOSALaucherAppsHandler),
    ('/unauthenticated/osa/launcher/app/download', GetOSALaucherAppHandler),
    ('/unauthenticated/osa/callback/twitter', SolutionsCallbackTwitterHandler),
    ('/bob/fetch', BobFetchHandler),
    ('/bob/api/apps', GetAppsHandler),
    ('/bob/api/apps/create', CreateAppHandler),
    ('/bob/api/apps/set_domain', SetFacebookAppDomain),
    ('/bob/api/apps/put_main_service', BobPutMainService),
    ('/bob/api/apps/put_track', BobPutAppTrack),
    ('/bob/api/translations', BobTranslationsHandler),
    ('/solutions/djmatic/api/1', solutions.djmatic.api.DJMaticApiHandler),
    ('/shop/invoices/export', ExportInvoicesHandler),
    ('/shop/products/export', ExportProductsHandler),
    ('/shop/prospects/callback', ProspectCallbackHandler),
    ('/shop/prospects/discover/callback', ProspectDiscoverCallbackHandler),
    ('/shop/beacons/app/validate_url', BeaconsAppValidateUrlHandler),
    ('/customers/map/([a-z-_]+)/services', CustomerMapServicesHandler),
    ('/customers/map/([a-z-_]+)', CustomerMapHandler),
    ('/solutions/common/public/attachment/view/(.*)', ViewAttachmentHandler),
    ('/solutions/common/public/menu/image/(.*)', ViewMenuItemImageHandler),
]

register_service_api_calls(solutions.djmatic.api)
register_service_api_calls(yourservicehere)

handlers.extend(rest_functions(solutions.common.restapi, authentication=NOT_AUTHENTICATED))

app = RogerthatWSGIApplication(handlers, name="main_unauthenticated")
