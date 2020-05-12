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

from mcfw.restapi import rest_functions
from rogerthat.bizz.service import branding_editor
from rogerthat.bizz.service.branding_editor.handlers import BrandingEditorPreviewHandler
from rogerthat.handlers.blobstore import CloudStorageBlobstoreHandler
from rogerthat.pages.branding import PostBrandingHandler, OriginalBrandingDownloadHandler
from rogerthat.pages.connect import ConnectHandler
from rogerthat.pages.icons import IconHandler
from rogerthat.pages.login import LogoutHandler, AuthenticationRequiredHandler, TermsAndConditionsHandler
from rogerthat.pages.message import MessageHistoryHandler, PhotoUploadUploadHandler
from rogerthat.pages.profile import GetMyAvatarHandler
from rogerthat.pages.qrtemplates import PostQRTemplateHandler, TemplateExampleHandler
from rogerthat.pages.service_page import ServicePageHandler, ServiceMenuItemBrandingHandler, ServiceAboutPageHandler, \
    EditableTranslationSetExcelDownloadHandler, PostEditableTranslationSetExcelHandler
from rogerthat.pages.service_users import ServiceUsersHandler
from rogerthat.pages.settings import GetGeneralSettings, GetMobileSettings, SettingsSave, EditMobileDescription, \
    DeleteMobile, SettingsStartDebugging, SettingsStopDebugging
from rogerthat.pages.unsubcribe import UnsubscribeHandler
from rogerthat.restapi.service_export import ExportServiceDataHandler, ImportServiceDataHandler
from rogerthat.wsgi import AuthenticatedRogerthatWSGIApplication

handlers = [
    ('/mobi/settings/general', GetGeneralSettings),
    ('/mobi/settings/mobile', GetMobileSettings),
    ('/mobi/settings/save', SettingsSave),
    ('/mobi/settings/start_debugging', SettingsStartDebugging),
    ('/mobi/settings/stop_debugging', SettingsStopDebugging),
    ('/mobi/settings/mobile/editdescription', EditMobileDescription),
    ('/mobi/settings/mobile/delete', DeleteMobile),
    ('/mobi/profile/my_avatar', GetMyAvatarHandler),
    ('/mobi/service/branding/upload', PostBrandingHandler),
    ('/mobi/service/branding/editor/(.*)/(.*)', BrandingEditorPreviewHandler),
    ('/mobi/service/qrtemplate/upload', PostQRTemplateHandler),
    ('/mobi/service/qrtemplate/example', TemplateExampleHandler),
    ('/mobi/service/menu/icons', IconHandler),
    ('/mobi/service/users', ServiceUsersHandler),
    ('/mobi/service/page', ServicePageHandler),
    ('/mobi/service/about', ServiceAboutPageHandler),
    ('/mobi/service/menu/item/branding', ServiceMenuItemBrandingHandler),
    ('/mobi/service/branding/download/(.*)', OriginalBrandingDownloadHandler),
    ('/mobi/service/translations', EditableTranslationSetExcelDownloadHandler),
    ('/mobi/service/translations/upload', PostEditableTranslationSetExcelHandler),
    ('/mobi/message/history', MessageHistoryHandler),
    ('/mobi/message/photo_upload/post', PhotoUploadUploadHandler),
    ('/mobi/message/photo_upload/get/([^/]+)?', CloudStorageBlobstoreHandler),
    ('/mobi/service/export', ExportServiceDataHandler),
    ('/mobi/service/import', ImportServiceDataHandler),
    ('/login_required', AuthenticationRequiredHandler),
    ('/terms-and-conditions', TermsAndConditionsHandler),
    ('/connect/(.*)', ConnectHandler),
    ('/unsubscribeme', UnsubscribeHandler),
    ('/logout', LogoutHandler),
]

handlers.extend(rest_functions(branding_editor.handlers))

app = AuthenticatedRogerthatWSGIApplication(handlers, name="main_authenticated")
