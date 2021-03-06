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

from google.appengine.api import app_identity
import webapp2

from mcfw.restapi import rest_functions, GenericRESTRequestHandler
from rogerthat.bizz.jobs import worker_callbacks as jobs_worker_callbacks
from rogerthat.consts import DEBUG
from rogerthat.handlers.acm import ACMOpenIdLoginHandler, ACMOpenIdLogoutHandler,\
    ACMOpenIdAuthorizedCallbackHandler, ACMOpenIdLoggedOutCallbackHandler,\
    ACMOpenIdTokenHandler
from rogerthat.handlers.apple import AppleAppSiteAssociationHandler
from rogerthat.handlers.itsme import ItsmeAuthorizeHandler, ItsmeLoginHandler, ItsmeAuthorizedHandler, ItsmeJWKsHandler
from rogerthat.pages import ViewImageHandler
from rogerthat.pages.account import AccountLogoutHandler, AccountDeleteHandler, \
    AccountDataDownloadHandler, AccountConsentHandler
from rogerthat.pages.admin.apps import UploadAppAppleCertsHandler
from rogerthat.pages.app import AppUrlHandler
from rogerthat.pages.branding import BrandingDownloadHandler, BrandingHandler
from rogerthat.pages.fb_user import FacebookDeleteUserHandler
from rogerthat.pages.firebase_handlers import FirebaseTokenHandler
from rogerthat.pages.icons import LibraryIconHandler
from rogerthat.pages.install import InstallationRequestHandler
from rogerthat.pages.invite import InviteQRCodeRequestHandler, InviteUserRequestHandler
from rogerthat.pages.js_embedding import JSEmbeddingDownloadHandler
from rogerthat.pages.legal import LegalHandler
from rogerthat.pages.logging_page import LogExceptionHandler
from rogerthat.pages.login import LoginHandler, AuthenticationRequiredHandler, \
    SetPasswordHandler, ResetPasswordHandler, AutoLogin
from rogerthat.pages.main import MainPage, RobotsTxt, CrossDomainDotXml
from rogerthat.pages.mdp import InitMyDigiPassSessionHandler, AuthorizedMyDigiPassHandler
from rogerthat.pages.news import ViewNewsImageHandler, NewsSaveReadItems
from rogerthat.pages.payment import PaymentCallbackHandler, PaymentLoginAppHandler, PaymentLoginRedirectHandler
from rogerthat.pages.photo import ServiceDownloadPhotoHandler
from rogerthat.pages.profile import GetAvatarHandler, GetCachedAvatarHandler
from rogerthat.pages.qrinstall import QRInstallRequestHandler
from rogerthat.pages.register_mobile import FinishRegistrationHandler, \
    InitiateRegistrationViaEmailVerificationHandler, VerifyEmailWithPinHandler, RegisterInstallIdentifierHandler, \
    RegisterMobileViaFacebookHandler, LogRegistrationStepHandler, InitServiceAppHandler, RegisterMobileViaQRHandler, \
    RegisterDeviceHandler, AnonymousRegistrationHandler, RegisterMobileViaAppleHandler, RegistrationCommunityHandler,\
    RegisterMobileViaAuthHandler
from rogerthat.pages.service_disabled import ServiceDisabledHandler
from rogerthat.pages.service_interact import ServiceInteractRequestHandler, ServiceInteractQRCodeRequestHandler
from rogerthat.pages.service_map import ServiceMapHandler
from rogerthat.pages.service_page import GetServiceAppHandler
from rogerthat.pages.settings import ForwardLog, DebugLog
from rogerthat.pages.shortner import ShortUrlHandler
from rogerthat.pages.unsubscribe_reminder_service import UnsubscribeReminderHandler, UnsubscribeDeactivateHandler
from rogerthat.restapi import user, srv, service_map, news, logger, firebase, build_api
from rogerthat.restapi.admin import ApplePushFeedbackHandler, ServerTimeHandler, ApplePushCertificateDownloadHandler
from rogerthat.rpc.http import JSONRPCRequestHandler, UserAuthenticationHandler, \
    InstantJSONRPCRequestHandler
from rogerthat.rpc.service import ServiceApiHandler, CallbackResponseReceiver
from rogerthat.service.api import XMLSchemaHandler
import rogerthat.web_client.api.app
import rogerthat.web_client.api.news
from rogerthat.web_client.pages.news import NewsPageHandler
from rogerthat.wsgi import RogerthatWSGIApplication
from rogerthat_service_api_calls import register_all_service_api_calls


def authorize_internal_request():
    # Authorizes requests made by the application on a different 'service' (<service>-dot-<application_id>.appspot.com)
    if DEBUG:
        return True
    allowed_app_ids = [app_identity.get_application_id()]
    request = GenericRESTRequestHandler.getCurrentRequest()
    incoming_app_id = request.headers.get('X-Appengine-Inbound-Appid', None)
    if incoming_app_id and incoming_app_id in allowed_app_ids:
        return True
    return False

handlers = [
    ('/', MainPage),
    ('/robots.txt', RobotsTxt),
    ('/crossdomain.xml', CrossDomainDotXml),
    ('/legal', LegalHandler),
    ('/login', LoginHandler),
    ('/login_required', AuthenticationRequiredHandler),
    ('/unauthenticated/mobi/registration/init_via_email', InitiateRegistrationViaEmailVerificationHandler),
    ('/unauthenticated/mobi/registration/register_install', RegisterInstallIdentifierHandler),
    ('/unauthenticated/mobi/registration/verify_email', VerifyEmailWithPinHandler),
    ('/unauthenticated/mobi/registration/register_facebook', RegisterMobileViaFacebookHandler),
    ('/unauthenticated/mobi/registration/register_qr', RegisterMobileViaQRHandler),
    ('/unauthenticated/mobi/registration/register_device', RegisterDeviceHandler),
    ('/unauthenticated/mobi/registration/register_anonymous', AnonymousRegistrationHandler),
    ('/unauthenticated/mobi/registration/register_apple', RegisterMobileViaAppleHandler),
    ('/unauthenticated/mobi/registration/register_auth', RegisterMobileViaAuthHandler),
    ('/unauthenticated/mobi/registration/finish', FinishRegistrationHandler),
    ('/unauthenticated/mobi/registration/log_registration_step', LogRegistrationStepHandler),
    ('/unauthenticated/mobi/registration/init_service_app', InitServiceAppHandler),
    ('/unauthenticated/mobi/registration/register_community', RegistrationCommunityHandler),
    ('/unauthenticated/mobi/cached/avatar/(.*)', GetCachedAvatarHandler),
    ('/unauthenticated/mobi/avatar/(.*)', GetAvatarHandler),
    ('/unauthenticated/mobi/branding/(.*)', BrandingDownloadHandler),
    ('/unauthenticated/qrinstall', QRInstallRequestHandler),
    ('/unauthenticated/mobi/service/photo/download/(.*)', ServiceDownloadPhotoHandler),
    ('/unauthenticated/mobi/logging/exception', LogExceptionHandler),
    ('/unauthenticated/mobi/apps/upload_cert', UploadAppAppleCertsHandler),
    ('/unauthenticated/forward_log', ForwardLog),
    ('/unauthenticated/debug_log', DebugLog),
    ('/unauthenticated/service-map', ServiceMapHandler),
    ('/unauthenticated/service-app', GetServiceAppHandler),
    ('/json-rpc', JSONRPCRequestHandler),
    ('/json-rpc/instant', InstantJSONRPCRequestHandler),
    ('/auth', UserAuthenticationHandler),
    ('/api/1', ServiceApiHandler),
    ('/api/1/MessageFlow.xsd', XMLSchemaHandler),
    ('/branding/([^/]+)/(.*)', BrandingHandler),
    ('/invite', InviteQRCodeRequestHandler),
    ('/q/i(.*)', InviteUserRequestHandler),
    ('/si/(.*)/(.*)', ServiceInteractQRCodeRequestHandler),
    ('/q/s/(.*)/(.*)', ServiceInteractRequestHandler),
    ('/(M|S)/(.*)', ShortUrlHandler),
    ('/A/(.*)', AppUrlHandler),
    ('/setpassword', SetPasswordHandler),
    ('/resetpassword', ResetPasswordHandler),
    ('/install/?', InstallationRequestHandler),
    webapp2.Route('/install/<app_id:[^/]+>', InstallationRequestHandler),
    ('/api/1/callback', CallbackResponseReceiver),
    ('/api/1/apple_feedback', ApplePushFeedbackHandler),
    ('/api/1/apple_certs', ApplePushCertificateDownloadHandler),
    ('/api/1/servertime', ServerTimeHandler),
    ('/unsubscribe_reminder', UnsubscribeReminderHandler),
    ('/unsubscribe_deactivate', UnsubscribeDeactivateHandler),
    ('/auto_login', AutoLogin),
    ('/mobi/js_embedding/(.*)', JSEmbeddingDownloadHandler),
    ('/mobi/rest/mdp/session/init', InitMyDigiPassSessionHandler),
    ('/mobi/rest/mdp/session/authorized', AuthorizedMyDigiPassHandler),
    ('/mobi/rest/account/logout', AccountLogoutHandler),
    ('/mobi/rest/account/delete', AccountDeleteHandler),
    ('/mobi/rest/account/data_download', AccountDataDownloadHandler),
    ('/mobi/rest/account/consent', AccountConsentHandler),
    ('/mobi/service/menu/icons/lib/(.*)', LibraryIconHandler),
    ('/service_disabled', ServiceDisabledHandler),
    ('/unauthenticated/news/image/(.*)', ViewNewsImageHandler),
    ('/unauthenticated/image/(.*)', ViewImageHandler),
    ('/unauthenticated/facebook/user/delete', FacebookDeleteUserHandler),
    ('/rest/news/stats/read', NewsSaveReadItems),
    ('/payments/callbacks/([^/]+)/(.*)', PaymentCallbackHandler),
    ('/payments/login/([^/]+)/redirect', PaymentLoginRedirectHandler),
    ('/payments/login/app', PaymentLoginAppHandler),
    ('/apple-app-site-association', AppleAppSiteAssociationHandler),
    ('/.well-known/apple-app-site-association', AppleAppSiteAssociationHandler),
    webapp2.Route('/firebase/token', FirebaseTokenHandler),
    webapp2.Route('/oauth/itsme/authorize', ItsmeAuthorizeHandler),
    webapp2.Route('/oauth/itsme/login', ItsmeLoginHandler, 'itsme_login'),
    webapp2.Route('/oauth/itsme/authorized', ItsmeAuthorizedHandler, 'itsme_authorized'),
    webapp2.Route('/oauth/itsme/jwks.json', ItsmeJWKsHandler),
    webapp2.Route('/oauth/itsme/<app_id:[^/]+>/jwks.json', ItsmeJWKsHandler),
    webapp2.Route('/web/<application_identifier:[^/]+>/news/id/<news_id:\d+>', NewsPageHandler, name='news-item'),
    webapp2.Route('/auth/openid/v1/acm/login', ACMOpenIdLoginHandler),
    webapp2.Route('/auth/openid/v1/acm/logout', ACMOpenIdLogoutHandler),
    webapp2.Route('/auth/openid/v1/acm/token', ACMOpenIdTokenHandler),
    webapp2.Route('/auth/openid/v1/acm/authorized', ACMOpenIdAuthorizedCallbackHandler),
    webapp2.Route('/auth/openid/v1/acm/logged-out', ACMOpenIdLoggedOutCallbackHandler),
]

handlers.extend(rest_functions(user))
handlers.extend(rest_functions(srv))
handlers.extend(rest_functions(news))
handlers.extend(rest_functions(service_map))
handlers.extend(rest_functions(logger))
handlers.extend(rest_functions(firebase))
handlers.extend(rest_functions(rogerthat.web_client.api.app))
handlers.extend(rest_functions(rogerthat.web_client.api.news))
handlers.extend(rest_functions(build_api))
handlers.extend(rest_functions(jobs_worker_callbacks, authorized_function=authorize_internal_request))

register_all_service_api_calls()

app = RogerthatWSGIApplication(handlers, name="main_unauthenticated")
