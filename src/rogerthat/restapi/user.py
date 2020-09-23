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
from datetime import datetime
import json
import logging
import os
import re
import urllib

from dateutil.relativedelta import relativedelta
from google.appengine.ext import deferred

from mcfw.cache import cached
from mcfw.exceptions import HttpNotFoundException
from mcfw.properties import azzert
from mcfw.restapi import GenericRESTRequestHandler, rest
from mcfw.rpc import returns, arguments
from rogerthat import utils
from rogerthat.bizz.limit import rate_signup_reset_password, rate_login, clear_rate_login
from rogerthat.bizz.rtemail import EMAIL_REGEX
from rogerthat.bizz.session import create_session
from rogerthat.bizz.user import calculate_secure_url_digest, update_user_profile_language_from_headers, \
    unsubscribe_from_reminder_email, delete_account
from rogerthat.consts import SESSION_TIMEOUT, DEBUG
from rogerthat.dal import app
from rogerthat.dal.mobile import get_mobile_by_account
from rogerthat.dal.profile import get_profile_info, get_service_or_user_profile, get_deactivated_user_profile, \
    get_user_profile
from rogerthat.exceptions import ServiceExpiredException
from rogerthat.models import ActivationLog, App, CurrentlyForwardingLogs, FriendServiceIdentityConnection, \
    ServiceIdentity, UserContext, UserProfileInfo, UserAddressType,\
    UserContextScope
from rogerthat.rpc import users
from rogerthat.rpc.models import Mobile
from rogerthat.settings import get_server_settings
from rogerthat.templates import get_languages_from_request, JINJA_ENVIRONMENT, render
from rogerthat.to.statistics import UserStatisticsTO
from rogerthat.to.system import ProfileAddressTO, ProfilePhoneNumberTO
from rogerthat.translations import DEFAULT_LANGUAGE, localize
from rogerthat.utils import now, is_clean_app_user_email, send_mail, get_server_url
from rogerthat.utils.app import create_app_user_by_email, \
    get_human_user_from_app_user, sanitize_app_user
from rogerthat.utils.cookie import set_cookie
from rogerthat.utils.crypto import encrypt, sha256_hex, decrypt


SIGNUP_SUCCESS = 1
SIGNUP_INVALID_EMAIL = 2
SIGNUP_INVALID_NAME = 3
SIGNUP_ACCOUNT_EXISTS = 4
SIGNUP_RATE_LIMITED = 5
SIGNUP_INVALID_EMAIL_DOMAIN = 6

LOGIN_SUCCESS = 1
LOGIN_FAIL_NO_PASSWORD = 2
LOGIN_FAIL = 3
LOGIN_TO_MANY_ATTEMPTS = 4
LOGIN_ACCOUNT_DEACTIVATED = 5
LOGIN_FAIL_SERVICE_EXPIRED = 6

DEACTIVATE_SUCCESS = 1
DEACTIVATE_ACCOUNT_DOES_NOT_EXITS = 2


@rest("/mobi/rest/user/signup", "post")
@returns(int)
@arguments(name=unicode, email=unicode, cont=unicode)
def signup(name, email, cont):
    if not name or not name.strip():
        return SIGNUP_INVALID_NAME

    if not email or not email.strip():
        return SIGNUP_INVALID_EMAIL

    if not EMAIL_REGEX.match(email):
        return SIGNUP_INVALID_EMAIL

    default_app = app.get_default_app()
    if default_app.user_regex:
        regexes = default_app.user_regex.splitlines()
        for regex in regexes:
            if re.match(regex, email):
                break
        else:
            return SIGNUP_INVALID_EMAIL_DOMAIN

    app_user_email = create_app_user_by_email(email).email()

    user = users.User(app_user_email)
    profile = get_service_or_user_profile(user)
    if profile and profile.passwordHash:
        return SIGNUP_ACCOUNT_EXISTS

    deactivated_profile = get_deactivated_user_profile(user)
    if deactivated_profile and deactivated_profile.passwordHash:
        return SIGNUP_ACCOUNT_EXISTS

    if not rate_signup_reset_password(user, os.environ.get('HTTP_X_FORWARDED_FOR', None)):
        return SIGNUP_RATE_LIMITED

    timestamp = now() + 5 * 24 * 3600
    data = dict(n=name, e=app_user_email, t=timestamp, a="registration", c=cont)
    data["d"] = calculate_secure_url_digest(data)
    data = encrypt(user, json.dumps(data))
    link = '%s/setpassword?%s' % (get_server_settings().baseUrl,
                                  urllib.urlencode((("email", app_user_email), ("data", base64.encodestring(data)),)))
    vars_ = dict(link=link, name=name, site=get_server_settings().baseUrl)
    body = render("signup", [DEFAULT_LANGUAGE], vars_)
    html = render("signup_html", [DEFAULT_LANGUAGE], vars_)
    logging.info("Sending message to %s\n%s" % (email, body))
    settings = get_server_settings()

    from_ = settings.senderEmail if default_app.type == App.APP_TYPE_ROGERTHAT else ("%s <%s>" % (default_app.name, default_app.dashboard_email_address))
    send_mail(from_, email, "Rogerthat registration", body, html=html)

    return SIGNUP_SUCCESS


def get_reset_password_url_params(name, user, action):
    """Returns a base64 url encoded data"""
    email = user.email()
    timestamp = now() + 5 * 24 * 3600
    data = dict(n=name, e=email, t=timestamp, a=action, c=None)
    data["d"] = calculate_secure_url_digest(data)
    data = encrypt(user, json.dumps(data))
    return urllib.urlencode(dict(email=email, data=base64.b64encode(data)))


@rest("/mobi/rest/user/reset_password", "post")
@returns(bool)
@arguments(email=unicode, sender_name=unicode, set_password_route=unicode)
def reset_password(email, sender_name=u'Rogerthat', set_password_route=None):
    # XXX: Validating the email would be an improvement

    app_user_email = create_app_user_by_email(email).email()
    user = users.User(app_user_email)
    profile_info = get_profile_info(user)
    if not profile_info:
        return False

    if not rate_signup_reset_password(user, os.environ.get('HTTP_X_FORWARDED_FOR', None)):
        return False

    request = GenericRESTRequestHandler.getCurrentRequest()
    language = get_languages_from_request(request)[0]

    settings = get_server_settings()
    if not set_password_route:
        set_password_route = '/setpassword'
    action = localize(language, "password reset")
    name = profile_info.name
    url_params = get_reset_password_url_params(name, user, action)
    link = '%s%s?%s' % (get_server_url(), set_password_route, url_params)

    # The use of the variable "key" is to let it pass the unittests
    key = 'app_website_' + sender_name.lower()
    sender_website = localize(language, key)
    key = sender_name
    sender_name = localize(language, key)

    vars_ = dict(link=link, name=name, app_name=sender_name, app_website=sender_website, language=language)
    body = JINJA_ENVIRONMENT.get_template('generic/reset_password.tmpl').render(vars_)
    html = JINJA_ENVIRONMENT.get_template('generic/reset_password_html.tmpl').render(vars_)
    logging.info("Sending message to %s\n%s" % (email, body))
    subject = u' - '.join((sender_name, action))
    utils.send_mail(settings.senderEmail2ToBeReplaced, email, subject, body, html=html)
    return True


@rest("/mobi/rest/user/login", "post")
@returns(int)
@arguments(email=unicode, password=unicode, remember=bool)
def login(email, password, remember):
    user = users.get_current_user()
    if user:
        return LOGIN_SUCCESS

    if not email or not password:
        return LOGIN_FAIL

    app_user_email = create_app_user_by_email(email).email()
    user = users.User(app_user_email)
    if not is_clean_app_user_email(user):
        return LOGIN_FAIL

    profile = get_service_or_user_profile(user)
    if not profile:
        deactivated_profile = get_deactivated_user_profile(user)

        if deactivated_profile:
            ActivationLog(timestamp=now(), email=user.email(), mobile=None,
                          description="Login web with deactivated user").put()
            return LOGIN_ACCOUNT_DEACTIVATED
        else:
            return LOGIN_FAIL

    if not profile.passwordHash:
        return LOGIN_FAIL_NO_PASSWORD

    if not rate_login(user):
        return LOGIN_TO_MANY_ATTEMPTS

    if profile.passwordHash != sha256_hex(password):
        return LOGIN_FAIL

    response = GenericRESTRequestHandler.getCurrentResponse()
    try:
        secret, _ = create_session(user)
    except ServiceExpiredException:
        return LOGIN_FAIL_SERVICE_EXPIRED

    server_settings = get_server_settings()
    if remember:
        set_cookie(response, server_settings.cookieSessionName, secret, expires=now() + SESSION_TIMEOUT)
    else:
        set_cookie(response, server_settings.cookieSessionName, secret)

    clear_rate_login(user)

    request = GenericRESTRequestHandler.getCurrentRequest()
    update_user_profile_language_from_headers(profile, request.headers)

    return LOGIN_SUCCESS


@rest("/mobi/rest/user/unsubscribe/reminder", "post")
@returns(int)
@arguments(email=unicode, data=unicode, reason=unicode)
def unsubscribe_reminder(email, data, reason):

    def parse_data(email, data):
        app_user_email = create_app_user_by_email(email).email()
        user = users.User(app_user_email)
        data = base64.decodestring(data)
        data = decrypt(user, data)
        data = json.loads(data)
        azzert(data["d"] == calculate_secure_url_digest(data))
        return data, user

    try:
        data, app_user = parse_data(email, data)
    except:
        logging.exception("Could not decipher url!")
        return DEACTIVATE_ACCOUNT_DOES_NOT_EXITS

    is_success = unsubscribe_from_reminder_email(app_user)
    if is_success:
        ActivationLog(timestamp=now(), email=app_user.email(), mobile=None,
                      description="Unsubscribed from reminder email | %s" % reason).put()
        return DEACTIVATE_SUCCESS
    else:
        ActivationLog(timestamp=now(), email=app_user.email(), mobile=None,
                      description="Unsubscribed from reminder email not existing account | %s" % reason).put()
        return DEACTIVATE_ACCOUNT_DOES_NOT_EXITS


@rest("/mobi/rest/user/unsubscribe/deactivate", "post")
@returns(int)
@arguments(email=unicode, data=unicode, reason=unicode)
def unsubscribe_deactivate(email, data, reason):

    def parse_data(email, data):
        if ":" in email:
            user = sanitize_app_user(users.User(email))
        else:
            app_user_email = create_app_user_by_email(email).email()
            user = users.User(app_user_email)
        data = base64.decodestring(data)
        data = decrypt(user, data)
        data = json.loads(data)
        azzert(data["d"] == calculate_secure_url_digest(data))
        return data, user

    try:
        data, app_user = parse_data(email, data)
    except:
        logging.exception("Could not decipher url!")
        return DEACTIVATE_ACCOUNT_DOES_NOT_EXITS

    deferred.defer(delete_account, app_user)
    ActivationLog(timestamp=now(), email=app_user.email(), mobile=None,
                  description="Deactivate from reminder email | %s" % reason).put()
    return DEACTIVATE_SUCCESS


@rest("/mobi/rest/user/authenticate_mobile", "post")
@cached(1, 3600, False, True)
@returns(bool)
@arguments(email=unicode, password=unicode)
def authenticate_mobile(email, password):
    if email and email.startswith('dbg_'):
        return bool(CurrentlyForwardingLogs.all().filter('xmpp_target =', email).filter('xmpp_target_password =', password).count(1))

    mobile = get_mobile_by_account(email)
    return bool(mobile) and mobile.accountPassword == password


@rest("/mobi/rest/user/statistics", "get")
@returns(UserStatisticsTO)
@arguments()
def user_statistic():
    qry1 = Mobile.all(keys_only=True).filter('status >=', 4).filter('status <', 8)
    qry2 = FriendServiceIdentityConnection.all(keys_only=True).filter('deleted', False)
    qry3 = ServiceIdentity.all(keys_only=True)
    qries = [qry1, qry2, qry3]

    def stats(qry):
        cursor = None
        fetched = 1
        count = 0
        while fetched != 0:
            fetched = qry.with_cursor(cursor).count()
            count += fetched
            cursor = qry.cursor()
        return count - 1
    user_count, application_user_count, application_count = [stats(q) for q in qries]
    us = UserStatisticsTO()
    us.user_count = user_count
    us.service_user_count = application_user_count
    us.service_count = application_count
    return us


@rest("/mobi/rest/user/context/<uid:[^/]+>", "get")
@returns(dict)
@arguments(uid=unicode)
def get_user_context(uid):
    user_context = UserContext.create_key(uid).get()  # type: UserContext
    if not user_context and not DEBUG:
        logging.debug('Context not found: ' + uid)
        raise HttpNotFoundException()
    elif user_context:
        expiration_time = user_context.created + relativedelta(minutes=5)
        is_expired = expiration_time < datetime.now()
        if is_expired:
            logging.debug('Context expired since %s, returning limited information' % expiration_time)
            return {'id': user_context.app_user.email()}
        return get_user_context_dict(user_context.app_user, user_context.scopes)
    else:
        return get_user_context_dict(users.User(uid), UserContextScope.all())


def get_user_context_dict(app_user, scopes):
    user_profile = get_user_profile(app_user)
    if not user_profile:
        logging.debug('User profile not found: %s' % app_user)
        raise HttpNotFoundException()

    r = {'id': app_user.email()}
    if UserContextScope.NAME in scopes:
        if user_profile.first_name:
            r['first_name'] = user_profile.first_name
            r['last_name'] = user_profile.last_name
        else:
            parts = user_profile.name.split(' ', 1)
            if len(parts) == 1:
                r['first_name'] = parts[0]
                r['last_name'] = None
            else:
                r['first_name'] = parts[0]
                r['last_name'] = parts[1]

    if UserContextScope.EMAIL in scopes:
        r['email'] = get_human_user_from_app_user(app_user).email()

    if UserContextScope.EMAIL_ADDRESSES in scopes:
        r['email_addresses'] = [] # todo implement

    if UserContextScope.ADDRESSES in scopes or UserContextScope.PHONE_NUMBERS in scopes:
        user_profile_info = UserProfileInfo.create_key(user_profile.user).get()
        if UserContextScope.ADDRESSES in scopes:
            addresses = []
            if user_profile_info:
                for address in user_profile_info.addresses:
                    if address.type == UserAddressType.HOME:
                        addresses.append(ProfileAddressTO.from_model(address).to_dict())
                        break
            r['addresses'] = addresses

        if UserContextScope.PHONE_NUMBERS in scopes:
            phone_numbers = []
            if user_profile_info:
                for m in user_profile_info.phone_numbers:
                    phone_numbers.append(ProfilePhoneNumberTO.from_model(m))
            r['phone_numbers'] = [pn.to_dict() for pn in sorted(phone_numbers)]

    return r
