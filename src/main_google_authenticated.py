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

import webapp2

import rogerthat.bizz.communities.api
from mcfw.restapi import rest_functions
from rogerthat.handlers.image_handlers import AppQRTemplateHandler
from rogerthat.handlers.proxy import ProxyHandlerConfigurator
from rogerthat.handlers.upload_handlers import UploadAppAssetHandler, UploadDefaultBrandingHandler, \
    UploadGlobalAppAssetHandler, UploadGlobalBrandingHandler
from rogerthat.restapi import apps, embedded_apps, firebase, payment
from rogerthat.wsgi import RogerthatWSGIApplication
from shop import view, shop_q_and_a
from shop.handlers import StaticFileHandler, GenerateQRCodesHandler
from shop.view import BizzAdminHandler, QuestionsHandler, \
    QuestionsDetailHandler, authorize_manager, LoyaltySlidesHandler, UploadLoyaltySlideHandler, \
    LoginAsCustomerHandler, ExportEmailAddressesHandler, \
    LoyaltySlidesNewOrderHandler, UploadLoyaltySlideNewOrderHandler, \
    ShopLogoutHandler, CustomersImportHandler, ConsoleHandler, ConsoleIndexHandler

handlers = [
    ('/internal/shop/?', BizzAdminHandler),
    ('/internal/shop/logout', ShopLogoutHandler),
    ('/internal/shop/questions', QuestionsHandler),
    ('/internal/shop/questions/(.*)', QuestionsDetailHandler),
    ('/internal/shop/loyalty/slides', LoyaltySlidesHandler),
    ('/internal/shop/loyalty/slides/new_order', LoyaltySlidesNewOrderHandler),
    ('/internal/shop/loyalty/slide/upload', UploadLoyaltySlideHandler),
    ('/internal/shop/loyalty/slide/new_order/upload', UploadLoyaltySlideNewOrderHandler),
    ('/internal/shop/login_as', LoginAsCustomerHandler),
    ('/internal/shop/contacts_export', ExportEmailAddressesHandler),
    ('/internal/shop/stat/(.*)', StaticFileHandler),
    ('/internal/shop/customers/generate-qr', GenerateQRCodesHandler),
    ('/internal/shop/customers/import', CustomersImportHandler),
    webapp2.Route('/internal/console<route:.*>', ConsoleHandler),
    webapp2.Route('/console-api/images/apps/<app_id:[^/]+>/qr-templates/<description:[^/]+>', AppQRTemplateHandler),
    webapp2.Route('/console-api/uploads/apps/<app_id:[^/]+>/assets/<asset_type:[^/]+>', UploadAppAssetHandler),
    webapp2.Route('/console-api/uploads/assets', UploadGlobalAppAssetHandler),
    webapp2.Route('/console-api/uploads/assets/<asset_id:[^/]+>', UploadGlobalAppAssetHandler),
    webapp2.Route('/console-api/uploads/apps/<app_id:[^/]+>/default-brandings/<branding_type:[^/]+>',
                  UploadDefaultBrandingHandler),
    webapp2.Route('/console-api/uploads/default-brandings', UploadGlobalBrandingHandler),
    webapp2.Route('/console-api/uploads/default-brandings/<branding_id:[^/]+>', UploadGlobalBrandingHandler),
    webapp2.Route('/console-api/proxy<route:.*>', ProxyHandlerConfigurator),
    webapp2.Route('/console', ConsoleIndexHandler),
    webapp2.Route('/console/<route:.*>', ConsoleIndexHandler),
]
handlers.extend(rest_functions(view, authorized_function=authorize_manager))
handlers.extend(rest_functions(shop_q_and_a, authorized_function=authorize_manager))
handlers.extend(rest_functions(apps, authorized_function=authorize_manager))
handlers.extend(rest_functions(embedded_apps, authorized_function=authorize_manager))
handlers.extend(rest_functions(firebase, authorized_function=authorize_manager))
handlers.extend(rest_functions(payment, authorized_function=authorize_manager))
handlers.extend(rest_functions(rogerthat.bizz.communities.api, authorized_function=authorize_manager))

app = RogerthatWSGIApplication(handlers, uses_session=False, name="main_google_authenticated",
                               google_authenticated=True)
