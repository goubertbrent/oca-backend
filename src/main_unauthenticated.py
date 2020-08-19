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

from webapp2 import Route
from webapp2_extras.routes import RedirectRoute

from bob.handlers import SetIosAppIdHandler
from mcfw.consts import NOT_AUTHENTICATED
from mcfw.restapi import rest_functions
from rogerthat.handlers.blobstore import CloudStorageBlobstoreHandler
from rogerthat.wsgi import RogerthatWSGIApplication
from shop.callbacks import ProspectDiscoverCallbackHandler
from shop.handlers import ExportInvoicesHandler, ExportProductsHandler, ProspectCallbackHandler, \
    CustomerMapHandler, CustomerMapServicesHandler, CustomerSigninHandler, \
    CustomerSignupHandler, CustomerSetPasswordHandler, CustomerResetPasswordHandler, CustomerSignupPasswordHandler, \
    CustomerCirkloAcceptHandler, VouchersCirkloSignupHandler
import shop.handlers
from solutions.common.handlers.launcher import GetOSALaucherAppsHandler, GetOSALaucherAppHandler
from solutions.common.handlers.loyalty import LoyaltySlideDownloadHandler, LoyaltyNoMobilesUnsubscribeEmailHandler, \
    LoyaltyLotteryConfirmWinnerHandler
from solutions.common.handlers.maps import FlandersHandler
from solutions.common.handlers.menu import ViewMenuItemImageHandler
from solutions.common.handlers.payments import StripeHandler, StripeSuccessHandler, \
    StripeCancelHandler, StripeWebhookHandler
from solutions.common.handlers.vcard import VCardHandler
import solutions.common.restapi
import solutions.common.restapi.app
import solutions.common.restapi.campaignmonitor
from solutions.common.restapi.rss import RssCoronavirusDotBeHandler
from solutions.flex.handlers import FlexHomeHandler


handlers = [
    ('/flex/', FlexHomeHandler),
    ('/unauthenticated/payments/stripe', StripeHandler),
    ('/unauthenticated/payments/stripe/success', StripeSuccessHandler),
    ('/unauthenticated/payments/stripe/cancel', StripeCancelHandler),
    ('/unauthenticated/payments/stripe/webhook', StripeWebhookHandler),
    ('/unauthenticated/loyalty/slide', LoyaltySlideDownloadHandler),
    ('/unauthenticated/loyalty/no_mobiles/unsubscribe_email', LoyaltyNoMobilesUnsubscribeEmailHandler),
    ('/unauthenticated/loyalty/no_mobiles/lottery_winner', LoyaltyLotteryConfirmWinnerHandler),
    ('/unauthenticated/osa/launcher/apps', GetOSALaucherAppsHandler),
    ('/unauthenticated/osa/launcher/app/download', GetOSALaucherAppHandler),
    ('/unauthenticated/osa/flanders', FlandersHandler),
    Route('/unauthenticated/rss/info-coronavirus-be', RssCoronavirusDotBeHandler),
    ('/bob/api/apps/set_ios_app_id', SetIosAppIdHandler),
    ('/shop/invoices/export', ExportInvoicesHandler),
    ('/shop/products/export', ExportProductsHandler),
    ('/shop/prospects/callback', ProspectCallbackHandler),
    ('/shop/prospects/discover/callback', ProspectDiscoverCallbackHandler),
    ('/customers/map/([a-z-_0-9]+)/services', CustomerMapServicesHandler),
    ('/customers/map/([a-z-_0-9]+)', CustomerMapHandler),
    RedirectRoute('/vcards', VCardHandler, 'vcard', strict_slash=True),
    RedirectRoute('/vcards/<user_id:[^/]+>', VCardHandler, 'vcard', strict_slash=True),
    RedirectRoute('/customers/setpassword', CustomerSetPasswordHandler, 'set_password', strict_slash=True),
    RedirectRoute('/customers/setpassword/<app_id:[^/]+>', CustomerSetPasswordHandler, 'set_password_app',
                  strict_slash=True),
    RedirectRoute('/customers/signup-password', CustomerSignupPasswordHandler, 'signup_set_password', strict_slash=True),
    RedirectRoute('/customers/signup-password/<app_id:[^/]+>', CustomerSignupPasswordHandler, 'signup_set_password',
                  strict_slash=True),
    RedirectRoute('/customers/resetpassword', CustomerResetPasswordHandler, 'reset_password', strict_slash=True),
    RedirectRoute('/customers/resetpassword/<app_id:[^/]+>', CustomerResetPasswordHandler, 'reset_password_app',
                  strict_slash=True),
    RedirectRoute('/customers/signin', CustomerSigninHandler, 'signin', strict_slash=True),
    RedirectRoute('/customers/signin/<app_id:[^/]+>', CustomerSigninHandler, 'signin_app', strict_slash=True),
    RedirectRoute('/customers/signup', CustomerSignupHandler, 'signup', strict_slash=True),
    RedirectRoute('/customers/signup/<app_id:[^/]+>', CustomerSignupHandler, 'signup_app', strict_slash=True),
    RedirectRoute('/customers/consent/cirklo', CustomerCirkloAcceptHandler, 'consent_cirklo_accept'),
    RedirectRoute('/vouchers/cirklo/signup', VouchersCirkloSignupHandler, 'cirklo_signup'),
    RedirectRoute('/vouchers/cirklo/signup/<city_id:[^/]+>', VouchersCirkloSignupHandler, 'cirklo_signup'),
    RedirectRoute('/ourcityapp', name='ourcityapp', redirect_to_name='signin', strict_slash=True),
    ('/solutions/common/public/attachment/view/(.*)', CloudStorageBlobstoreHandler),
    ('/solutions/common/public/menu/image/(.*)', ViewMenuItemImageHandler)
]

handlers.extend(rest_functions(solutions.common.restapi, authentication=NOT_AUTHENTICATED))
handlers.extend(rest_functions(solutions.common.restapi.app, authentication=NOT_AUTHENTICATED))
handlers.extend(rest_functions(solutions.common.restapi.campaignmonitor, authentication=NOT_AUTHENTICATED))
handlers.extend(rest_functions(shop.handlers, authentication=NOT_AUTHENTICATED))

app = RogerthatWSGIApplication(handlers, name="main_unauthenticated")
