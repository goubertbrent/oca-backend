# -*- coding: utf-8 -*-
# Copyright 2017 GIG Technology NV
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

from add_1_monkey_patches import dummy2
from add_2_zip_imports import dummy
from add_3_solution_handlers import register_solution_callback_api_handlers
from mcfw.restapi import rest_functions
from rogerthat.wsgi import AuthenticatedRogerthatWSGIApplication
from solutions.common.handlers import ImageViewerHandler, SolutionMainBrandingHandler, InvoicePdfHandler, \
    OrderPdfHandler, UploadStaticContentPDFHandler, GetSolutionLogoHandler, GetTmpSolutionImageHandler, \
    UploadSolutionLogoHandler, UploadSolutionAvatarHandler, GetSolutionAvatarHandler, FlowStatisticsExportHandler
from solutions.common.handlers.broadcast import UploadAttachmentHandler
from solutions.common.handlers.city_vouchers import CityVouchersDownloadHandler, CityVoucherExportHandler, \
    ExportVoucherHandler
from solutions.common.handlers.discussion_groups import DiscussionGroupsPdfHandler
from solutions.common.handlers.events import EventsGoogleOauth2callbackHandler
from solutions.common.handlers.loyalty import UploadLoyaltySlideHandler, LoyaltySlidePreviewHandler, \
    LoyaltySlideOverlayHandler, ExportLoyaltyHandler
from solutions.common.handlers.service import LoginAsServiceHandler
import solutions.common.restapi.services
import solutions.common.restapi.billing
import solutions.common.restapi.city_vouchers
import solutions.common.restapi.cityapp
import solutions.common.restapi.discussion_groups
import solutions.common.restapi.hints
import solutions.common.restapi.holiday
import solutions.common.restapi.locations
import solutions.common.restapi.loyalty
import solutions.common.restapi.news
import solutions.common.restapi.order
import solutions.common.restapi.pharmacy.order
import solutions.common.restapi.qanda
import solutions.common.restapi.reservation
import solutions.common.restapi.store
import solutions.common.restapi.statistics
from solutions.djmatic.handlers import DJMaticHomeHandler
import solutions.djmatic.restapi
from solutions.flex.handlers import FlexHomeHandler, FlexLogoutHandler


dummy()
dummy2()
register_solution_callback_api_handlers()

handlers = [
    ('/djmatic/', DJMaticHomeHandler),
    ('/flex/', FlexHomeHandler),
    ('/flex/logout', FlexLogoutHandler),
    ('/common/login_as', LoginAsServiceHandler),
    ('/common/broadcast/attachment/upload', UploadAttachmentHandler),
    ('/common/settings/my_logo', GetSolutionLogoHandler),
    ('/common/settings/tmp_blob', GetTmpSolutionImageHandler),
    ('/common/settings/logo/post', UploadSolutionLogoHandler),
    ('/common/settings/my_avatar', GetSolutionAvatarHandler),
    ('/common/settings/avatar/post', UploadSolutionAvatarHandler),
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
]

handlers.extend(rest_functions(solutions.common.restapi))
handlers.extend(rest_functions(solutions.common.restapi.services))
handlers.extend(rest_functions(solutions.common.restapi.billing))
handlers.extend(rest_functions(solutions.common.restapi.cityapp))
handlers.extend(rest_functions(solutions.common.restapi.city_vouchers))
handlers.extend(rest_functions(solutions.common.restapi.discussion_groups))
handlers.extend(rest_functions(solutions.common.restapi.hints))
handlers.extend(rest_functions(solutions.common.restapi.holiday))
handlers.extend(rest_functions(solutions.common.restapi.locations))
handlers.extend(rest_functions(solutions.common.restapi.loyalty))
handlers.extend(rest_functions(solutions.common.restapi.news))
handlers.extend(rest_functions(solutions.common.restapi.order))
handlers.extend(rest_functions(solutions.common.restapi.pharmacy.order))
handlers.extend(rest_functions(solutions.common.restapi.reservation))
handlers.extend(rest_functions(solutions.common.restapi.qanda))
handlers.extend(rest_functions(solutions.common.restapi.store))
handlers.extend(rest_functions(solutions.common.restapi.statistics))
handlers.extend(rest_functions(solutions.djmatic.restapi))

app = AuthenticatedRogerthatWSGIApplication(handlers, name="main_authenticated")
