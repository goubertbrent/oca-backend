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

import shop.handlers
import solutions.common.restapi
import solutions.common.restapi.campaignmonitor
from bob.handlers import SetIosAppIdHandler
from mcfw.consts import NOT_AUTHENTICATED
from mcfw.restapi import rest_functions
from rogerthat.handlers.blobstore import CloudStorageBlobstoreHandler
from rogerthat.wsgi import RogerthatWSGIApplication
from shop.handlers import CustomerMapHandler, CustomerMapServicesHandler, CustomerSigninHandler, \
    CustomerSignupHandler, CustomerSetPasswordHandler, CustomerResetPasswordHandler, CustomerSignupPasswordHandler, \
    CustomerCirkloAcceptHandler, VouchersCirkloSignupHandler
from solutions.common.handlers.loyalty import LoyaltySlideDownloadHandler, LoyaltyNoMobilesUnsubscribeEmailHandler, \
    LoyaltyLotteryConfirmWinnerHandler
from solutions.common.handlers.menu import ViewMenuItemImageHandler
from solutions.common.handlers.vcard import VCardHandler
from solutions.common.restapi.rss import RssCoronavirusDotBeHandler
from solutions.flex.handlers import FlexHomeHandler

handlers = [
    ('/flex/', FlexHomeHandler),
    ('/unauthenticated/loyalty/slide', LoyaltySlideDownloadHandler),
    ('/unauthenticated/loyalty/no_mobiles/unsubscribe_email', LoyaltyNoMobilesUnsubscribeEmailHandler),
    ('/unauthenticated/loyalty/no_mobiles/lottery_winner', LoyaltyLotteryConfirmWinnerHandler),
    Route('/unauthenticated/rss/info-coronavirus-be', RssCoronavirusDotBeHandler),
    ('/bob/api/apps/set_ios_app_id', SetIosAppIdHandler),
    ('/customers/map/([a-z-_0-9]+)/services', CustomerMapServicesHandler),
    ('/customers/map/([a-z-_0-9]+)', CustomerMapHandler),
    RedirectRoute('/vcards', VCardHandler, 'vcard', strict_slash=True),
    RedirectRoute('/vcards/<user_id:[^/]+>', VCardHandler, 'vcard', strict_slash=True),
    RedirectRoute('/customers/setpassword', CustomerSetPasswordHandler, 'set_password', strict_slash=True),
    RedirectRoute('/customers/signup-password', CustomerSignupPasswordHandler, 'signup_set_password', strict_slash=True),
    RedirectRoute('/customers/resetpassword', CustomerResetPasswordHandler, 'reset_password', strict_slash=True),
    RedirectRoute('/customers/signin', CustomerSigninHandler, 'signin', strict_slash=True),
    Route('/customers/signin/<app_id:[^/]+>', CustomerSigninHandler, 'signin_app'),
    RedirectRoute('/customers/signup', CustomerSignupHandler, 'signup', strict_slash=True),
    RedirectRoute('/customers/consent/cirklo', CustomerCirkloAcceptHandler, 'consent_cirklo_accept'),
    RedirectRoute('/vouchers/cirklo/signup', VouchersCirkloSignupHandler, 'cirklo_signup'),
    RedirectRoute('/vouchers/cirklo/signup/<city_id:[^/]+>', VouchersCirkloSignupHandler, 'cirklo_signup'),
    RedirectRoute('/ourcityapp', name='ourcityapp', redirect_to_name='signin', strict_slash=True),
    ('/solutions/common/public/attachment/view/(.*)', CloudStorageBlobstoreHandler),
    ('/solutions/common/public/menu/image/(.*)', ViewMenuItemImageHandler)
]

handlers.extend(rest_functions(solutions.common.restapi, authentication=NOT_AUTHENTICATED))
handlers.extend(rest_functions(solutions.common.restapi.campaignmonitor, authentication=NOT_AUTHENTICATED))
handlers.extend(rest_functions(shop.handlers, authentication=NOT_AUTHENTICATED))

app = RogerthatWSGIApplication(handlers, name="main_unauthenticated")
