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
import logging
import time

from google.appengine.ext import deferred

from mcfw.consts import MISSING
from mcfw.rpc import returns, arguments
from rogerthat.bizz.embedded_applications import get_embedded_application, get_embedded_apps_by_type, \
    get_embedded_apps_by_community
from rogerthat.bizz.friends import get_user_invite_url, get_user_and_qr_code_url
from rogerthat.bizz.registration import save_push_notifications_consent, get_headers_for_consent
from rogerthat.bizz.service import get_default_qr_template_by_app_id
from rogerthat.dal.app import get_app_settings, get_app_by_id
from rogerthat.dal.mobile import get_mobile_settings_cached
from rogerthat.dal.profile import get_user_profile
from rogerthat.models import JSEmbedding, ProfileZipCodes, ProfileStreets
from rogerthat.models.apps import AppAsset
from rogerthat.rpc import users
from rogerthat.rpc.http import get_current_request
from rogerthat.rpc.rpc import expose
from rogerthat.rpc.users import get_current_user
from rogerthat.to.app import GetAppAssetResponseTO, GetAppAssetRequestTO, GetEmbeddedAppsResponseTO, \
    GetEmbeddedAppsRequestTO, GetEmbeddedAppResponseTO, GetEmbeddedAppRequestTO, EmbeddedAppTO
from rogerthat.to.js_embedding import GetJSEmbeddingResponseTO, GetJSEmbeddingRequestTO
from rogerthat.to.system import SettingsTO, SaveSettingsRequest, SaveSettingsResponse, LogErrorResponseTO, \
    LogErrorRequestTO, UnregisterMobileRequestTO, UnregisterMobileResponseTO, HeartBeatRequestTO, HeartBeatResponseTO, \
    GetIdentityRequestTO, GetIdentityResponseTO, UpdateApplePushDeviceTokenRequestTO, \
    UpdateApplePushDeviceTokenResponseTO, GetIdentityQRCodeRequestTO, GetIdentityQRCodeResponseTO, \
    SetMobilePhoneNumberRequestTO, SetMobilePhoneNumberResponseTO, EditProfileRequestTO, EditProfileResponseTO, \
    GetProfileAddressesResponseTO, GetProfileAddressesRequestTO, \
    AddProfileAddressResponseTO, AddProfileAddressRequestTO, \
    DeleteProfileAddressesResponseTO, DeleteProfileAddressesRequestTO, \
    UpdateProfileAddressResponseTO, UpdateProfileAddressRequestTO, \
    ListZipCodesResponseTO, ListZipCodesRequestTO, ListStreetsResponseTO, \
    ListStreetsRequestTO, ZipCodeTO, AddProfilePhoneNumberResponseTO, \
    AddProfilePhoneNumberRequestTO, UpdateProfilePhoneNumberResponseTO, \
    UpdateProfilePhoneNumberRequestTO, DeleteProfilePhoneNumbersResponseTO, \
    DeleteProfilePhoneNumbersRequestTO, GetProfilePhoneNumbersResponseTO, \
    GetProfilePhoneNumbersRequestTO
from rogerthat.utils import channel, slog, try_or_defer
from rogerthat.utils.app import create_app_user, get_app_id_from_app_user


@expose(('api',))
@returns(LogErrorResponseTO)
@arguments(request=LogErrorRequestTO)
def logError(request):
    from rogerthat.bizz.system import logErrorBizz
    return logErrorBizz(request, get_current_user())


@expose(('api',))
@returns(SaveSettingsResponse)
@arguments(request=SaveSettingsRequest)
def saveSettings(request):
    mobile = users.get_current_mobile()
    db_settings = get_mobile_settings_cached(mobile)
    db_settings.recordPhoneCalls = request.callLogging
    db_settings.geoLocationTracking = request.tracking
    db_settings.timestamp = int(time.time())
    db_settings.version += 1
    db_settings.put()

    user_profile = get_user_profile(mobile.user)
    if MISSING.default(request.push_notifications, None):
        if not user_profile.consent_push_notifications_shown:
            user_profile.consent_push_notifications_shown = True
            user_profile.put()

        rest_request = get_current_request()
        deferred.defer(save_push_notifications_consent, mobile.user, get_headers_for_consent(rest_request),
                       u'yes' if request.push_notifications.enabled else u'no')

    app_settings = get_app_settings(users.get_current_app_id())
    channel.send_message(users.get_current_user(), u'rogerthat.settings.update', mobile_id=mobile.id)

    return SaveSettingsResponse(settings=SettingsTO.fromDBSettings(app_settings, user_profile, db_settings))


@expose(('api',))
@returns(UnregisterMobileResponseTO)
@arguments(request=UnregisterMobileRequestTO)
def unregisterMobile(request):
    from rogerthat.bizz.system import unregister_mobile
    unregister_mobile(users.get_current_user(), users.get_current_mobile())


@expose(('api',))
@returns(HeartBeatResponseTO)
@arguments(request=HeartBeatRequestTO)
def heartBeat(request):
    from rogerthat.bizz.system import heart_beat
    response = HeartBeatResponseTO()
    app_user = users.get_current_user()
    current_mobile = users.get_current_mobile()
    response.systemTime = heart_beat(app_user, current_mobile, majorVersion=request.majorVersion, minorVersion=request.minorVersion,
                                     flushBackLog=request.flushBackLog, appType=request.appType,
                                     product=request.product, timestamp=request.timestamp, timezone=request.timezone,
                                     timezoneDeltaGMT=request.timezoneDeltaGMT, osVersion=request.SDKVersion,
                                     deviceModelName=request.deviceModelName, simCountry=request.simCountry,
                                     simCountryCode=request.simCountryCode, simCarrierName=request.simCarrierName,
                                     simCarrierCode=request.simCarrierCode, netCountry=request.netCountry,
                                     netCountryCode=request.netCountryCode, netCarrierName=request.netCarrierName,
                                     netCarrierCode=request.netCarrierCode, localeLanguage=request.localeLanguage,
                                     localeCountry=request.localeCountry, deviceId=request.deviceId,
                                     accept_missing=True)
    slog('T', get_current_user().email(), "com.mobicage.api.system.heartBeat", timestamp=request.timestamp,
         major_version=request.majorVersion, minor_version=request.minorVersion, product=request.product,
         sdk_version=request.SDKVersion, networkState=request.networkState)
    return response


@expose(('api',))
@returns(GetIdentityResponseTO)
@arguments(request=GetIdentityRequestTO)
def getIdentity(request):
    from rogerthat.bizz.system import get_identity
    from rogerthat.bizz.friends import userCode as userCodeBizz
    user = users.get_current_user()
    response = GetIdentityResponseTO()
    response.shortUrl = unicode(get_user_invite_url(userCodeBizz(user)))
    response.identity = get_identity(user)
    return response


@expose(('api',))
@returns(UpdateApplePushDeviceTokenResponseTO)
@arguments(request=UpdateApplePushDeviceTokenRequestTO)
def updateApplePushDeviceToken(request):
    from rogerthat.bizz.system import update_apple_push_device_token
    try_or_defer(update_apple_push_device_token, users.get_current_mobile(), request.token)


@expose(('api',))
@returns(GetIdentityQRCodeResponseTO)
@arguments(request=GetIdentityQRCodeRequestTO)
def getIdentityQRCode(request):
    # Only for human users
    from rogerthat.bizz.friends import userCode as userCodeBizz
    from rogerthat.bizz.system import qrcode

    app_user = users.get_current_user()
    app_id = get_app_id_from_app_user(app_user)
    code = userCodeBizz(create_app_user(users.User(request.email), app_id))
    response = GetIdentityQRCodeResponseTO()
    response.shortUrl = unicode(get_user_invite_url(code))
    qrtemplate, color = get_default_qr_template_by_app_id(app_id)
    qr_code_url_and_user_tuple = get_user_and_qr_code_url(code)
    if not qr_code_url_and_user_tuple:
        logging.warn("getIdentityQRCode ProfilePointer was None\n- request.email: %s\n- request.size: %s",
                     request.email, request.size)
        return None
    qr_code_url, _ = qr_code_url_and_user_tuple
    response.qrcode = unicode(base64.b64encode(qrcode(qr_code_url, qrtemplate.blob, color, False)))
    return response


@expose(('api',))
@returns(SetMobilePhoneNumberResponseTO)
@arguments(request=SetMobilePhoneNumberRequestTO)
def setMobilePhoneNumber(request):
    from rogerthat.bizz.system import set_validated_phonenumber
    set_validated_phonenumber(users.get_current_mobile(), request.phoneNumber)


@expose(('api',))
@returns(EditProfileResponseTO)
@arguments(request=EditProfileRequestTO)
def editProfile(request):
    from rogerthat.bizz.system import edit_profile
    edit_profile(users.get_current_user(), request.name, request.first_name, request.last_name, request.avatar,
                 request.access_token, request.birthdate, request.gender, request.has_birthdate,
                 request.has_gender, users.get_current_mobile(), accept_missing=True)


@expose(('api',))
@returns(ListZipCodesResponseTO)
@arguments(request=ListZipCodesRequestTO)
def listZipCodes(request):
    app_id = users.get_current_app_id()
    app = get_app_by_id(app_id)
    if not app.country:
        logging.error('No country set for app %s', app_id)
        return ListZipCodesResponseTO(items=[])
    m = ProfileZipCodes.create_key(app.country).get()
    if not m:
        return ListZipCodesResponseTO(items=[])
    return ListZipCodesResponseTO(items=[ZipCodeTO(zip_code=z.zip_code, name=z.name) for z in m.zip_codes])


@expose(('api',))
@returns(ListStreetsResponseTO)
@arguments(request=ListStreetsRequestTO)
def listStreets(request):
    app = get_app_by_id(users.get_current_app_id())
    m = ProfileStreets.create_key(app.country, request.zip_code).get()
    return ListStreetsResponseTO(items=m.streets if m else [])


@expose(('api',))
@returns(GetProfileAddressesResponseTO)
@arguments(request=GetProfileAddressesRequestTO)
def getProfileAddresses(request):
    from rogerthat.bizz.system import get_profile_addresses
    app_user = users.get_current_user()
    return GetProfileAddressesResponseTO(items=get_profile_addresses(app_user))


@expose(('api',))
@returns(AddProfileAddressResponseTO)
@arguments(request=AddProfileAddressRequestTO)
def addProfileAddress(request):
    from rogerthat.bizz.system import add_profile_address
    app_user = users.get_current_user()
    address = add_profile_address(app_user, request)
    return AddProfileAddressResponseTO.from_model(address)


@expose(('api',))
@returns(UpdateProfileAddressResponseTO)
@arguments(request=UpdateProfileAddressRequestTO)
def updateProfileAddress(request):
    from rogerthat.bizz.system import update_profile_address
    app_user = users.get_current_user()
    address = update_profile_address(app_user, request)
    return UpdateProfileAddressResponseTO.from_model(address)


@expose(('api',))
@returns(DeleteProfileAddressesResponseTO)
@arguments(request=DeleteProfileAddressesRequestTO)
def deleteProfileAddresses(request):
    from rogerthat.bizz.system import delete_profile_addresses
    app_user = users.get_current_user()
    delete_profile_addresses(app_user, request.uids)
    return DeleteProfileAddressesResponseTO()


@expose(('api',))
@returns(GetProfilePhoneNumbersResponseTO)
@arguments(request=GetProfilePhoneNumbersRequestTO)
def getProfilePhoneNumbers(request):
    from rogerthat.bizz.system import get_profile_phone_numbers
    app_user = users.get_current_user()
    return GetProfilePhoneNumbersResponseTO(items=get_profile_phone_numbers(app_user))


@expose(('api',))
@returns(AddProfilePhoneNumberResponseTO)
@arguments(request=AddProfilePhoneNumberRequestTO)
def addProfilePhoneNumber(request):
    from rogerthat.bizz.system import add_profile_phone_number
    app_user = users.get_current_user()
    model = add_profile_phone_number(app_user, request)
    return AddProfilePhoneNumberResponseTO.from_model(model)


@expose(('api',))
@returns(UpdateProfilePhoneNumberResponseTO)
@arguments(request=UpdateProfilePhoneNumberRequestTO)
def updateProfilePhoneNumber(request):
    from rogerthat.bizz.system import update_profile_phone_number
    app_user = users.get_current_user()
    model = update_profile_phone_number(app_user, request)
    return UpdateProfilePhoneNumberResponseTO.from_model(model)


@expose(('api',))
@returns(DeleteProfilePhoneNumbersResponseTO)
@arguments(request=DeleteProfilePhoneNumbersRequestTO)
def deleteProfilePhoneNumbers(request):
    from rogerthat.bizz.system import delete_profile_phone_numbers
    app_user = users.get_current_user()
    delete_profile_phone_numbers(app_user, request.uids)
    return DeleteProfilePhoneNumbersResponseTO()


@expose(('api',))
@returns(GetJSEmbeddingResponseTO)
@arguments(request=GetJSEmbeddingRequestTO)
def getJsEmbedding(request):
    return GetJSEmbeddingResponseTO.fromDBJSEmbedding(JSEmbedding.all())


@expose(('api',))
@returns(GetAppAssetResponseTO)
@arguments(request=GetAppAssetRequestTO)
def getAppAsset(request):
    """
    Args:
        request (GetAppAssetRequestTO)
    """
    app_id = users.get_current_app_id()
    asset = AppAsset.get_by_app_id(app_id, request.kind)
    if not asset:
        asset = AppAsset.default_key(request.kind).get()
    if asset:
        serving_url = asset.serving_url
        scale_x = asset.scale_x
    else:
        serving_url = None
        scale_x = 0
    return GetAppAssetResponseTO(request.kind, serving_url, scale_x)


@expose(('api',))
@returns(GetEmbeddedAppsResponseTO)
@arguments(request=GetEmbeddedAppsRequestTO)
def getEmbeddedApps(request):
    # type: (GetEmbeddedAppsRequestTO) -> GetEmbeddedAppsResponseTO
    if MISSING.default(request.type, None):
        embedded_apps = get_embedded_apps_by_type(request.type)
    else:
        user_profile = get_user_profile(users.get_current_user())
        embedded_apps = get_embedded_apps_by_community(user_profile.community_id)
    return GetEmbeddedAppsResponseTO(embedded_apps=[EmbeddedAppTO.from_model(a) for a in embedded_apps])


@expose(('api',))
@returns(GetEmbeddedAppResponseTO)
@arguments(request=GetEmbeddedAppRequestTO)
def getEmbeddedApp(request):
    # type: (GetEmbeddedAppRequestTO) -> GetEmbeddedAppResponseTO
    embedded_app = get_embedded_application(request.name)
    return GetEmbeddedAppResponseTO.from_dict(embedded_app.to_dict())
