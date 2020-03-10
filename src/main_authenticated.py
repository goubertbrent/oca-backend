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

import solutions.common.restapi.billing
import solutions.common.restapi.city_vouchers
import solutions.common.restapi.cityapp
import solutions.common.restapi.discussion_groups
import solutions.common.restapi.forms
import solutions.common.restapi.hints
import solutions.common.restapi.locations
import solutions.common.restapi.loyalty
import solutions.common.restapi.maps
import solutions.common.restapi.news
import solutions.common.restapi.opening_hours
import solutions.common.restapi.order
import solutions.common.restapi.participation
import solutions.common.restapi.payments
import solutions.common.restapi.pharmacy.order
import solutions.common.restapi.qanda
import solutions.common.restapi.reports
import solutions.common.restapi.reservation
import solutions.common.restapi.services
import solutions.common.restapi.settings
import solutions.common.restapi.statistics
import solutions.common.restapi.store
from mcfw.restapi import rest_functions
from rogerthat.wsgi import AuthenticatedRogerthatWSGIApplication
from solutions.common.handlers import ImageViewerHandler, SolutionMainBrandingHandler, InvoicePdfHandler, \
    OrderPdfHandler, UploadStaticContentPDFHandler, FlowStatisticsExportHandler
from solutions.common.handlers.city_vouchers import CityVouchersDownloadHandler, CityVoucherExportHandler, \
    ExportVoucherHandler
from solutions.common.handlers.discussion_groups import DiscussionGroupsPdfHandler
from solutions.common.handlers.events import EventsGoogleOauth2callbackHandler
from solutions.common.handlers.loyalty import UploadLoyaltySlideHandler, LoyaltySlidePreviewHandler, \
    LoyaltySlideOverlayHandler, ExportLoyaltyHandler
from solutions.common.handlers.menu import ExportMenuHandler
from solutions.common.handlers.service import LoginAsServiceHandler
from solutions.flex.handlers import FlexHomeHandler, FlexLogoutHandler, TermsAndConditionsHandler

handlers = [
    ('/flex/', FlexHomeHandler),
    ('/flex/logout', FlexLogoutHandler),
    ('/common/login_as', LoginAsServiceHandler),
    ('/common/image_viewer', ImageViewerHandler),
    ('/common/main_branding/(.*)', SolutionMainBrandingHandler),
    ('/common/order/pdf', OrderPdfHandler),
    ('/common/invoice/pdf', InvoicePdfHandler),
    ('/common/static_content/pdf/post', UploadStaticContentPDFHandler),
    ('/common/loyalty/slide/upload', UploadLoyaltySlideHandler),
    ('/common/loyalty/slide/preview', LoyaltySlidePreviewHandler),
    ('/common/loyalty/slide/overlay', LoyaltySlideOverlayHandler),
    ('/common/statistics/flows/export', FlowStatisticsExportHandler),
    ('/common/loyalty/export', ExportLoyaltyHandler),
    ('/common/vouchers/export', ExportVoucherHandler),
    ('/common/events/google/oauth2callback', EventsGoogleOauth2callbackHandler),
    ('/common/discussion_groups/(\d+)/pdf', DiscussionGroupsPdfHandler),
    ('/common/city/vouchers/qr/download/(\d+)', CityVouchersDownloadHandler),
    ('/common/city_vouchers/export', CityVoucherExportHandler),
    ('/common/restaurant/menu/export', ExportMenuHandler),
    ('/terms', TermsAndConditionsHandler),
]

handlers.extend(rest_functions(solutions.common.restapi))
handlers.extend(rest_functions(solutions.common.restapi.services))
handlers.extend(rest_functions(solutions.common.restapi.billing))
handlers.extend(rest_functions(solutions.common.restapi.cityapp))
handlers.extend(rest_functions(solutions.common.restapi.city_vouchers))
handlers.extend(rest_functions(solutions.common.restapi.discussion_groups))
handlers.extend(rest_functions(solutions.common.restapi.forms))
handlers.extend(rest_functions(solutions.common.restapi.hints))
handlers.extend(rest_functions(solutions.common.restapi.locations))
handlers.extend(rest_functions(solutions.common.restapi.loyalty))
handlers.extend(rest_functions(solutions.common.restapi.maps))
handlers.extend(rest_functions(solutions.common.restapi.news))
handlers.extend(rest_functions(solutions.common.restapi.opening_hours))
handlers.extend(rest_functions(solutions.common.restapi.order))
handlers.extend(rest_functions(solutions.common.restapi.participation))
handlers.extend(rest_functions(solutions.common.restapi.payments))
handlers.extend(rest_functions(solutions.common.restapi.pharmacy.order))
handlers.extend(rest_functions(solutions.common.restapi.reservation))
handlers.extend(rest_functions(solutions.common.restapi.qanda))
handlers.extend(rest_functions(solutions.common.restapi.reports))
handlers.extend(rest_functions(solutions.common.restapi.store))
handlers.extend(rest_functions(solutions.common.restapi.settings))
handlers.extend(rest_functions(solutions.common.restapi.statistics))

app = AuthenticatedRogerthatWSGIApplication(handlers, name="main_authenticated")
