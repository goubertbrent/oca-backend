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

import solutions.common.jobs.api
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
import solutions.common.integrations.cirklo.api as vouchers_api
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
    ('/common/city-vouchers/export', ExportVoucherHandler),
    ('/common/events/google/oauth2callback', EventsGoogleOauth2callbackHandler),
    ('/common/discussion_groups/(\d+)/pdf', DiscussionGroupsPdfHandler),
    ('/common/city/vouchers/qr/download/(\d+)', CityVouchersDownloadHandler),
    ('/common/city_vouchers/export', CityVoucherExportHandler),
    ('/common/restaurant/menu/export', ExportMenuHandler),
    ('/terms', TermsAndConditionsHandler),
]
modules = [
    solutions.common.jobs.api,
    solutions.common.restapi,
    solutions.common.restapi.services,
    solutions.common.restapi.billing,
    solutions.common.restapi.cityapp,
    solutions.common.restapi.city_vouchers,
    solutions.common.restapi.discussion_groups,
    solutions.common.restapi.forms,
    solutions.common.restapi.hints,
    solutions.common.restapi.locations,
    solutions.common.restapi.loyalty,
    solutions.common.restapi.maps,
    solutions.common.restapi.news,
    solutions.common.restapi.opening_hours,
    solutions.common.restapi.order,
    solutions.common.restapi.participation,
    solutions.common.restapi.payments,
    solutions.common.restapi.pharmacy.order,
    solutions.common.restapi.reservation,
    solutions.common.restapi.qanda,
    solutions.common.restapi.reports,
    solutions.common.restapi.store,
    solutions.common.restapi.settings,
    solutions.common.restapi.statistics,
    vouchers_api,
]
for mod in modules:
    handlers.extend(rest_functions(mod))

app = AuthenticatedRogerthatWSGIApplication(handlers, name="main_authenticated")
