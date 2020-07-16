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
import random
import re
import uuid

from google.appengine.ext import webapp, db, deferred
import webapp2

from mcfw.consts import MISSING
from mcfw.properties import azzert
from mcfw.rpc import parse_complex_value, serialize_complex_value, returns
from mcfw.utils import chunks
from rogerthat.bizz.authentication import decode_jwt_cached
from rogerthat.bizz.friends import get_service_profile_via_user_code, REGISTRATION_ORIGIN_QR, ACCEPT_ID, \
    ACCEPT_AND_CONNECT_ID, REGISTRATION_ORIGIN_OAUTH, register_response_receiver
from rogerthat.bizz.oauth import get_oauth_access_token
from rogerthat.bizz.profile import get_profile_for_facebook_user, FailedToBuildFacebookProfileException, \
    create_user_profile
from rogerthat.bizz.registration import register_mobile, get_device_names_of_my_mobiles, get_device_name, \
    get_mobile_type, get_or_insert_installation, send_installation_progress_callback, \
    save_tos_consent, save_push_notifications_consent, get_headers_for_consent
from rogerthat.dal import parent_key
from rogerthat.dal.app import get_app_by_id, get_app_settings
from rogerthat.dal.profile import get_user_profile, get_deactivated_user_profile, get_service_or_user_profile, \
    get_service_profile
from rogerthat.dal.registration import get_last_but_one_registration
from rogerthat.dal.roles import get_service_admins
from rogerthat.dal.service import get_service_interaction_def
from rogerthat.models import Installation, InstallationLog, Registration, App, ServiceProfile, \
    UserProfile, Profile, InstallationStatus
from rogerthat.pages.legal import DOC_TERMS, get_current_document_version
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException, logServiceError
from rogerthat.settings import get_server_settings
from rogerthat.templates import render
from rogerthat.to.friends import RegistrationResultTO, RegistrationResultRolesTO
from rogerthat.to.oauth import OauthAccessTokenTO
from rogerthat.to.registration import MobileInfoTO, DeprecatedMobileInfoTO, OAuthInfoTO
from rogerthat.to.service import UserDetailsTO
from rogerthat.translations import localize, DEFAULT_LANGUAGE
from rogerthat.utils import get_country_code_by_ipaddress, countries, now, send_mail, bizz_check
from rogerthat.utils.app import create_app_user, get_human_user_from_app_user, create_app_user_by_email, \
    get_app_id_from_app_user
from rogerthat.utils.crypto import sha256_hex
from rogerthat.utils.languages import get_iso_lang
from rogerthat.utils.service import create_service_identity_user, \
    get_identity_from_service_identity_user, get_service_identity_tuple
from rogerthat.utils.transactions import run_in_transaction


def _log_installation_country(installation_key, ipaddress):
    country_code = get_country_code_by_ipaddress(ipaddress)
    country_name = countries.name_for_code(country_code)
    log = InstallationLog(parent=installation_key, timestamp=now(), description="Installed from country: %s (%s)" %
                                                                                (country_name, country_code))
    db.put(log)
    installation = Installation.get(installation_key)
    send_installation_progress_callback(installation, [log])


def _verify_app_id(app_id):
    app = get_app_by_id(app_id)
    if app:
        return app
    logging.warn("Could not find app with id: %s", app_id)
    return None


def verify_app(response, language, app_id):
    # type: (webapp2.Response, str) -> App
    app = _verify_app_id(app_id)
    error_msg = None
    if not app:
        response.set_status(502)
        error_msg = 'App %s not found' % app_id
    elif app.disabled:
        response.set_status(502)
        error_msg = localize(language, 'cannot_register_app_disabled', app=app.name)
    if error_msg:
        response.out.write(json.dumps({'result': error_msg}))
    else:
        return app


class RegisterInstallIdentifierHandler(webapp.RequestHandler):

    def post(self):
        logging.debug(self.request.POST)
        version = self.request.get("version", None)
        install_id = self.request.get("install_id", None)
        platform = self.request.get("platform", None)
        language = _get_language_from_request(self.request)
        use_xmpp_kick_channel = self.request.get('use_xmpp_kick', 'true') == 'true'
        use_firebase_kick_channel = self.request.get('use_firebase_kick', 'false') == 'true'
        ipaddress = os.environ.get('HTTP_X_FORWARDED_FOR', None)

        if None in (version, install_id, platform):
            logging.error("Insufficient data")
            return

        app_id = self.request.get("app_id", App.APP_ID_ROGERTHAT)
        if not verify_app(self.response, language, app_id):
            return

        now_ = now()
        mobile_type = get_mobile_type(platform, use_xmpp_kick_channel, use_firebase_kick_channel)
        installation = get_or_insert_installation(install_id, version, mobile_type, now_, app_id, language)

        if not ipaddress:
            log = InstallationLog(parent=installation, timestamp=now_,
                                  description="Received installation registration request without IP address!")
        else:
            log = InstallationLog(parent=installation, timestamp=now_,
                                  description="Resolving country from IP address: %s" % ipaddress)
            deferred.defer(_log_installation_country, installation.key(), ipaddress)
        db.put(log)
        self.response.headers['Content-Type'] = 'text/json'

        self.response.out.write(json.dumps({'result': "success"}))
        send_installation_progress_callback(installation, [log])


class InitiateRegistrationViaEmailVerificationHandler(webapp.RequestHandler):

    def post(self):
        logging.debug(self.request.POST)
        version = self.request.get("version", 0)
        email = self.request.get("email", None)
        registration_time = self.request.get("registration_time", None)
        device_id = self.request.get("device_id", None)
        registration_id = self.request.get("registration_id", None)
        request_signature = self.request.get("request_signature", None)
        install_id = self.request.get("install_id", None)
        language = _get_language_from_request(self.request)
        request_id = self.request.get("request_id", None)
        app_id = self.request.get("app_id", App.APP_ID_ROGERTHAT)
        platform = self.request.get('platform')
        use_xmpp_kick_channel = self.request.get('use_xmpp_kick', 'true') == 'true'
        use_firebase_kick_channel = self.request.get('use_firebase_kick', 'false') == 'true'
        anonymous_account = self.request.get("anonymous_account", None)

        server_settings = get_server_settings()

        # Verify request signature.
        calculated_signature = sha256_hex(version + email + " " + registration_time + " " + device_id + " " +
                                          registration_id + " " + base64.b64decode(
                                              server_settings.registrationEmailSignature.encode("utf8")))
        if request_signature.upper() != calculated_signature.upper():
            self.response.set_status(501)
            return

        # Validate input.
        version = int(version)
        azzert(version > 0 and version <= 3)
        registration_time = int(registration_time)
        # XXX: validating the email would be an improvement
        app = verify_app(self.response, language, app_id)
        if not app:
            return

        if " " in email:
            self.response.set_status(502)
            result = localize(language, "Spaces are not allowed in an e-mail address")
            self.response.out.write(json.dumps(dict(result=result)))
            return

        # User regex
        self.response.headers['Content-Type'] = 'text/json'
        if app.user_regex:
            app_user = create_app_user_by_email(email, app_id)
            existing_profile = get_service_or_user_profile(app_user)
            if existing_profile and isinstance(existing_profile, UserProfile):
                pass  # Existing users are allowed to register
            else:
                # Check app.user_regex
                regexes = app.user_regex.splitlines()
                for regex in regexes:
                    if re.match(regex, email):
                        break
                else:
                    self.response.set_status(502)
                    result = localize(language, "You can not register with this e-mail address")
                    self.response.out.write(json.dumps(dict(result=result)))
                    return

        @db.non_transactional
        def get_service_admins_non_transactional(app_user):
            return list(get_service_admins(app_user))

        def trans():
            db_puts = []

            mobile_type = get_mobile_type(platform, use_xmpp_kick_channel, use_firebase_kick_channel)
            installation = get_or_insert_installation(install_id, version, mobile_type, registration_time, app_id,
                                                      language, status=InstallationStatus.IN_PROGRESS)
            app_user = create_app_user(users.User(email), app_id)
            registration = None
            if version >= 2:
                registration = Registration.get_by_key_name(registration_id, parent_key(app_user))
                if registration and registration.request_id == request_id:
                    log = InstallationLog(parent=registration.installation, timestamp=now(),
                                          pin=registration.pin,
                                          description="Received a HTTP request retry for 'request pin'. Not sending a new mail.")
                    db_puts.append(log)
                    db.put(db_puts)
                    send_installation_progress_callback(installation, [log])
                    return

            rogerthat_profile = get_service_or_user_profile(users.User(email))
            server_settings = get_server_settings()
            if rogerthat_profile and isinstance(rogerthat_profile, ServiceProfile):
                # some guy tries to register a mobile on a service account ?!?
                warning = InstallationLog(parent=installation, timestamp=now(),
                                          description="Warning somebody tries to register a mobile with the email address of service account %s" % email)
                db_puts.append(warning)
                raise Exception('Trying to register using a service email: %s', email)
            else:
                profile = get_user_profile(app_user)
                if profile:
                    name = profile.name
                else:
                    deactivated_profile = get_deactivated_user_profile(app_user)
                    name = deactivated_profile.name if deactivated_profile else None
                if not registration:
                    registration = Registration(parent=parent_key(app_user), key_name=registration_id)
                registration.timestamp = registration_time
                registration.device_id = device_id
                for pin, static_email in chunks(server_settings.staticPinCodes, 2):
                    if email == static_email and len(pin) == 4:
                        registration.pin = int(pin)
                        break
                else:
                    registration.pin = random.randint(1000, 9999)

                registration.timesleft = 3
                registration.installation = installation
                registration.request_id = request_id
                registration.language = language
                db_puts.append(registration)

                if anonymous_account:
                    db_puts.append(InstallationLog(parent=registration.installation,
                                                   timestamp=now(),
                                                   description="Anonymous user is initiating the registration"))

                db_puts.append(InstallationLog(parent=registration.installation,
                                               timestamp=now(),
                                               pin=registration.pin,
                                               description="%s requested pin" % email))

                # Send email with pin.
                app = get_app_by_id(app_id)
                variables = dict(pin=registration.pin, name=name, app=app)
                body = render("activation_code_email", [language], variables)
                html = render("activation_code_email_html", [language], variables)

                from_ = server_settings.senderEmail if app.type == App.APP_TYPE_ROGERTHAT else (
                    "%s <%s>" % (app.name, app.dashboard_email_address))
                subject = localize(language, "%(app_name)s mobile registration", app_name=app.name)
                send_mail(from_, email, subject, body, html=html)

                i2 = InstallationLog(parent=registration.installation, timestamp=now(), pin=registration.pin,
                                     description="Sent email to %s with pin %s" % (email, registration.pin))
                db_puts.append(i2)

            db.put(db_puts)
            send_installation_progress_callback(installation, [m for m in db_puts if isinstance(m, InstallationLog)])

        run_in_transaction(trans, xg=True)


class VerifyEmailWithPinHandler(webapp.RequestHandler):

    def post(self):
        logging.debug(self.request.POST)
        version = self.request.get("version", 0)
        email = self.request.get("email", None)
        tos_age = self.request.get("tos_age", None)
        push_notifications_enabled = self.request.get("push_notifications_enabled", None)
        registration_time = self.request.get("registration_time", None)
        device_id = self.request.get("device_id", None)
        registration_id = self.request.get("registration_id", None)
        pin_code = self.request.get("pin_code", None)
        pin_signature = self.request.get("pin_signature", None)
        request_id = self.request.get('request_id', None)
        language = _get_language_from_request(self.request)
        app_id = self.request.get("app_id", App.APP_ID_ROGERTHAT)
        use_xmpp_kick_channel = self.request.get('use_xmpp_kick', 'true') == 'true'
        gcm_registration_id = self.request.get('GCM_registration_id', '')
        firebase_registration_id = self.request.get('firebase_registration_id', '')
        unique_device_id = self.request.get("unique_device_id", None)
        anonymous_account = self.request.get('anonymous_account')

        server_settings = get_server_settings()

        # Verify request signature.
        calculated_signature = sha256_hex(version + " " + email + " " + registration_time + " " + device_id + " " +
                                          registration_id + " " + pin_code + base64.b64decode(
                                              server_settings.registrationPinSignature.encode("utf8")))
        if pin_signature.upper() != calculated_signature.upper():
            self.response.set_status(500)
            return

        # Validate input.
        version = int(version)
        azzert(version > 0 and version <= 3)
        registration_time = int(registration_time)
        pin_code = int(pin_code)
        # XXX: validating the email address would be an improvement.

        app = verify_app(self.response, language, app_id)
        if not app:
            return

        human_user = users.User(email)
        app_user = create_app_user(human_user, app_id)
        registration = Registration.get_by_key_name(registration_id, parent_key(app_user))

        logging.info(
            "Pin received for email %s and device_id [%s] of type %s and len %d - expecting device_id [%s] of type %s and len %d"
            % (email, device_id, type(device_id), len(device_id), registration.device_id, type(registration.device_id),
               len(registration.device_id)))

        azzert(registration)
        azzert(registration.timestamp == registration_time)
        azzert(registration.device_id == device_id)
        azzert(registration.timesleft > 0)

        is_retry = version >= 2 and request_id == registration.request_id
        registration.request_id = request_id
        installation = registration.installation

        # Handle request
        self.response.headers['Content-Type'] = 'text/json'
        if pin_code != registration.pin:
            # Allow pin code from previous registration
            previous_registration = get_last_but_one_registration(installation)
            if not previous_registration or pin_code != previous_registration.pin or previous_registration.parent_key() != registration.parent_key():
                if not is_retry:
                    registration.timesleft -= 1
                    installation_log = InstallationLog(parent=installation, timestamp=now(),
                                                       pin=pin_code, description="Entered wrong pin: %04d" % pin_code)
                else:
                    installation_log = InstallationLog(parent=installation, timestamp=now(),
                                                       pin=pin_code,
                                                       description="Received wrong pin again in HTTP request retry. Not seeing this as a failed attempt (already processed it).")
                db.put([registration, installation_log])

                send_installation_progress_callback(installation, [installation_log])
                self.response.out.write(json.dumps(dict(result="fail", attempts_left=registration.timesleft)))
                return

        installation_log = InstallationLog(parent=installation, timestamp=now(), pin=pin_code,
                                           description="Entered correct pin: %04d%s" % (
                                               pin_code, " (in HTTP request retry)" if is_retry else ""))

        if version >= 3:
            device_names = get_device_names_of_my_mobiles(human_user, language, app_id, unique_device_id)
            if device_names:
                registration.device_names = device_names
                installation_log_devices = InstallationLog(parent=registration.installation,
                                                           timestamp=now(),
                                                           registration=registration,
                                                           description="Current device names: %s" % device_names)
                db_puts = [registration, installation_log, installation_log_devices]
                db.put(db_puts)
                send_installation_progress_callback(installation,
                                                    [m for m in db_puts if isinstance(m, InstallationLog)])
                self.response.out.write(json.dumps(dict(result="success",
                                                        has_devices=True,
                                                        device_names=device_names)))
                return

        tos_version = None
        if tos_age:
            tos_version = get_current_document_version(DOC_TERMS)
        consent_push_notifications_shown = push_notifications_enabled is not None
        account, registration.mobile, age_and_gender_set = register_mobile(human_user,
                                                                           app_id=app_id,
                                                                           use_xmpp_kick_channel=use_xmpp_kick_channel,
                                                                           gcm_registration_id=gcm_registration_id,
                                                                           language=registration.language,
                                                                           firebase_registration_id=firebase_registration_id,
                                                                           tos_version=tos_version,
                                                                           consent_push_notifications_shown=consent_push_notifications_shown,
                                                                           anonymous_account=anonymous_account)

        headers = get_headers_for_consent(self.request)
        if tos_version:
            deferred.defer(save_tos_consent, app_user, headers, tos_version, tos_age)
        if consent_push_notifications_shown:
            deferred.defer(save_push_notifications_consent, app_user, headers, push_notifications_enabled)

        if installation:
            installation.mobile = registration.mobile
            installation.profile = get_user_profile(app_user)
            db.put([installation, registration, installation_log])
            send_installation_progress_callback(installation, [installation_log])
        else:
            registration.put()

        self.response.out.write(json.dumps(dict(result="success",
                                                has_devices=False,
                                                account=account.to_dict(),
                                                age_and_gender_set=age_and_gender_set)))


class CommonRegistrationHandler(webapp.RequestHandler):
    ANONYMOUS = False
    TYPE = 'COMMON'

    def _validate_signature(self, signature, version, install_id, registration_time, device_id, registration_id):
        raise NotImplementedError()

    def _get_app_user(self, language, app_id):
        raise NotImplementedError()

    def _get_first_name(self):
        return None

    def _get_last_name(self):
        return None

    def _put_and_callback(self):
        db.put(self.to_put)
        send_installation_progress_callback(
            self.installation, [m for m in self.to_put if isinstance(m, InstallationLog)])

    def post(self):
        logging.debug(self.request.POST)

        self.server_settings = get_server_settings()
        self.to_put = []
        self.installation = None

        version = self.request.get("version", None)
        install_id = self.request.get("install_id", None)
        registration_time = self.request.get("registration_time", None)
        device_id = self.request.get("device_id", None)
        registration_id = self.request.get("registration_id", None)
        tos_age = self.request.get("tos_age", None)
        push_notifications_enabled = self.request.get("push_notifications_enabled", None)
        signature = self.request.get("signature", None)
        language = _get_language_from_request(self.request)
        app_id = self.request.get("app_id", App.APP_ID_ROGERTHAT)
        use_xmpp_kick_channel = self.request.get('use_xmpp_kick', 'true') == 'true'
        use_firebase_kick_channel = self.request.get('use_firebase_kick', 'false') == 'true'
        gcm_registration_id = self.request.get('GCM_registration_id', '')
        firebase_registration_id = self.request.get('firebase_registration_id', '')
        unique_device_id = self.request.get('unique_device_id', None)
        platform = self.request.get('platform')

        if not self._validate_signature(signature, version, install_id, registration_time, device_id, registration_id):
            logging.error("Invalid request signature.")
            self.response.set_status(500)
            return

        # Validate input.
        version = int(version)
        azzert(version > 0 and version <= 3)

        app = verify_app(self.response, language, app_id)
        if not app:
            return
        mobile_type = get_mobile_type(platform, use_xmpp_kick_channel, use_firebase_kick_channel)
        installation = get_or_insert_installation(install_id, version, mobile_type, registration_time, app_id, language,
                                                  status=InstallationStatus.IN_PROGRESS)
        self.to_put.append(InstallationLog(
            parent=installation,
            timestamp=now(),
            description="Creating %s profile & validating registration request" % self.TYPE))

        try:
            app_user = self._get_app_user(language, app_id)
        except BusinessException as e:
            self.response.set_status(500)
            if e.message:
                self.response.out.write(json.dumps(dict(error=e.message)))
            return

        human_user = get_human_user_from_app_user(app_user)

        # Create registration entry.
        self.response.headers['Content-Type'] = 'text/json'
        registration = Registration(parent=parent_key(app_user), key_name=registration_id)
        registration.timestamp = int(registration_time)
        registration.device_id = device_id
        registration.pin = -1
        registration.timesleft = -1
        registration.installation = installation
        registration.language = language

        self.to_put.append(InstallationLog(
            parent=installation,
            timestamp=now(),
            description="%s profile created & registration request validated." % self.TYPE))
        self.to_put.append(registration)

        if version >= 3 and not self.ANONYMOUS:
            device_names = get_device_names_of_my_mobiles(human_user, language, app_id, unique_device_id)
            if device_names:
                registration.device_names = device_names
                self.to_put.append(InstallationLog(parent=installation,
                                                   timestamp=now(),
                                                   description="Current device names: %s" % device_names))
                self._put_and_callback()
                self.response.out.write(json.dumps(dict(has_devices=True,
                                                        email=human_user.email(),
                                                        device_names=device_names)))
                return

        try:
            tos_version = None
            if tos_age:
                tos_version = get_current_document_version(DOC_TERMS)
            consent_push_notifications_shown = push_notifications_enabled is not None
            first_name = self._get_first_name()
            last_name = self._get_last_name()
            account, registration.mobile, age_and_gender_set = register_mobile(human_user,
                                                                               first_name=first_name,
                                                                               last_name=last_name,
                                                                               app_id=app_id,
                                                                               use_xmpp_kick_channel=use_xmpp_kick_channel,
                                                                               gcm_registration_id=gcm_registration_id,
                                                                               language=registration.language,
                                                                               firebase_registration_id=firebase_registration_id,
                                                                               tos_version=tos_version,
                                                                               consent_push_notifications_shown=consent_push_notifications_shown)

            if self.ANONYMOUS:
                age_and_gender_set = True
            elif self.TYPE == RegisterMobileViaFacebookHandler.TYPE:
                age_and_gender_set = True

            app_user = create_app_user(human_user, app_id)
            headers = get_headers_for_consent(self.request)
            if tos_version:
                deferred.defer(save_tos_consent, app_user, headers, tos_version, tos_age)
            if consent_push_notifications_shown:
                deferred.defer(save_push_notifications_consent, app_user, headers, push_notifications_enabled)

        except Exception:
            logging.exception('Failed to execute register_mobile')
            self._put_and_callback()
            raise

        installation.profile = get_user_profile(app_user)
        installation.mobile = registration.mobile
        self.to_put.append(installation)
        self._put_and_callback()
        self.response.out.write(json.dumps(dict(has_devices=False,
                                                account=account.to_dict(),
                                                email=human_user.email(),
                                                age_and_gender_set=age_and_gender_set)))


class AnonymousRegistrationHandler(CommonRegistrationHandler):
    TYPE = 'ANONYMOUS'
    ANONYMOUS = True

    def _get_app_user(self, language, app_id):
        while True:
            app_user = create_app_user(users.User('u-%s@rogerth.at' % uuid.uuid4().hex), app_id)
            # assuring there's no existing UserProfile with this guid
            logging.debug('Checking if user email %s is still free.', app_user.email())
            if not get_user_profile(app_user):
                return app_user

    def _validate_signature(self, signature, version, install_id, registration_time, device_id, registration_id):
        s = version + "  " + registration_time + " " + device_id + " " + registration_id + " " + \
            base64.b64decode(self.server_settings.registrationMainSignature.encode("utf8"))
        calculated_signature = sha256_hex(s)
        return signature.upper() == calculated_signature.upper()


class RegisterMobileViaFacebookHandler(CommonRegistrationHandler):
    TYPE = 'FACEBOOK'
    ANONYMOUS = False

    def _get_app_user(self, language, app_id):
        try:
            profile = get_profile_for_facebook_user(self.access_token, None, True, language=language, app_id=app_id)
            return profile.user
        except FailedToBuildFacebookProfileException as fe:
            logging.warn("Failed to build facebook profile", exc_info=True)
            self.to_put.append(InstallationLog(parent=self.installation, timestamp=now(),
                                               description="ERROR: Failed to build facebook profile"))
            self._put_and_callback()
            raise BusinessException(fe.message)
        except Exception:
            logging.error("Failed to build facebook profile.", exc_info=True)
            self.to_put.append(InstallationLog(parent=self.installation, timestamp=now(),
                                               description="ERROR: Failed to build facebook profile"))
            self._put_and_callback()
            self.response.set_status(500)
            raise BusinessException()

    def _validate_signature(self, signature, version, install_id, registration_time, device_id, registration_id):
        calculated_signature = sha256_hex(version + " " + install_id + " " + registration_time + " " + device_id + " " +
                                          registration_id + " " + self.access_token + base64.b64decode(
                                              self.server_settings.registrationMainSignature.encode("utf8")))
        return signature.upper() == calculated_signature.upper()

    def post(self):
        self.access_token = self.request.get("access_token", None)
        super(RegisterMobileViaFacebookHandler, self).post()


class RegisterMobileViaAppleHandler(CommonRegistrationHandler):
    TYPE = 'APPLE'
    ANONYMOUS = False

    def _get_app_user(self, language, app_id):
        try:
            if self.apple_email:
                return create_app_user(users.User(self.apple_email), app_id)
            return create_app_user(users.User('%s@privaterelay.appleid.com' % self.apple_user_id), app_id)
        except Exception:
            logging.error("Failed to build apple profile.", exc_info=True)
            self.to_put.append(InstallationLog(parent=self.installation, timestamp=now(),
                                               description="ERROR: Failed to build apple profile"))
            self._put_and_callback()
            self.response.set_status(500)
            raise BusinessException()

    def _validate_signature(self, signature, version, install_id, registration_time, device_id, registration_id):
        calculated_signature = sha256_hex(version + " " + install_id + " " + registration_time + " " + device_id + " " +
                                          registration_id + " " + self.apple_user_id + base64.b64decode(
                                              self.server_settings.registrationMainSignature.encode("utf8")))
        return signature.upper() == calculated_signature.upper()

    def _get_first_name(self):
        return self.apple_given_name

    def _get_last_name(self):
        return self.apple_family_name

    def post(self):
        self.apple_user_id = self.request.get("user", None)
        self.apple_family_name = self.request.get("full_name.family_name", None)
        self.apple_given_name = self.request.get("full_name.given_name", None)
        self.apple_email = self.request.get("email", None)
        super(RegisterMobileViaAppleHandler, self).post()


class RegisterMobileViaQRHandler(webapp.RequestHandler):

    def post(self):
        logging.debug(self.request.POST)
        language = _get_language_from_request(self.request)

        if self.request.get("qr_url", None):
            self.handle_post_qr_url(language)
        else:
            self.handle_post_qr_content(language)

    def handle_post_qr_url(self, language):
        from rogerthat.pages.shortner import get_short_url_by_code
        version = self.request.get("version", None)
        install_id = self.request.get("install_id", None)
        registration_time = self.request.get("registration_time", None)
        device_id = self.request.get("device_id", None)
        registration_id = self.request.get("registration_id", None)
        qr_url = self.request.get("qr_url", None)
        signature = self.request.get("signature", None)
        app_id = self.request.get("app_id", App.APP_ID_ROGERTHAT)
        use_xmpp_kick_channel = self.request.get('use_xmpp_kick', 'true') == 'true'
        use_firebase_kick_channel = self.request.get('use_firebase_kick', 'false') == 'true'
        gcm_registration_id = self.request.get('GCM_registration_id', '')
        firebase_registration_id = self.request.get('firebase_registration_id', '')
        platform = self.request.get('platform')

        server_settings = get_server_settings()

        calculated_signature = sha256_hex(version + " " + install_id + " " + registration_time + " " + device_id + " " +
                                          registration_id + " " + qr_url + base64.b64decode(
                                              server_settings.registrationMainSignature.encode("utf8")))

        to_put = []
        try:
            if signature.upper() != calculated_signature.upper():
                logging.error("Invalid request signature.")
                self.response.set_status(500)
                return

            # Validate input.
            version = int(version)
            azzert(version > 0 and version <= 3)

            app = verify_app(self.response, language, app_id)
            if not app:
                return
            bizz_check(install_id and qr_url, u"Could not validate QR code")

            mobile_type = get_mobile_type(platform, use_xmpp_kick_channel, use_firebase_kick_channel)
            installation = get_or_insert_installation(install_id, version, mobile_type, registration_time, app_id,
                                                      language, status=InstallationStatus.IN_PROGRESS)

            to_put.append(InstallationLog(parent=installation, timestamp=now(),
                                          description="Creating qr based profile & validating registration request. QR url: %s" % qr_url))

            m = re.match('(.*)/(M|S)/(.*)', qr_url)
            bizz_check(m, u"Could not validate QR code")
            entry_point = m.group(2)
            code = m.group(3)

            bizz_check(entry_point == "S", u"Could not validate QR code")

            su = get_short_url_by_code(code)
            bizz_check(su, u"Could not validate QR code")

            logging.debug("register_via_qr qr_url: %s", qr_url)
            logging.debug("register_via_qr su.full: %s", su.full)

            match = re.match("^/q/s/(.+)/(\\d+)$", su.full)
            bizz_check(match, u"Could not validate QR code")

            user_code = match.group(1)
            service_profile = get_service_profile_via_user_code(user_code)
            bizz_check(service_profile, u"Could not validate QR code")

            service_user = service_profile.user

            sid = int(match.group(2))
            service_interaction_def = get_service_interaction_def(service_user, int(sid))
            service_identity_user = create_service_identity_user(service_user, service_interaction_def.service_identity)
            service_identity = get_identity_from_service_identity_user(service_identity_user)

            logging.debug("register_via_qr service_identity_user: %s", service_identity_user)

            human_user = users.User(u"user%s@rogerth.at" % uuid.uuid4().get_hex())
            app_user = create_app_user(human_user, app_id)

            validate_user_registration(
                installation, app_user, language, service_identity_user, service_profile, service_identity,
                REGISTRATION_ORIGIN_QR)
            installation.qr_url = su.full[4:]
            to_put.append(installation)

            # Create registration entry.
            self.response.headers['Content-Type'] = 'text/json'
            registration = Registration(parent=parent_key(app_user), key_name=registration_id)
            registration.timestamp = int(registration_time)
            registration.device_id = device_id
            registration.pin = -1
            registration.timesleft = -1
            registration.installation = installation
            registration.language = language
            registration.put()
            account, registration.mobile, age_and_gender_set = register_mobile(human_user,
                                                                               app_id=app_id,
                                                                               use_xmpp_kick_channel=use_xmpp_kick_channel,
                                                                               gcm_registration_id=gcm_registration_id,
                                                                               language=registration.language,
                                                                               firebase_registration_id=firebase_registration_id)
            to_put.append(InstallationLog(parent=installation, timestamp=now(),
                                          description="Profile created & registration request validated."))
            installation.profile = get_user_profile(app_user)
            installation.mobile = registration.mobile
            to_put.append(registration)
            db.put(to_put)
            send_installation_progress_callback(installation, [m for m in to_put if isinstance(m, InstallationLog)])
            self.response.out.write(json.dumps(dict(account=account.to_dict(),
                                                    email=human_user.email(),
                                                    age_and_gender_set=age_and_gender_set)))
        except BusinessException as be:
            logging.debug("BusinessException during via QR-url handler %s", be)
            self.response.set_status(500)
            return

    def handle_post_qr_content(self, language):
        # todo too much copy paste from OauthRegistrationHandler
        version = self.request.get("version", None)
        install_id = self.request.get("install_id", None)
        registration_time = self.request.get("registration_time", None)
        device_id = self.request.get("device_id", None)
        registration_id = self.request.get("registration_id", None)
        qr_type = self.request.get("qr_type", None)
        qr_content = self.request.get("qr_content", None)
        signature = self.request.get("signature", None)
        app_id = self.request.get("app_id", App.APP_ID_ROGERTHAT)
        use_xmpp_kick_channel = self.request.get('use_xmpp_kick', 'true') == 'true'
        use_firebase_kick_channel = self.request.get('use_firebase_kick', 'false') == 'true'
        gcm_registration_id = self.request.get('GCM_registration_id', '')
        firebase_registration_id = self.request.get('firebase_registration_id', '')
        platform = self.request.get('platform')

        server_settings = get_server_settings()

        calculated_signature = sha256_hex(version + " " + install_id + " " + registration_time + " " + device_id + " " +
                                          registration_id + " " + qr_type + "-" + qr_content + base64.b64decode(
                                              server_settings.registrationMainSignature.encode("utf8")))

        if signature.upper() != calculated_signature.upper():
            logging.error("Invalid request signature.")
            self.response.set_status(500)
            return

        app = verify_app(self.response, language, app_id)
        if not app:
            return
        bizz_check(install_id and qr_type and qr_content, u"Could not validate QR code")

        to_put = []
        try:
            oauth = get_app_settings(app_id).oauth
            if not oauth.service_identity_email:
                logging.error("oauth.service_identity_email is not set.")
                self.response.set_status(500)
                return

            if qr_type == "jwt":
                # For now we only support itsyou.online
                decoded_jwt = decode_jwt_cached(qr_content, False)
                username = decoded_jwt.get('username', None)
                bizz_check(username, u"Service did not provide a username")
            else:
                logging.error("Unknown qr_type: %s" % qr_type)
                self.response.set_status(500)
                return

            mobile_type = get_mobile_type(platform, use_xmpp_kick_channel, use_firebase_kick_channel)
            installation = get_or_insert_installation(install_id, version, mobile_type, registration_time, app_id,
                                                      language, status=InstallationStatus.IN_PROGRESS)

            to_put.append(InstallationLog(parent=installation, timestamp=now(),
                                          description="Creating qr based profile & validating registration request. Language: %s, QR type: %s" % (
                                              language, qr_type)))

            service_identity_user = users.User(oauth.service_identity_email)
            service_user, service_identity = get_service_identity_tuple(service_identity_user)
            svc_profile = get_service_profile(service_user)

            profile, app_user = _get_existing_user_profile(username, app_id, oauth.domain)

            data = json.dumps(dict(qr_type=qr_type, qr_content=qr_content))
            registration_result = validate_user_registration(installation, app_user, language, service_identity_user,
                                                             svc_profile, service_identity, REGISTRATION_ORIGIN_QR,
                                                             data)
            if not profile:
                _create_user_profile(app_user, username, registration_result)

            human_user = get_human_user_from_app_user(app_user)

            registration = Registration(parent=parent_key(app_user), key_name=registration_id)
            registration.timestamp = int(registration_time)
            registration.device_id = device_id
            registration.pin = -1
            registration.timesleft = -1
            registration.installation = installation
            registration.language = language
            to_put.append(registration)

            account, registration.mobile, age_and_gender_set = register_mobile(human_user,
                                                                               app_id=app_id,
                                                                               use_xmpp_kick_channel=use_xmpp_kick_channel,
                                                                               gcm_registration_id=gcm_registration_id,
                                                                               language=registration.language,
                                                                               firebase_registration_id=firebase_registration_id)

            to_put.append(InstallationLog(parent=installation, timestamp=now(),
                                          description="Profile created & registration request validated."))
            installation.profile = get_user_profile(app_user),
            installation.mobile = registration.mobile
            to_put.append(installation)
            db.put(to_put)
            send_installation_progress_callback(installation, [m for m in to_put if isinstance(m, InstallationLog)])
            response = dict(account=account.to_dict(),
                            email=human_user.email(),
                            age_and_gender_set=age_and_gender_set)

        except BusinessException as be:
            logging.debug("BusinessException during via QR-content handler %s", be)
            self.response.set_status(500)
            return

        self.response.out.write(json.dumps(response))


# This handler is called to unregister another logged in device
class RegisterDeviceHandler(webapp.RequestHandler):

    def post(self):
        logging.debug(self.request.POST)
        version = self.request.get("version", 0)
        email = self.request.get("email", None)
        tos_age = self.request.get("tos_age", None)
        push_notifications_enabled = self.request.get("push_notifications_enabled", None)
        registration_time = self.request.get("registration_time", None)
        device_id = self.request.get("device_id", None)
        registration_id = self.request.get("registration_id", None)
        signature = self.request.get("signature", None)
        app_id = self.request.get("app_id", App.APP_ID_ROGERTHAT)
        use_xmpp_kick_channel = self.request.get('use_xmpp_kick', 'true') == 'true'
        gcm_registration_id = self.request.get('GCM_registration_id', '')
        firebase_registration_id = self.request.get('firebase_registration_id', '')
        hardware_model = self.request.get("hardware_model", None)
        sim_carrier_name = self.request.get("sim_carrier_name", None)
        anonymous_account = self.request.get("anonymous_account", None)
        language = _get_language_from_request(self.request)

        server_settings = get_server_settings()

        # Verify request signature.
        calculated_signature = sha256_hex(version + " " + email + " " + registration_time + " " + device_id + " " +
                                          registration_id + " " + base64.b64decode(
                                              server_settings.registrationMainSignature.encode("utf8")))

        if signature.upper() != calculated_signature.upper():
            self.response.set_status(500)
            return

        # Validate input.
        version = int(version)
        azzert(version == 3)
        registration_time = int(registration_time)

        app = verify_app(self.response, language, app_id)
        if not app:
            return

        human_user = users.User(email)
        app_user = create_app_user(human_user, app_id)
        registration = Registration.get_by_key_name(registration_id, parent_key(app_user))

        azzert(registration)
        azzert(registration.timestamp == registration_time)
        azzert(registration.device_id == device_id)
        if not registration.device_names:
            logging.error('There were no devices on the registration object o.O\n%s', db.to_dict(registration))

        device_name = get_device_name(hardware_model, sim_carrier_name)
        installation_log = InstallationLog(parent=registration.installation, timestamp=now(),
                                           description="Continued with registering device, the following device '%s' is registered and %s are unregistered" % (
                                               device_name, registration.device_names))

        tos_version = None
        if tos_age:
            tos_version = get_current_document_version(DOC_TERMS)
        consent_push_notifications_shown = push_notifications_enabled is not None
        account, registration.mobile, age_and_gender_set = register_mobile(human_user,
                                                                           app_id=app_id,
                                                                           use_xmpp_kick_channel=use_xmpp_kick_channel,
                                                                           gcm_registration_id=gcm_registration_id,
                                                                           language=registration.language,
                                                                           firebase_registration_id=firebase_registration_id,
                                                                           hardware_model=hardware_model,
                                                                           sim_carrier_name=sim_carrier_name,
                                                                           tos_version=tos_version,
                                                                           consent_push_notifications_shown=consent_push_notifications_shown,
                                                                           anonymous_account=anonymous_account)

        headers = get_headers_for_consent(self.request)
        if tos_version:
            deferred.defer(save_tos_consent, app_user, headers, tos_version, tos_age)
        if consent_push_notifications_shown:
            deferred.defer(save_push_notifications_consent, app_user, headers, push_notifications_enabled)

        installation_log.mobile = registration.mobile
        installation_log.profile = get_user_profile(app_user)
        db.put([registration, installation_log])
        send_installation_progress_callback(registration.installation, [installation_log])
        self.response.out.write(json.dumps(dict(account=account.to_dict(),
                                                age_and_gender_set=age_and_gender_set)))


class FinishRegistrationHandler(webapp.RequestHandler):

    def post(self):
        logging.debug(self.request.POST)
        from rogerthat.bizz.registration import finish_registration
        account = self.request.POST['account']
        password = self.request.POST['password']
        app_id = self.request.POST.get("app_id", App.APP_ID_ROGERTHAT)
        anonymous_account = self.request.POST.get('anonymous_account')
        language = _get_language_from_request(self.request)

        if not users.set_json_rpc_user(account, password, True):
            self.response.set_status(401, "could not authenticate")
            return

        app = verify_app(self.response, language, app_id)
        if not app:
            return

        mobileInfoJSON = json.loads(self.request.POST["mobileInfo"])
        if mobileInfoJSON.get('version', 1) == 1:
            oldMobileInfo = parse_complex_value(DeprecatedMobileInfoTO, mobileInfoJSON, False)
            mobileInfo = MobileInfoTO.fromDeprecatedMobileInfoTO(oldMobileInfo)
        else:
            mobileInfo = parse_complex_value(MobileInfoTO, mobileInfoJSON, False)

        invitor_code = self.request.POST.get('invitor_code')
        invitor_secret = self.request.POST.get('invitor_secret')

        ipaddress = os.environ.get('HTTP_X_FORWARDED_FOR', None)
        if ipaddress:
            ipaddress = unicode(ipaddress)

        finish_registration(account, mobileInfo, invitor_code, invitor_secret, ipaddress,
                            anonymous_account=anonymous_account)
        r = json.dumps({})
        self.response.out.write(r)


class LogRegistrationStepHandler(webapp.RequestHandler):
    STEPS = {'1': "'Create account' button pressed",
             '1a': "'Location usage' continue pressed",
             '1b': "'Notification usage' continue pressed",
             '1c': "'Terms' agree pressed",
             '2a': "'Use Facebook' button pressed",
             '2b': "'Use e-mail' button pressed",
             '2c': "'Use apple' button pressed"}

    def post(self):
        logging.debug(self.request.POST)
        install_id = self.request.get("install_id", None)
        step = self.request.get("step", None)
        azzert(step is not None, "step is a required argument")
        if step == "log_url":
            url = self.request.get("url", None)
            azzert(url is not None, "url is a required argument")
            count = int(self.request.get("count", 0))
            msg = "%s/ Navigated to %s" % (count, url)
        else:
            msg = LogRegistrationStepHandler.STEPS.get(step, "Unknown step: %s" % step)
        installation = Installation.get_by_key_name(install_id) if install_id else None
        if installation:
            installation.status = InstallationStatus.IN_PROGRESS
            log = InstallationLog(parent=installation, timestamp=now(), description=msg)
            db.put([installation, log])
            send_installation_progress_callback(installation, [log])


class InitServiceAppHandler(webapp2.RequestHandler):

    def post(self):
        logging.debug(self.request.POST)
        version = self.request.get("version", None)
        install_id = self.request.get("install_id", None)
        registration_time = self.request.get("registration_time", None)
        device_id = self.request.get("device_id", None)
        registration_id = self.request.get("registration_id", None)
        signature = self.request.get("signature", None)
        language = _get_language_from_request(self.request)
        app_id = self.request.get("app_id", App.APP_ID_ROGERTHAT)
        use_xmpp_kick_channel = self.request.get('use_xmpp_kick', 'true') == 'true'
        gcm_registration_id = self.request.get('GCM_registration_id', '')
        firebase_registration_id = self.request.get('firebase_registration_id', '')
        ysaaa_guid = self.request.get("service", None)

        app = verify_app(self.response, language, app_id)
        if not app:
            return

        if not ysaaa_guid:
            logging.warn('Missing YSAAA guid!\nPOST params: %s', self.request.POST)
            return self.abort(401)

        server_settings = get_server_settings()

        calculated_signature = sha256_hex(version + " " + install_id + " " + registration_time + " " + device_id + " " +
                                          registration_id + " " + ysaaa_guid + base64.b64decode(
                                              server_settings.registrationMainSignature.encode("utf8")))
        if signature.upper() != calculated_signature.upper():
            logging.error("Invalid request signature.")
            self.response.set_status(500)
            return

        for ysaaa_hash, _ in chunks(server_settings.ysaaaMapping, 2):
            if ysaaa_guid == ysaaa_hash:
                break
        else:
            azzert(False, u"ysaaa registration received but not found mapping")

        user_id = str(uuid.uuid4()).replace("-", "")
        user = users.User("%s@ysaaa.rogerth.at" % user_id)
        account, _, age_and_gender_set = register_mobile(user,
                                                         name=user_id,
                                                         app_id=app_id,
                                                         use_xmpp_kick_channel=use_xmpp_kick_channel,
                                                         gcm_registration_id=gcm_registration_id,
                                                         language=language,
                                                         ysaaa=True,
                                                         firebase_registration_id=firebase_registration_id)

        self.response.out.write(json.dumps(dict(result="success",
                                                account=account.to_dict(),
                                                email=user.email(),
                                                age_and_gender_set=age_and_gender_set)))


class GetRegistrationOauthInfoHandler(webapp2.RequestHandler):

    def post(self):
        logging.debug(self.request.POST)
        version = self.request.get("version", None)
        install_id = self.request.get("install_id", None)
        registration_time = self.request.get("registration_time", None)
        device_id = self.request.get("device_id", None)
        registration_id = self.request.get("registration_id", None)
        signature = self.request.get("signature", None)
        app_id = self.request.get("app_id", App.APP_ID_ROGERTHAT)
        platform = self.request.get('platform')
        use_xmpp_kick_channel = self.request.get('use_xmpp_kick', 'true') == 'true'
        use_firebase_kick_channel = self.request.get('use_firebase_kick', 'false') == 'true'
        language = _get_language_from_request(self.request)

        server_settings = get_server_settings()

        email_sig = base64.b64decode(server_settings.registrationMainSignature.encode('utf8'))
        calculated_signature = sha256_hex(version + " " + install_id + " " + registration_time + " " + device_id + " " +
                                          registration_id + " " + 'oauth' + email_sig)

        if signature.upper() != calculated_signature.upper():
            logging.error("Invalid request signature.")
            self.response.set_status(400)
            return

        app = verify_app(self.response, language, app_id)
        if not app:
            return

        mobile_type = get_mobile_type(platform, use_xmpp_kick_channel, use_firebase_kick_channel)
        installation = get_or_insert_installation(install_id, version, mobile_type, registration_time, app_id,
                                                  language, status=InstallationStatus.IN_PROGRESS)
        log = InstallationLog(parent=installation, timestamp=now(), description='Oauth registration started')
        log.put()
        send_installation_progress_callback(installation, [log])
        oauth = get_app_settings(app_id).oauth
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(serialize_complex_value(OAuthInfoTO.create(oauth.authorize_url, oauth.scopes,
                                                                                      install_id, oauth.client_id),
                                                                   OAuthInfoTO, False)))


@returns((unicode, RegistrationResultTO))
def validate_user_registration(installation, app_user, language, service_identity_user, service_profile,
                               service_identity, origin, data=None):
    from rogerthat.service.api import friends as service_api_friends
    from rogerthat.bizz.profile import _create_new_avatar

    avatar, _ = _create_new_avatar(app_user)
    user_profile = UserProfile(parent=parent_key(app_user), key_name=app_user.email())
    user_profile.name = None
    user_profile.language = language
    user_profile.avatarId = avatar.key().id()
    user_profile.app_id = get_app_id_from_app_user(app_user)
    user_details = [UserDetailsTO.fromUserProfile(user_profile)]

    r = service_api_friends.register(register_response_receiver,
                                     logServiceError,
                                     service_profile,
                                     service_identity=service_identity,
                                     user_details=user_details,
                                     origin=origin,
                                     data=data,
                                     PERFORM_CALLBACK_SYNCHRONOUS=True)

    if isinstance(r, unicode):
        installation.service_callback_result = r
    elif isinstance(r, RegistrationResultTO):
        installation.service_callback_result = r.result
        installation.auto_connected_services = r.auto_connected_services
        installation.roles = json.dumps(serialize_complex_value(r.roles, RegistrationResultRolesTO, True))
    else:
        bizz_check(False, u"Service denied your install, could not parse result.")

    bizz_check(installation.service_callback_result == ACCEPT_ID or installation.service_callback_result ==
               ACCEPT_AND_CONNECT_ID, u"Service denied your install")

    installation.service_identity_user = service_identity_user
    return r


class OauthRegistrationHandler(webapp2.RequestHandler):

    def post(self):
        logging.debug(self.request.POST)
        version = self.request.get("version", None)
        install_id = self.request.get("install_id", None)
        registration_time = self.request.get("registration_time", None)
        device_id = self.request.get("device_id", None)
        registration_id = self.request.get("registration_id", None)
        request_signature = self.request.get("signature", None)
        app_id = self.request.get("app_id", App.APP_ID_ROGERTHAT)
        code = self.request.get('code')
        state = self.request.get('state')
        tos_age = self.request.get("tos_age", None)
        push_notifications_enabled = self.request.get("push_notifications_enabled", None)
        use_xmpp_kick_channel = self.request.get('use_xmpp_kick', 'true') == 'true'
        use_firebase_kick_channel = self.request.get('use_firebase_kick', 'false') == 'true'
        gcm_registration_id = self.request.get('GCM_registration_id', '')
        firebase_registration_id = self.request.get('firebase_registration_id', '')
        unique_device_id = self.request.get("unique_device_id", None)
        language = _get_language_from_request(self.request)
        platform = self.request.get('platform')

        email_sig = base64.b64decode(get_server_settings().registrationMainSignature.encode('utf8'))
        calculated_signature = sha256_hex(version + " " + install_id + " " + registration_time + " " + device_id + " " +
                                          registration_id + " " + code + state + email_sig)
        if request_signature.upper() != calculated_signature.upper():
            self.abort(400)
            return

        # Validate input.
        version = int(version)
        azzert(version > 0 and version <= 3)

        app = verify_app(self.response, language, app_id)
        if not app:
            return

        self.response.headers['Content-Type'] = 'application/json'
        to_put = []
        installation = None
        try:
            oauth = get_app_settings(app_id).oauth
            access_token = get_oauth_access_token(oauth.token_url, oauth.client_id, oauth.secret, code,
                                                  'oauth-%s://x-callback-url' % app_id, state)
            if access_token.info is not MISSING and access_token.info.username is not MISSING:
                username = access_token.info.username
            else:
                # todo: get oauth identity
                # username = get_oauth_identity(oauth.identity_url, access_token, variable_type)
                bizz_check(False, u"Service did not provide a username")

            mobile_type = get_mobile_type(platform, use_xmpp_kick_channel, use_firebase_kick_channel)
            installation = get_or_insert_installation(install_id, version, mobile_type, registration_time, app_id,
                                                      language, status=InstallationStatus.IN_PROGRESS)

            to_put.append(InstallationLog(parent=installation, timestamp=now(),
                                          description='Oauth registration authorized with state %s' % state))

            profile, app_user = _get_existing_user_profile(username, app_id, oauth.domain)
            registration_result = None
            if oauth.service_identity_email:
                service_identity_user = users.User(oauth.service_identity_email)
                service_user, service_identity = get_service_identity_tuple(service_identity_user)
                svc_profile = get_service_profile(service_user)

                data = json.dumps(
                    dict(state=state,
                         result=serialize_complex_value(access_token, OauthAccessTokenTO, False, skip_missing=True)))
                registration_result = validate_user_registration(installation, app_user, language,
                                                                 service_identity_user, svc_profile, service_identity,
                                                                 REGISTRATION_ORIGIN_OAUTH, data)
                installation.oauth_state = state
                to_put.append(installation)
            if not profile:
                profile = _create_user_profile(app_user, username, registration_result)

            human_user = get_human_user_from_app_user(app_user)

            registration = Registration(parent=parent_key(app_user), key_name=registration_id)
            registration.timestamp = int(registration_time)
            registration.device_id = device_id
            registration.pin = -1
            registration.timesleft = -1
            registration.installation = installation
            registration.language = language
            to_put.append(registration)
            to_put.append(InstallationLog(parent=installation, timestamp=now(),
                                          description="Profile created & registration request validated."))

            if version >= 3:
                device_names = get_device_names_of_my_mobiles(human_user, language, app_id, unique_device_id)
                if device_names:
                    registration.device_names = device_names
                    to_put.append(InstallationLog(parent=registration.installation,
                                                  timestamp=now(),
                                                  registration=registration,
                                                  description="Current device names: '%s'" % device_names))
                    db.put(to_put)
                    send_installation_progress_callback(installation,
                                                        [m for m in to_put if isinstance(m, InstallationLog)])
                    self.response.out.write(json.dumps(dict(has_devices=True,
                                                            email=human_user.email(),
                                                            device_names=device_names)))
                    return

            tos_version = None
            if tos_age:
                tos_version = get_current_document_version(DOC_TERMS)
            consent_push_notifications_shown = push_notifications_enabled is not None
            account, registration.mobile, age_and_gender_set = register_mobile(human_user, app_id=app_id,
                                                                               use_xmpp_kick_channel=use_xmpp_kick_channel,
                                                                               gcm_registration_id=gcm_registration_id,
                                                                               language=registration.language,
                                                                               firebase_registration_id=firebase_registration_id,
                                                                               tos_version=tos_version,
                                                                               consent_push_notifications_shown=consent_push_notifications_shown)

            headers = get_headers_for_consent(self.request)
            if tos_version:
                deferred.defer(save_tos_consent, app_user, headers, tos_version, tos_age)
            if consent_push_notifications_shown:
                deferred.defer(save_push_notifications_consent, app_user, headers, push_notifications_enabled)

            to_put.append(InstallationLog(parent=installation, timestamp=now(),
                                          description="Profile created & registration request validated."))
            installation.mobile = registration.mobile
            installation.profile = profile
            to_put.append(installation)
            db.put(to_put)
            send_installation_progress_callback(installation, [m for m in to_put if isinstance(m, InstallationLog)])
            response = dict(has_devices=False,
                            account=account.to_dict(),
                            email=human_user.email(),
                            age_and_gender_set=age_and_gender_set)
        except BusinessException as exception:
            logging.warning("Failed to finish OauthRegistrationHandler", exc_info=True)
            db.put(to_put)
            if installation:
                send_installation_progress_callback(installation, [m for m in to_put if isinstance(m, InstallationLog)])
            self.response.set_status(500)
            self.response.out.write(json.dumps(dict(error=exception.message)))
            return
        self.response.out.write(json.dumps(response))


def _get_existing_user_profile(username, app_id, oauth_domain):
    # Existing users may have a profile with unhashed username in their email, ensure their old profile is returned
    email_unhashed = u'%s@%s' % (username, oauth_domain)
    email_hashed = u'%s@%s' % (sha256_hex(username), oauth_domain)
    app_user_unhashed = create_app_user(users.User(email_unhashed), app_id)
    app_user_hashed = create_app_user(users.User(email_hashed), app_id)
    profile_1, profile_2 = db.get([Profile.createKey(app_user_unhashed), Profile.createKey(app_user_hashed)])
    if profile_1:
        return profile_1, app_user_unhashed
    return profile_2, app_user_hashed


def _create_user_profile(app_user, username, registration_result):
    name = username
    avatar = None
    if isinstance(registration_result, RegistrationResultTO):
        if registration_result.user_details is not MISSING:
            name = MISSING.default(registration_result.user_details.name, username)
            avatar = MISSING.default(registration_result.user_details.avatar, None)
    return create_user_profile(app_user, name, image=avatar)


def _get_language_from_request(request):
    # type: (webapp2.Request) -> unicode
    country = request.get('country', None)
    language = request.get('language', None)
    if language is None:
        language = DEFAULT_LANGUAGE
    if '-' in language:
        language = get_iso_lang(language.lower())
    elif language and country:
        language = '%s_%s' % (language, country)
    return language
