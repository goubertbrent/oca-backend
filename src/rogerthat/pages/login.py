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

import base64
import json
import logging
import os
import urllib

from google.appengine.ext import webapp, db
from google.appengine.ext.webapp import template

from mcfw.properties import azzert
from rogerthat.bizz import session
from rogerthat.bizz.job import hookup_with_default_services
from rogerthat.bizz.limit import clear_rate_login
from rogerthat.bizz.profile import update_password_hash, create_user_profile
from rogerthat.bizz.registration import get_headers_for_consent, save_tos_consent
from rogerthat.bizz.session import create_session
from rogerthat.bizz.user import calculate_secure_url_digest, update_user_profile_language_from_headers
from rogerthat.consts import DEBUG
from rogerthat.dal.profile import get_service_or_user_profile
from rogerthat.exceptions import ServiceExpiredException
from rogerthat.exceptions.login import AlreadyUsedUrlException, ExpiredUrlException, InvalidUrlException
from rogerthat.models import UserProfile, ServiceProfile
from rogerthat.pages.legal import get_legal_language, get_version_content, DOC_TERMS_SERVICE, get_current_document_version, \
    DOC_TERMS
from rogerthat.rpc import users
from rogerthat.settings import get_server_settings
from rogerthat.templates import get_languages_from_header, JINJA_ENVIRONMENT
from rogerthat.utils import urlencode, now, channel
from rogerthat.utils.cookie import set_cookie
from rogerthat.utils.crypto import decrypt, sha256_hex

_BASE_DIR = os.path.dirname(__file__)


class SessionHandler(webapp.RequestHandler):

    def redirect(self, url, permanent=False):
        return super(SessionHandler, self).redirect(str(url), permanent)

    def start_session(self, user, cont=None):
        try:
            secret, _ = create_session(user)
        except ServiceExpiredException:
            return self.redirect('/service_disabled')
        server_settings = get_server_settings()
        set_cookie(self.response, server_settings.cookieSessionName, secret)
        if not cont:
            cont = self.request.GET.get("continue", "/")
        if cont:
            self.redirect(cont)
        else:
            self.redirect("/")

    def stop_session(self):
        current_session = users.get_current_session()
        session.drop_session(current_session)
        server_settings = get_server_settings()
        set_cookie(self.response, server_settings.cookieSessionName, current_session.parent_session_secret or "")
        self.redirect("/")


class LoginHandler(webapp.RequestHandler):

    def get(self):
        user = users.get_current_user()
        if user:
            self.redirect("/")
        else:
            # Show login.html
            path = os.path.join(_BASE_DIR, 'login.html')
            cont = self.request.GET.get("continue", "/")
            self.response.out.write(template.render(path, {"continue": cont, 'debug': DEBUG}))


class SetPasswordHandler(SessionHandler):

    def return_error(self, reason="Invalid url received."):
        path = os.path.join(_BASE_DIR, 'error.html')
        self.response.out.write(template.render(path, {"reason": reason, "hide_header": True}))

    def parse_data(self, email, data):
        user = users.User(email)
        data = base64.decodestring(data)
        data = decrypt(user, data)
        data = json.loads(data)
        azzert(data["d"] == calculate_secure_url_digest(data))
        return data, user

    def parse_and_validate_data(self, email, data):
        if not email or not data:
            raise InvalidUrlException()

        try:
            data, user = self.parse_data(email, data)
        except UnicodeEncodeError:
            logging.warn("Could not decipher url!\ndata: %s\nemail: %s", data, email, exc_info=True)
            raise InvalidUrlException()
        except:
            logging.exception("Could not decipher url!\ndata: %s\nemail: %s", data, email)
            raise InvalidUrlException()

        now_ = now()
        timestamp = data["t"]
        if not (now_ < timestamp < now_ + 5 * 24 * 3600):
            raise ExpiredUrlException(action=data["a"])

        profile = get_service_or_user_profile(user)
        if profile and profile.lastUsedMgmtTimestamp + 5 * 24 * 3600 > timestamp:
            raise AlreadyUsedUrlException(action=data["a"])

        return data

    def get(self):
        email = self.request.get("email")
        data = self.request.get("data")

        try:
            parsed_data = self.parse_and_validate_data(email, data)
        except ExpiredUrlException as e:
            return self.return_error("The %s link has expired." % e.action)
        except AlreadyUsedUrlException as e:
            return self.return_error("You cannot use the %s link more than once." % e.action)
        except InvalidUrlException:
            return self.return_error()

        path = os.path.join(_BASE_DIR, 'setpassword.html')
        self.response.out.write(template.render(path, {
            'name': parsed_data['n'],
            'hide_header': True,
            'data': data,
            'email': email,
            'action': parsed_data['a']
        }))

    def post(self):
        email = self.request.get("email", None)
        password = self.request.get("password", None)
        data = self.request.get("data", None)

        if not (email and password and data):
            return self.redirect("/")

        try:
            data, user = self.parse_data(email, data)
        except:
            logging.exception("Could not decypher url!")
            return self.redirect("/")

        now_ = now()

        language_header = self.request.headers.get('Accept-Language', None)
        language = get_languages_from_header(language_header)[0] if language_header else None

        passwordHash = sha256_hex(password)
        profile = get_service_or_user_profile(user)
        if not profile:
            profile = create_user_profile(user, data['n'], language)
            update_password_hash(profile, passwordHash, now_)
        else:
            def update():
                p = db.get(profile.key())
                if isinstance(profile, UserProfile) and not p.language:
                    p.language = language
                p.passwordHash = passwordHash
                p.lastUsedMgmtTimestamp = now_
                p.put()
                return p
            profile = db.run_in_transaction(update)

        if isinstance(profile, UserProfile):
            hookup_with_default_services.schedule(user, ipaddress=os.environ.get('HTTP_X_FORWARDED_FOR', None))

        self.start_session(user, data["c"])


class ResetPasswordHandler(webapp.RequestHandler):

    def get(self):
        cont = self.request.GET.get("continue", "/")
        email = self.request.GET.get("email", "")
        path = os.path.join(_BASE_DIR, 'resetpassword.html')
        self.response.out.write(template.render(path, {"continue": cont, "hide_header": True, "email": email}))


class AuthenticationRequiredHandler(webapp.RequestHandler):

    def get(self):
        path = "/login"
        cont = self.request.GET.get("continue", None)
        if cont:
            path += "?" + urlencode((("continue", cont),))
        self.redirect(path)


class TermsAndConditionsHandler(webapp.RequestHandler):

    def get_doc_and_lang(self, user):
        profile = get_service_or_user_profile(user)
        if isinstance(profile, ServiceProfile):
            if profile.solution:
                return None, None
            doc_type = DOC_TERMS_SERVICE
            language = get_legal_language(profile.defaultLanguage)
        else:
            doc_type = DOC_TERMS
            language = get_legal_language(profile.language)
        return doc_type, language

    def get(self):
        user = users.get_current_user()
        doc_type, language = self.get_doc_and_lang(user)
        if not doc_type and not language:
            self.redirect('/')
            return
        version = get_current_document_version(doc_type)
        self.response.out.write(JINJA_ENVIRONMENT.get_template('terms_and_conditions.html').render({
            'user': user,
            'tac': get_version_content(language, doc_type, version),
            'language': language,
            'version': version,
            'logout_url': users.create_logout_url('/'),
        }))

    def post(self):
        user = users.get_current_user()
        if not user:
            self.redirect('/logout')
            return
        doc, lang = self.get_doc_and_lang(user)
        if not doc and not lang:
            self.redirect('/')
            return
        version = long(self.request.get('version')) or get_current_document_version(doc)
        profile = get_service_or_user_profile(user)
        profile.tos_version = version
        profile.put()
        save_tos_consent(user, get_headers_for_consent(self.request), version, None)
        self.redirect('/')


class LogoutHandler(SessionHandler):

    def get(self):
        user = users.get_current_user()
        self.stop_session()
        channel.send_message(user, u'rogerthat.system.logout')

        cont = self.request.get('continue')
        if cont:
            self.redirect('/%s' % cont)


class OfflineDebugLoginHandler(SessionHandler):

    def get(self):
        from google.appengine.api import users as ae_users
        self.start_session(ae_users.get_current_user())


class AutoLogin(webapp.RequestHandler):

    def parse_data(self, email, data):
        user = users.User(email)
        data = base64.decodestring(data)
        data = decrypt(user, data)
        data = json.loads(data)
        azzert(data["d"] == calculate_secure_url_digest(data))
        return data, user

    def get(self):
        email = self.request.get("email", None)
        data = self.request.get("data", None)
        service_identity = self.request.get("si", None)

        user = users.get_current_user()
        if user:
            users.clear_user()
            channel.send_message(user, u'rogerthat.system.logout')

        if not email or not data:
            logging.warn("not al params received for email: %s and data: %s" % (email, data))
            self.redirect("/")
            return

        try:
            data, _ = self.parse_data(email, data)
        except:
            logging.warn("Could not decipher url! email: %s and data: %s" % (email, data), exc_info=True)
            self.redirect("/")
            return

        user = users.User(email)

        profile = get_service_or_user_profile(user)
        if not profile:
            logging.warn("profile not found for email: %s" % email)
            self.redirect("/")
            return
        try:
            secret, _ = create_session(user, service_identity=service_identity)
        except ServiceExpiredException:
            return self.redirect('/service_disabled')
        server_settings = get_server_settings()
        set_cookie(self.response, server_settings.cookieSessionName, secret)

        clear_rate_login(user)
        update_user_profile_language_from_headers(profile, self.response.headers)

        params = self.request.GET
        redirect_url = '/'
        if params:
            params = dict((k, v.decode('utf8')) for k, v in params.iteritems())
            del params['email']
            del params['data']
            if "si" in params:
                del params['si']
            redirect_url = "%s?%s" % (redirect_url, urllib.urlencode(params))
        logging.info("Redirecting to url: %s" % redirect_url)
        self.redirect(redirect_url)
