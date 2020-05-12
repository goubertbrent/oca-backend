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
import hashlib
import json
import logging
import os
from random import choice
import re
import time
from types import NoneType

from google.appengine.api import urlfetch
from google.appengine.api.images import Image
from google.appengine.ext import db, deferred, ndb

from mcfw.cache import cached
from mcfw.consts import MISSING
from mcfw.imaging import generate_qr_code
from mcfw.properties import azzert
from mcfw.rpc import returns, arguments
from rogerthat.bizz.features import Features, Version
from rogerthat.bizz.job.update_friends import update_friend_service_identity_connections
from rogerthat.capi.system import unregisterMobile, forwardLogs, updateEmbeddedAppTranslations
from rogerthat.consts import FAST_QUEUE, HIGH_LOAD_WORKER_QUEUE
from rogerthat.dal import put_and_invalidate_cache, generator
from rogerthat.dal.app import get_app_by_id
from rogerthat.dal.broadcast import get_broadcast_settings_flow_cache_keys_of_user
from rogerthat.dal.friend import get_friends_map
from rogerthat.dal.messaging import get_messages_count
from rogerthat.dal.mobile import get_mobile_by_id, get_mobile_by_key, get_user_active_mobiles_count, \
    get_mobiles_by_ios_push_id, get_user_active_mobiles, \
    get_mobile_settings_cached
from rogerthat.dal.profile import get_avatar_by_id, get_user_profile_key, get_user_profile, get_profile_info, \
    get_deactivated_user_profile, get_service_profile
from rogerthat.models import UserProfile, Avatar, CurrentlyForwardingLogs, Installation, InstallationLog, \
    PublicKeyHistory, UserProfileInfo, UserProfileInfoAddress, \
    UserProfileInfoPhoneNumber
from rogerthat.models.properties.profiles import MobileDetails, PublicKeys, PublicKeyTO
from rogerthat.pages.legal import get_current_document_version, DOC_TERMS
from rogerthat.rpc import users
from rogerthat.rpc.models import Mobile, RpcCAPICall, ServiceAPICallback, Session, \
    ClientError, ErrorPlatformVersion, ClientErrorOccurrence
from rogerthat.rpc.rpc import mapping, logError
from rogerthat.rpc.service import logServiceError
from rogerthat.settings import get_server_settings
from rogerthat.templates import render
from rogerthat.to import GeoPointTO
from rogerthat.to.app import UpdateAppAssetResponseTO, UpdateLookAndFeelResponseTO, UpdateEmbeddedAppsResponseTO, \
    UpdateEmbeddedAppResponseTO
from rogerthat.to.profile import UserProfileTO
from rogerthat.to.system import UserStatusTO, IdentityTO, UpdateSettingsResponseTO, UnregisterMobileResponseTO, \
    UnregisterMobileRequestTO, IdentityUpdateResponseTO, LogErrorResponseTO, LogErrorRequestTO, ForwardLogsResponseTO, \
    ForwardLogsRequestTO, UpdateEmbeddedAppTranslationsResponseTO, EmbeddedAppTranslationsTO, \
    UpdateEmbeddedAppTranslationsRequestTO, AddProfileAddressRequestTO, \
    ProfileAddressTO, UpdateProfileAddressRequestTO, \
    AddProfilePhoneNumberRequestTO, UpdateProfilePhoneNumberRequestTO
from rogerthat.translations import DEFAULT_LANGUAGE, D, localize
from rogerthat.utils import now, try_or_defer, send_mail, file_get_contents
from rogerthat.utils.app import get_app_id_from_app_user, get_app_user_tuple
from rogerthat.utils.crypto import encrypt_for_jabber_cloud, decrypt_from_jabber_cloud
from rogerthat.utils.languages import get_iso_lang
from rogerthat.utils.transactions import run_in_xg_transaction, run_in_transaction
from rogerthat.to.service import ProfilePhoneNumberTO


try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO  # @UnusedImport

_BASE_DIR = os.path.dirname(__file__)
_QR_SAMPLE_OVERLAY_PATH = os.path.join(_BASE_DIR, 'qr-sample.png')
QR_SAMPLE_OVERLAY = file_get_contents(_QR_SAMPLE_OVERLAY_PATH)
_QR_CODE_OVERLAY_PATH = os.path.join(_BASE_DIR, 'qr-brand.png')
DEFAULT_QR_CODE_OVERLAY = file_get_contents(_QR_CODE_OVERLAY_PATH)
_QR_OCA_CODE_OVERLAY_PATH = os.path.join(_BASE_DIR, 'qr-brand-oca.png')
DEFAULT_OCA_QR_CODE_OVERLAY = file_get_contents(_QR_OCA_CODE_OVERLAY_PATH)
_QR_CODE_HAND_ONLY_OVERLAY_PATH = os.path.join(_BASE_DIR, 'qr-hand-only.png')
HAND_ONLY_QR_CODE_OVERLAY = file_get_contents(_QR_CODE_HAND_ONLY_OVERLAY_PATH)
_QR_CODE_EMPTY_OVERLAY_PATH = os.path.join(_BASE_DIR, 'qr-empty.png')
EMPTY_QR_CODE_OVERLAY = file_get_contents(_QR_CODE_EMPTY_OVERLAY_PATH)

LOGO_SIZE = (72, 72)
LOGO_POSITION = (259, 220)

DEFAULT_QR_CODE_COLOR = [0x6a, 0xb8, 0x00]

ERROR_PATTERN_TXN_TOOK_TOO_LONG = re.compile('Transaction with name "(.*)" took (\d+) milliseconds!')
COM_MOBICAGE_RE = re.compile('\\b(com\.mobicage\.rogerth\\S+)')
BRACKETS_RE = re.compile('({.*?})')


@returns(NoneType)
@arguments(user=users.User, mobile=Mobile, reason=unicode)
def unregister_mobile(user, mobile, reason=None):
    azzert(mobile.user == user)
    mark_mobile_for_delete(user, mobile.key())

    def trans():
        request = UnregisterMobileRequestTO()
        request.reason = reason
        ctxs = unregisterMobile(unregister_mobile_success_callback, logError, user, request=request,
                                MOBILE_ACCOUNT=mobile,
                                DO_NOT_SAVE_RPCCALL_OBJECTS=True)  # Only unregister this mobile :)
        for ctx in ctxs:
            ctx.mobile_key = mobile.key()
            ctx.put()

    run_in_transaction(trans, xg=True)


@mapping('com.mobicage.capi.system.unregisterMobileSuccessCallBack')
@returns(NoneType)
@arguments(context=RpcCAPICall, result=UnregisterMobileResponseTO)
def unregister_mobile_success_callback(context, result):
    mobile_key = context.mobile_key
    mobile = get_mobile_by_key(mobile_key)
    current_user = users.get_current_user()
    azzert(mobile.user == current_user)
    azzert(mobile == users.get_current_mobile())
    mobile.status = mobile.status | Mobile.STATUS_UNREGISTERED
    mobile.put()


@returns(NoneType)
@arguments(account=unicode, mobile_key=db.Key)
def delete_xmpp_account(account, mobile_key):
    settings = get_server_settings()
    jabberEndpoint = choice(settings.jabberAccountEndPoints)
    account_parts = account.split("@")
    azzert(len(account_parts) == 2)
    user = account_parts[0]
    server = account_parts[1]
    payload = json.dumps(dict(username=user, server=server))
    challenge, data = encrypt_for_jabber_cloud(settings.jabberSecret.encode('utf8'), payload)
    jabberUrl = "http://%s/unregister" % jabberEndpoint
    logging.info("Calling url %s to unregister %s" % (jabberUrl, account))
    response = urlfetch.fetch(url=jabberUrl, payload=data, method="POST", allow_truncated=False, follow_redirects=False,
                              validate_certificate=False, deadline=30)
    azzert(response.status_code == 200)
    success, signalNum, out, err = json.loads(
        decrypt_from_jabber_cloud(settings.jabberSecret.encode('utf8'), challenge, response.content))
    logging.info("success: %s\nexit_code or signal: %s\noutput: %s\nerror: %s" % (success, signalNum, out, err))
    azzert(success)
    if mobile_key:
        try_or_defer(_mark_mobile_as_uregistered, mobile_key)


def _mark_mobile_as_uregistered(mobile_key):
    def trans():
        mobile = db.get(mobile_key)
        mobile.status = mobile.status | Mobile.STATUS_ACCOUNT_DELETED
        mobile.put()
        return mobile

    db.run_in_transaction(trans)


def account_removal_response(sender, stanza):
    logging.info("Incoming 'unregister' message from sender %s:\n%s" % (sender, stanza))
    unregister_elements = stanza.getElementsByTagNameNS(u"mobicage:jabber", u"unregister")
    unregister_element = unregister_elements[0]
    mobile_id = unregister_element.getAttribute(u'mobileid')
    mobile = get_mobile_by_id(mobile_id)
    mobile.status = mobile.status | Mobile.STATUS_ACCOUNT_DELETED
    mobile.put()


@returns(NoneType)
@arguments(current_user=users.User, current_mobile=Mobile, majorVersion=int, minorVersion=int, flushBackLog=bool,
           appType=int, product=unicode, timestamp=long, timezone=unicode, timezoneDeltaGMT=int, osVersion=unicode,
           deviceModelName=unicode, simCountry=unicode, simCountryCode=unicode, simCarrierName=unicode,
           simCarrierCode=unicode, netCountry=unicode, netCountryCode=unicode, netCarrierName=unicode,
           netCarrierCode=unicode, localeLanguage=unicode, localeCountry=unicode, now_time=int, embeddedApps=[unicode],
           deviceId=unicode)
def _heart_beat(current_user, current_mobile, majorVersion, minorVersion, flushBackLog, appType, product, timestamp,
                timezone, timezoneDeltaGMT, osVersion, deviceModelName, simCountry, simCountryCode, simCarrierName,
                simCarrierCode, netCountry, netCountryCode, netCarrierName, netCarrierCode, localeLanguage,
                localeCountry, now_time, embeddedApps, deviceId):
    from rogerthat.bizz.look_and_feel import update_look_and_feel_for_user
    m = current_mobile
    mobile_key = m.key()
    ms_key = get_mobile_settings_cached(m).key()

    embeddedApps = MISSING.default(embeddedApps, [])

    def trans():
        # type: () -> tuple[Mobile, UserProfile, bool]
        keys = (mobile_key, ms_key, get_user_profile_key(current_user))
        mobile, ms, my_profile = db.get(keys)  # type: (Mobile, MobileSettings, UserProfile)
        if mobile.account not in my_profile.mobiles:
            logging.warn('Mobile account "%s" of user %s has been unregistered', mobile.account, current_user)
            return mobile, my_profile, False

        if appType != MISSING:
            mobile.type = my_profile.mobiles[mobile.account].type_ = appType
        if simCountry != MISSING:
            mobile.simCountry = simCountry
        if simCountryCode != MISSING:
            mobile.simCountryCode = simCountryCode
        if simCarrierCode != MISSING:
            mobile.simCarrierCode = simCarrierCode
        if simCarrierName != MISSING:
            mobile.simCarrierName = simCarrierName
        if netCountry != MISSING:
            mobile.netCountry = netCountry
        if netCountryCode != MISSING:
            mobile.netCountryCode = netCountryCode
        if netCarrierCode != MISSING:
            mobile.netCarrierCode = netCarrierCode
        if netCarrierName != MISSING:
            mobile.netCarrierName = netCarrierName
        if deviceModelName != MISSING:
            mobile.hardwareModel = deviceModelName
        if osVersion != MISSING:
            mobile.osVersion = osVersion
        if localeCountry != MISSING:
            mobile.localeCountry = localeCountry
        if localeLanguage != MISSING:
            mobile.localeLanguage = localeLanguage
        if timezone != MISSING:
            mobile.timezone = timezone
        if timezoneDeltaGMT != MISSING:
            mobile.timezoneDeltaGMT = timezoneDeltaGMT
        if deviceId != MISSING:
            mobile.deviceId = deviceId

        language = mobile.localeLanguage
        if language:
            should_update_embedded_apps = False
            if '-' in language:
                language = get_iso_lang(language.lower())
            elif mobile.localeCountry:
                language = '%s_%s' % (mobile.localeLanguage, mobile.localeCountry)

            if my_profile.language != language:
                my_profile.language = language
                # trigger friend.update service api call
                deferred.defer(update_friend_service_identity_connections, my_profile.key(), [u"language"],
                               _transactional=True)
                db.delete_async(get_broadcast_settings_flow_cache_keys_of_user(my_profile.user))
                if embeddedApps:
                    should_update_embedded_apps = True
            deferred.defer(update_look_and_feel_for_user, current_user, _transactional=True, _queue=FAST_QUEUE)

            # User updated to app version x.1.x, send custom translations
            # todo: this will also trigger when user updates from 3.0.x to 3.1.x which we don't really want
            should_update_embedded_apps = should_update_embedded_apps or majorVersion > 1 and ms.majorVersion == 0
            # Update when embedded apps are different
            should_update_embedded_apps = should_update_embedded_apps or not set(embeddedApps).issubset(
                set(my_profile.embedded_apps or []))
            if should_update_embedded_apps:
                deferred.defer(update_embedded_app_translations_for_user, current_user, embeddedApps, language,
                               _transactional=True)

        ms.majorVersion = majorVersion
        ms.minorVersion = minorVersion
        ms.lastHeartBeat = now_time

        my_profile.country = mobile.netCountry or mobile.simCountry or mobile.localeCountry
        my_profile.timezone = mobile.timezone
        my_profile.timezoneDeltaGMT = mobile.timezoneDeltaGMT
        my_profile.embedded_apps = embeddedApps
        must_update_app_settings = False
        if my_profile.tos_version != get_current_document_version(DOC_TERMS):
            if mobile.is_android:
                version = Features.ASK_TOS.android
            elif mobile.is_ios:
                version = Features.ASK_TOS.ios
            else:
                version = Version(0, 1)
            must_update_app_settings = Version(majorVersion, minorVersion) >= version
        put_and_invalidate_cache(ms, mobile, my_profile)
        return mobile, my_profile, must_update_app_settings
    mobile, profile, must_update_app_settings = run_in_xg_transaction(trans)
    if must_update_app_settings:
        from rogerthat.bizz.app import push_app_settings_to_user
        # This will ask to agree to Terms and Conditions when version has changed
        push_app_settings_to_user(profile, mobile.app_id)


@returns(int)
@arguments(current_user=users.User, current_mobile=Mobile, majorVersion=int, minorVersion=int, flushBackLog=bool,
           appType=int, product=unicode, timestamp=long, timezone=unicode, timezoneDeltaGMT=int, osVersion=unicode,
           deviceModelName=unicode, simCountry=unicode, simCountryCode=unicode, simCarrierName=unicode,
           simCarrierCode=unicode, netCountry=unicode, netCountryCode=unicode, netCarrierName=unicode,
           netCarrierCode=unicode, localeLanguage=unicode, localeCountry=unicode, embeddedApps=[unicode], deviceId=unicode)
def heart_beat(current_user, current_mobile, majorVersion, minorVersion, flushBackLog, appType, product, timestamp,
               timezone, timezoneDeltaGMT, osVersion, deviceModelName, simCountry, simCountryCode, simCarrierName,
               simCarrierCode, netCountry, netCountryCode, netCarrierName, netCarrierCode, localeLanguage,
               localeCountry, embeddedApps, deviceId):
    now_time = int(time.time())

    try_or_defer(_heart_beat, current_user, current_mobile, majorVersion, minorVersion, flushBackLog, appType, product,
                 timestamp, timezone, timezoneDeltaGMT, osVersion, deviceModelName, simCountry, simCountryCode,
                 simCarrierName, simCarrierCode, netCountry, netCountryCode, netCarrierName, netCarrierCode,
                 localeLanguage, localeCountry, now_time, embeddedApps, deviceId,
                 accept_missing=True)
    return now_time


@returns(UserStatusTO)
@arguments(user=users.User)
def get_user_status(user):
    logging.info("Getting user status for %s" % user)
    us = UserStatusTO()
    user_profile = get_user_profile(user)
    us.profile = UserProfileTO.fromUserProfile(user_profile) if user_profile else None
    us.registered_mobile_count = get_user_active_mobiles_count(user)
    if user_profile:
        avatar = get_avatar_by_id(user_profile.avatarId)
        us.has_avatar = bool(avatar and avatar.picture)
    else:
        us.has_avatar = False
    return us


@returns(IdentityTO)
@arguments(app_user=users.User, user_profile=UserProfile)
def get_identity(app_user, user_profile=None):
    idTO = IdentityTO()
    profile = user_profile or get_user_profile(app_user)
    human_user, app_id = get_app_user_tuple(app_user)
    idTO.email = human_user.email()
    if profile.first_name:
        idTO.name = u'%s %s' % (profile.first_name, profile.last_name)
        idTO.firstName = profile.first_name
        idTO.lastName = profile.last_name
    else:
        idTO.name = profile.name
        parts = profile.name.split(" ", 1)
        if len(parts) == 1:
            idTO.firstName = parts[0]
            idTO.lastName = u''
        else:
            idTO.firstName = parts[0]
            idTO.lastName = parts[1]
    idTO.avatarId = profile.avatarId
    idTO.qualifiedIdentifier = profile.qualifiedIdentifier
    idTO.birthdate = profile.birthdate or 0
    idTO.gender = profile.gender or 0
    idTO.hasBirthdate = profile.birthdate is not None
    idTO.hasGender = profile.gender is not None
    idTO.profileData = profile.profileData

    app = get_app_by_id(get_app_id_from_app_user(app_user))
    if app.owncloud_base_uri:
        idTO.owncloudUri = app.owncloud_base_uri if profile.owncloud_password else None
        idTO.owncloudUsername = u"%s_%s" % (idTO.email, app_id)
        idTO.owncloudPassword = profile.owncloud_password
    else:
        idTO.owncloudUri = None
        idTO.owncloudUsername = None
        idTO.owncloudPassword = None
    return idTO


@returns(NoneType)
@arguments(user=users.User, type_=unicode, subject=unicode, message=unicode)
def feedback(user, type_, subject, message):
    email_subject = "Feedback - %s - %s" % (type_, subject)
    friend_count = len(get_friends_map(user).friends)
    message_count = get_messages_count(user)
    mobiles = get_user_active_mobiles(user)
    email = user.email()
    timestamp = now()
    profile_info = get_profile_info(user)

    d = dict(type_=type_, subject=subject, message=message, email=email,
             profile_info=profile_info, friend_count=friend_count, message_count=message_count,
             mobiles=mobiles, timestamp=timestamp)

    body = render("feedback", [DEFAULT_LANGUAGE], d)
    server_settings = get_server_settings()

    send_mail(server_settings.senderEmail, server_settings.supportEmail, email_subject, body)


@mapping('com.mobicage.capi.system.updateSettingsResponseHandler')
@returns(NoneType)
@arguments(context=RpcCAPICall, result=UpdateSettingsResponseTO)
def update_settings_response_handler(context, result):
    pass


@mapping('com.mobicage.capi.system.identityUpdateResponseHandler')
@returns(NoneType)
@arguments(context=RpcCAPICall, result=IdentityUpdateResponseTO)
def identity_update_response_handler(context, result):
    pass


@mapping('com.mobicage.capi.system.forwardLogsResponseHandler')
@returns(NoneType)
@arguments(context=RpcCAPICall, result=ForwardLogsResponseTO)
def forward_logs_response_handler(context, result):
    pass


def _mark_mobile_for_delete(mobile):
    logging.info("Marking mobile (%s) for delete", mobile.key())
    mobile.pushId = None
    mobile.status = mobile.status | Mobile.STATUS_DELETE_REQUESTED
    db.put_async(mobile)


@returns(NoneType)
@arguments(user=users.User, mobile_key=db.Key)
def mark_mobile_for_delete(user, mobile_key):
    def trans():
        mobile, profile = db.get((mobile_key, get_user_profile_key(user)))
        _mark_mobile_for_delete(mobile)
        if not profile:
            logging.debug("No UserProfile found for user %s. Trying to get archived UserProfile...", user)
            profile = get_deactivated_user_profile(user)
        if profile:
            if not profile.mobiles:
                profile.mobiles = MobileDetails()
            profile.mobiles.remove(mobile.account)
            profile.put()
        else:
            logging.warn("No profile found for user %s", user)

    xg_on = db.create_transaction_options(xg=True)
    db.run_in_transaction_options(xg_on, trans)


@returns(NoneType)
@arguments(mobile=Mobile, token=unicode)
def update_apple_push_device_token(mobile, token):
    if mobile.type in Mobile.IOS_TYPES:
        token.decode("hex")  # just check whether is nicely hex encoded

    if mobile.pushId == token:
        pass  # prevent unnecessary datastore accesses

    old_mobiles = list(get_mobiles_by_ios_push_id(token))
    user = mobile.user

    def trans(mobile_key, user):
        mobile, profile = db.get((mobile_key, get_user_profile_key(user)))
        mobile.pushId = token
        db.put_async(mobile)
        if not profile.mobiles:
            profile.mobiles = MobileDetails()
        if mobile.account in profile.mobiles:
            profile.mobiles[mobile.account].pushId = token
        else:
            profile.mobiles.addNew(mobile.account, mobile.type, token, get_app_id_from_app_user(user))
        for old_mobile in old_mobiles:
            if mobile_key != old_mobile.key():
                if mobile.user == old_mobile.user:
                    _mark_mobile_for_delete(old_mobile)
                    profile.mobiles.remove(old_mobile.account)
                else:
                    deferred.defer(mark_mobile_for_delete, old_mobile.user, old_mobile.key(), _transactional=True)
        profile.put()

    xg_on = db.create_transaction_options(xg=True)
    db.run_in_transaction_options(xg_on, trans, mobile.key(), user)


@returns(NoneType)
@arguments(token=unicode)
def obsolete_apple_push_device_token(token):
    logging.info("Obsoleting apple push device " + token)
    for mobile in get_mobiles_by_ios_push_id(token):
        logging.info("Removing pushId from mobile %s of %s.", mobile.account, mobile.user)
        mobile.pushId = None
        mobile.put()


@cached(2, 0, datastore="qrcode_image")
@returns(str)
@arguments(content=unicode, overlay=str, color=[int], sample=bool)
def qrcode(content, overlay, color, sample):
    return generate_qr_code(content, overlay, color, QR_SAMPLE_OVERLAY if sample else None)


@returns(NoneType)
@arguments(mobile=Mobile, phone_number=unicode)
def set_validated_phonenumber(mobile, phone_number):
    if mobile.type == Mobile.TYPE_ANDROID_HTTP or mobile.type == Mobile.TYPE_ANDROID_FIREBASE_HTTP:
        mobile.phoneNumber = phone_number
        mobile.phoneNumberVerified = True
        mobile.put()
    elif mobile.type in Mobile.IOS_TYPES:
        if mobile.phoneNumberVerificationCode == phone_number:
            mobile.phoneNumberVerified = True
            mobile.put()
        else:
            raise ValueError("Verification code does not match")
    else:
        raise ValueError("Unknown platform")


@returns(bool)
@arguments(request=LogErrorRequestTO)
def shouldLogClientError(request):
    # Return boolean - should we put this error in mobile error logs
    if request.description:
        if 'Warning: DNS SRV did time out. Falling back to rogerth.at:5222' in request.description \
                or 'Using fallback value for DNS SRV (but network is up)' in request.description:
            return False
        matches = ERROR_PATTERN_TXN_TOOK_TOO_LONG.findall(request.description)
        if matches:
            return False

    if request.errorMessage:
        if "ServerRespondedWrongHTTPCodeException" in request.errorMessage:
            return False
        if "java.lang.NullPointerException" in request.errorMessage \
                and "android.os.Parcel.readException(Parcel.java" in request.errorMessage:
            return False
        if "java.lang.SecurityException: !@Too many alarms (500) registered from pid " in request.errorMessage:
            return False
        if "mCursorDrawable" in request.errorMessage and "huawei" in request.platformVersion.lower():
            return False

    return True


@returns(LogErrorResponseTO)
@arguments(request=LogErrorRequestTO, user=users.User, install_id=unicode, session=Session)
def logErrorBizz(request, user=None, install_id=None, session=None):
    from add_1_monkey_patches import DEBUG
    if not shouldLogClientError(request):
        logging.warn('Ignoring logError request for %s:\n%s\n\n%s',
                     user or install_id, request.description, request.errorMessage)
        return

    if DEBUG:
        logging.warn('CLIENT ERROR:\n%s\n\n%s', request.description, request.errorMessage)

    deferred.defer(_log_client_error, request, user, install_id, session, _queue=HIGH_LOAD_WORKER_QUEUE)


def _filter_specific_stuff(msg):
    msg = COM_MOBICAGE_RE.sub('', msg)
    msg = BRACKETS_RE.sub('', msg)
    return msg


def get_error_key(platform, message, description):
    hashed_err = hashlib.sha256()
    hashed_err.update(str(platform))
    hashed_err.update('-')
    hashed_err.update(_filter_specific_stuff(message).encode('utf-8') if message else '')
    hashed_err.update('-')
    hashed_err.update(_filter_specific_stuff(description).encode('utf-8') if description else '')
    key_name = hashed_err.hexdigest()
    return key_name


@arguments(request=LogErrorRequestTO, user=users.User, install_id=unicode, session=Session)
def _log_client_error(request, user, install_id, session):
    key_name = get_error_key(request.platform, request.errorMessage, request.description)
    error_key = ClientError.create_key(key_name)

    # When too many collisions occur, consider a queue that can only execute 1 task/sec
    @ndb.transactional()
    def trans():
        err = error_key.get()
        if not err:
            err = ClientError(key=error_key,
                              versions=[],
                              message=request.errorMessage,
                              description=request.description,
                              platform=request.platform)
        for ver in err.versions:
            if ver.platform_version == request.platformVersion and ver.client_version == request.mobicageVersion:
                break
        else:
            err.versions.append(ErrorPlatformVersion(platform_version=request.platformVersion,
                                                     client_version=request.mobicageVersion))
        err.count += 1
        now_ = now()
        ts = request.timestamp / 1000 if request.timestamp > now_ * 10 else request.timestamp
        # don't accept timestamps in the future
        if ts > now_:
            ts = now_
        if session and session.user != user:
            if session.shop:
                user_str = u'%s (%s via shop)' % (user, session.user)
            else:
                user_str = u'%s (%s)' % (user, session.user)
        elif user:
            user_str = u'%s' % user
        else:
            user_str = None
        client_error = ClientErrorOccurrence(parent=error_key,
                                             user=user.email() if user else None,
                                             install_id=install_id,
                                             occurred_date=datetime.utcfromtimestamp(ts),
                                             user_str=user_str)
        ndb.put_multi([err, client_error])

    trans()

    installation = Installation.get_by_key_name(install_id) if install_id else None
    if installation:
        InstallationLog(parent=installation, timestamp=now(), description=u'ClientError occurred').put()


@returns(NoneType)
@arguments(app_user=users.User, name=unicode, first_name=unicode, last_name=unicode, image=unicode, access_token=unicode,
           birthdate=long, gender=long, has_birthdate=bool, has_gender=bool, current_mobile=Mobile)
def _edit_profile(app_user, name, first_name, last_name, image, access_token,
                  birthdate, gender, has_birthdate, has_gender, current_mobile):
    from rogerthat.bizz.profile import update_avatar_profile, couple_facebook_id_with_profile, schedule_re_index

    def trans(image):
        changed_properties = []
        user_profile = get_user_profile(app_user)
        if first_name is not None and first_name is not MISSING and last_name is not None and last_name is not MISSING:
            if user_profile.first_name != first_name:
                changed_properties.append(u"first_name")
            user_profile.first_name = first_name
            if user_profile.last_name != last_name:
                changed_properties.append(u"last_name")
            user_profile.last_name = last_name
            user_profile.name = u'%s %s' % (user_profile.first_name, user_profile.last_name)
        elif name is not None and name is not MISSING:
            if user_profile.name != name:
                changed_properties.append(u"name")
            user_profile.name = name
            user_profile.first_name = None
            user_profile.last_name = None

        # has_birthdate and has_gender are used starting from 1.0.999.A and 1.0.137.i
        if has_birthdate is not MISSING and has_gender is not MISSING:
            if has_birthdate is True:
                user_profile.birthdate = birthdate
                user_profile.birth_day = UserProfile.get_birth_day_int(birthdate)
            if has_gender is True:
                user_profile.gender = gender
        else:
            # birthdate and gender are only used without has_gender and has_birthdate in 1.0.998.A
            if birthdate is not MISSING and gender is not MISSING:
                if birthdate == 0 and gender == 0:
                    pass  # user pressed save in 1.0.998.A without setting gender and birthdate
                else:
                    user_profile.birthdate = birthdate
                    user_profile.birth_day = UserProfile.get_birth_day_int(birthdate)
                    if gender != 0:
                        user_profile.gender = gender

        if image:
            avatar = get_avatar_by_id(user_profile.avatarId)
            if not avatar:
                avatar = Avatar(user=user_profile.user)

            image = base64.b64decode(str(image))
            img = Image(image)
            if img.width > 150 or img.height > 150:
                logging.info('Resizing avatar from %sx%s to 150x150', img.width, img.height)
                img.resize(150, 150)
                image = img.execute_transforms(img.format, 100)

            update_avatar_profile(user_profile, avatar, image)
            changed_properties.append(u"avatar")
        user_profile.version += 1
        user_profile.put()

        from rogerthat.bizz.profile import update_mobiles, update_friends
        update_mobiles(user_profile.user, user_profile, current_mobile)  # update myIdentity
        schedule_re_index(app_user)
        if changed_properties:  # Not necessary when only birth date or gender were updated.
            update_friends(user_profile)  # notify my friends.

    xg_on = db.create_transaction_options(xg=True)
    db.run_in_transaction_options(xg_on, trans, image)

    if access_token:
        couple_facebook_id_with_profile(app_user, access_token)


@returns(NoneType)
@arguments(app_user=users.User, name=unicode, first_name=unicode, last_name=unicode, image=unicode, access_token=unicode,
           birthdate=long, gender=long, has_birthdate=bool, has_gender=bool, current_mobile=Mobile)
def edit_profile(app_user, name, first_name, last_name, image, access_token=None,
                 birthdate=MISSING, gender=MISSING, has_birthdate=MISSING, has_gender=MISSING, current_mobile=None):
    try_or_defer(_edit_profile, app_user, name, first_name, last_name, image, access_token,
                 birthdate, gender, has_birthdate, has_gender, current_mobile, accept_missing=True)


@returns(bool)
@arguments(profile_info=(UserProfileInfo, NoneType))
def has_profile_addresses(profile_info):
    return False if not (profile_info and profile_info.addresses) else True


@returns([ProfileAddressTO])
@arguments(app_user=users.User)
def get_profile_addresses(app_user):
    return get_profile_addresses_to(UserProfileInfo.create_key(app_user).get())


@returns([ProfileAddressTO])
@arguments(user_profile_info=UserProfileInfo)
def get_profile_addresses_to(user_profile_info):
    # type: (UserProfileInfo) -> list[ProfileAddressTO]
    if not user_profile_info:
        return []
    return [ProfileAddressTO.from_model(address) for address in user_profile_info.addresses]


def _update_profile_address(app_user, request, is_update=False):
    # type: (users.User, ProfileAddressTO, bool) -> UserProfileInfoAddress
    app_id = get_app_id_from_app_user(app_user)
    country_code = get_app_by_id(app_id).country
    if not country_code:
        raise Exception('No country code set for app %s' % app_id)
    upi_key = UserProfileInfo.create_key(app_user)
    profile_info = upi_key.get()
    if not profile_info:
        if is_update:
            return None
        profile_info = UserProfileInfo(key=upi_key)

    address_uid = UserProfileInfoAddress.create_uid([country_code,
                                                     request.zip_code,
                                                     request.street_name,
                                                     request.house_nr,
                                                     request.bus_nr])

    if is_update:
        old_address = profile_info.get_address(request.uid)
        if not old_address:
            return None
        should_update = request.uid == address_uid
    else:
        old_address = profile_info.get_address(address_uid)
        should_update = True if old_address else False

    if should_update:
        return _save_existing_address(profile_info, old_address, request)

    if is_update:
        profile_info.addresses.remove(old_address)
        existing_address = profile_info.get_address(address_uid)
        if existing_address:
            return _save_existing_address(profile_info, existing_address, request)

    street_uid = UserProfileInfoAddress.create_uid([country_code,
                                                    request.zip_code,
                                                    request.street_name])

    address = UserProfileInfoAddress(created=datetime.now(),
                                     address_uid=address_uid,
                                     street_uid=street_uid,
                                     label=request.label,
                                     geo_location=ndb.GeoPt(request.geo_location.lat,
                                                            request.geo_location.lon),
                                     distance=request.distance,
                                     street_name=request.street_name,
                                     house_nr=request.house_nr,
                                     bus_nr=request.bus_nr,
                                     zip_code=request.zip_code,
                                     city=request.city,
                                     type=request.type,
                                     country_code=country_code)
    profile_info.addresses.append(address)
    profile_info.put()

    return address


def _save_existing_address(profile_info, existing_address, request):
    existing_address.label = request.label
    existing_address.distance = request.distance
    existing_address.type = request.type
    profile_info.put()
    return existing_address


@returns(UserProfileInfoAddress)
@arguments(app_user=users.User, request=AddProfileAddressRequestTO)
def add_profile_address(app_user, request):
    return _update_profile_address(app_user, request)


@returns(UserProfileInfoAddress)
@arguments(app_user=users.User, request=UpdateProfileAddressRequestTO)
def update_profile_address(app_user, request):
    return _update_profile_address(app_user, request, is_update=True)


@returns()
@arguments(app_user=users.User, address_uids=[unicode])
def delete_profile_addresses(app_user, address_uids):
    upi = UserProfileInfo.create_key(app_user).get()
    if not upi:
        return

    should_put = False
    for a in reversed(upi.addresses):
        if a.address_uid in address_uids:
            should_put = True
            upi.addresses.remove(a)

    if should_put:
        upi.put()


@returns([ProfilePhoneNumberTO])
@arguments(app_user=users.User)
def get_profile_phone_numbers(app_user):
    return get_profile_phone_numbers_to(UserProfileInfo.create_key(app_user).get())


@returns([ProfilePhoneNumberTO])
@arguments(user_profile_info=UserProfileInfo)
def get_profile_phone_numbers_to(user_profile_info):
    # type: (UserProfileInfo) -> list[ProfilePhoneNumberTO]
    if not user_profile_info or not user_profile_info.phone_numbers:
        return []
    return [ProfilePhoneNumberTO.from_model(m) for m in user_profile_info.phone_numbers]


def _update_profile_phone_number(app_user, request, is_update=False):
    # type: (users.User, ProfileAddressTO, bool) -> UserProfileInfoAddress
    upi_key = UserProfileInfo.create_key(app_user)
    profile_info = upi_key.get()
    if not profile_info:
        if is_update:
            return None
        profile_info = UserProfileInfo(key=upi_key)
        
    phone_number = UserProfileInfoPhoneNumber(created=datetime.now(),
                                              type=request.type,
                                              label=request.label,
                                              number=request.number)
    phone_number_uid = phone_number.uid

    if is_update:
        old_phone_number = profile_info.get_phone_number(request.uid)
        if not old_phone_number:
            return None
        if request.uid == phone_number_uid:
            return _save_existing_phone_number(profile_info, old_phone_number, request)
    else:
        old_phone_number = profile_info.get_phone_number(phone_number_uid)
        if old_phone_number:
            return _save_existing_phone_number(profile_info, old_phone_number, request)

    if is_update:
        profile_info.phone_numbers.remove(old_phone_number)
        existing_phone_number = profile_info.get_phone_number(phone_number_uid)
        if existing_phone_number:
            return _save_existing_phone_number(profile_info, existing_phone_number, request)

    profile_info.phone_numbers.append(phone_number)
    profile_info.put()

    return phone_number


def _save_existing_phone_number(profile_info, existing_phone_number, request):
    existing_phone_number.type = request.type
    existing_phone_number.label = request.label
    profile_info.put()
    return existing_phone_number


@returns(UserProfileInfoPhoneNumber)
@arguments(app_user=users.User, request=AddProfilePhoneNumberRequestTO)
def add_profile_phone_number(app_user, request):
    return _update_profile_phone_number(app_user, request)


@returns(UserProfileInfoPhoneNumber)
@arguments(app_user=users.User, request=UpdateProfilePhoneNumberRequestTO)
def update_profile_phone_number(app_user, request):
    return _update_profile_phone_number(app_user, request, is_update=True)


@returns()
@arguments(app_user=users.User, uids=[unicode])
def delete_profile_phone_numbers(app_user, uids):
    upi = UserProfileInfo.create_key(app_user).get()
    if not upi:
        return

    should_put = False
    for m in reversed(upi.phone_numbers):
        if m.uid in uids:
            should_put = True
            upi.phone_numbers.remove(m)

    if should_put:
        upi.put()


@returns(CurrentlyForwardingLogs)
@arguments(app_user=users.User, xmpp_target_jid=unicode, mobile=Mobile, xmpp_target_password=unicode, type_=int)
def start_log_forwarding(app_user, xmpp_target_jid, mobile=None, xmpp_target_password=None,
                         type_=CurrentlyForwardingLogs.TYPE_XMPP):
    def trans():
        request = ForwardLogsRequestTO()
        request.jid = unicode(xmpp_target_jid) if xmpp_target_jid else None
        forwardLogs(forward_logs_response_handler, logError, app_user, request=request, MOBILE_ACCOUNT=mobile)
        if request.jid:
            clf = CurrentlyForwardingLogs(key=CurrentlyForwardingLogs.create_key(app_user),
                                          xmpp_target=request.jid,
                                          xmpp_target_password=xmpp_target_password,
                                          type=type_)
            clf.put()
            return clf
        else:
            db.delete(CurrentlyForwardingLogs.create_key(app_user))
            return None

    if db.is_in_transaction:
        return trans()
    else:
        xg_on = db.create_transaction_options(xg=True)
        return db.run_in_transaction_options(xg_on, trans)


@returns(NoneType)
@arguments(app_user=users.User)
def stop_log_forwarding(app_user):
    start_log_forwarding(app_user, None)


@returns([CurrentlyForwardingLogs])
@arguments()
def get_users_currently_forwarding_logs():
    def trans():
        return generator(CurrentlyForwardingLogs.all().ancestor(CurrentlyForwardingLogs.create_parent_key()))

    return db.run_in_transaction(trans)


@returns()
@arguments(service_user=users.User, email=unicode, success=bool)
def delete_service_finished(service_user, email, success):
    from rogerthat.service.api.system import service_deleted
    service_deleted(system_service_deleted_response_handler, logServiceError, get_service_profile(service_user),
                    email=email, success=success)


@mapping('system.service_deleted.response_handler')
@returns(NoneType)
@arguments(context=ServiceAPICallback, result=NoneType)
def system_service_deleted_response_handler(context, result):
    pass


@returns(NoneType)
@arguments(app_user=users.User, current_mobile=Mobile, public_key=unicode, public_keys=[PublicKeyTO])
def set_secure_info(app_user, current_mobile, public_key, public_keys):
    try_or_defer(_set_secure_info, app_user, current_mobile, public_key, public_keys)


@returns(NoneType)
@arguments(app_user=users.User, current_mobile=Mobile, public_key=unicode, public_keys=[PublicKeyTO])
def _set_secure_info(app_user, current_mobile, public_key, public_keys):
    def trans():

        user_profile = get_user_profile(app_user)
        if public_keys is not MISSING:
            changed_properties = [u"public_keys"]
            if not user_profile.public_keys:
                user_profile.public_keys = PublicKeys()
            for pk in public_keys:
                if pk.public_key:
                    user_profile.public_keys.addNew(pk.algorithm, pk.name, pk.index, pk.public_key)
                    name = PublicKeyHistory.create_name(pk.algorithm, pk.name, pk.index)
                    pk = PublicKeyHistory.create(app_user, name, pk.public_key)
                    pk.put()
                else:
                    user_profile.public_keys.remove(pk.algorithm, pk.name, pk.index)
        else:
            changed_properties = [u"public_key"]
            user_profile.public_key = public_key
            pk = PublicKeyHistory.create(app_user, None, public_key)
            pk.put()
        user_profile.version += 1
        user_profile.put()

        update_friend_service_identity_connections(user_profile.key(), changed_properties)  # trigger friend.update

    run_in_xg_transaction(trans)


@mapping('com.mobicage.capi.system.update_app_asset')
@returns(NoneType)
@arguments(context=RpcCAPICall, result=UpdateAppAssetResponseTO)
def update_app_asset_response(context, result):
    pass


@mapping('com.mobicage.capi.system.update_look_and_feel')
@returns(NoneType)
@arguments(context=RpcCAPICall, result=UpdateLookAndFeelResponseTO)
def update_look_and_feel_response(context, result):
    pass


@mapping('com.mobicage.capi.system.update_embedded_app_translations')
@returns(NoneType)
@arguments(context=RpcCAPICall, result=UpdateEmbeddedAppTranslationsResponseTO)
def update_embedded_app_translations_response(context, result):
    pass


@mapping('com.mobicage.capi.system.update_embedded_app')
@returns(NoneType)
@arguments(context=RpcCAPICall, result=UpdateEmbeddedAppResponseTO)
def update_embedded_app_response(context, result):
    pass


@mapping('com.mobicage.capi.system.update_embedded_apps')
@returns(NoneType)
@arguments(context=RpcCAPICall, result=UpdateEmbeddedAppsResponseTO)
def update_embedded_apps_response(context, result):
    pass


@returns()
@arguments(app_user=users.User, embedded_apps=[unicode], language=unicode)
def update_embedded_app_translations_for_user(app_user, embedded_apps, language):
    translations = get_embedded_app_translations(embedded_apps, language)
    if translations:
        updateEmbeddedAppTranslations(update_embedded_app_translations_response, logError, app_user,
                                      request=UpdateEmbeddedAppTranslationsRequestTO(translations))


@returns([EmbeddedAppTranslationsTO])
@arguments(embedded_apps=[unicode], language=unicode)
def get_embedded_app_translations(embedded_apps, language):
    translations = []
    for embedded_app in embedded_apps:
        trans = {}
        for translation_key in D[DEFAULT_LANGUAGE]:
            if translation_key.startswith(embedded_app):
                key = translation_key.replace('%s.' % embedded_app, '')
                trans[key] = localize(language, translation_key)
        if trans:
            translations.append(EmbeddedAppTranslationsTO(embedded_app, json.dumps(trans).decode('utf-8')))
    return translations
