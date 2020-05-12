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

import time

from mcfw.properties import bool_property, long_property, long_list_property, unicode_property, \
    typed_property, unicode_list_property
from rogerthat.dal.app import get_apps_by_id
from rogerthat.models import UserProfileInfoAddress
from rogerthat.models.properties.profiles import PublicKeyTO
from rogerthat.pages.legal import DOC_TERMS, get_current_document_version
from rogerthat.to import TO, GeoPointTO
from rogerthat.to.profile import UserProfileTO


class ConsentSettingsTO(object):
    ask_tos = bool_property('1', default=False)
    ask_push_notifications = bool_property('2', default=False)
    
    @staticmethod
    def fromUserProfile(app_settings, user_profile):
        s = ConsentSettingsTO()
        tos_version = get_current_document_version(DOC_TERMS)
        if not app_settings or app_settings.tos_enabled:
            s.ask_tos = tos_version > user_profile.tos_version
        else:
            s.ask_tos = False
        s.ask_push_notifications = not user_profile.consent_push_notifications_shown
        return s


class SettingsTO(TO):
    recordPhoneCalls = bool_property('1')
    recordPhoneCallsDays = long_property('2')
    recordPhoneCallsTimeslot = long_list_property('3')
    recordGeoLocationWithPhoneCalls = bool_property('4')

    geoLocationTracking = bool_property('5')
    geoLocationTrackingDays = long_property('6')
    geoLocationTrackingTimeslot = long_list_property('7')
    geoLocationSamplingIntervalBattery = long_property('8')
    geoLocationSamplingIntervalCharging = long_property('9')

    useGPSBattery = bool_property('10')
    useGPSCharging = bool_property('11')
    xmppReconnectInterval = long_property('12')
    operatingVersion = long_property('13')

    version = long_property('15')

    # properties coming from AppSettings
    wifiOnlyDownloads = bool_property('16', default=False)
    backgroundFetchTimestamps = long_list_property('17', default=[])

    # properties coming from UserProfile
    consent = typed_property('18', ConsentSettingsTO, False, default=None)

    ATTRIBUTES = (u'geoLocationTracking', u'geoLocationTrackingDays', u'geoLocationTrackingTimeslot',
                  u'geoLocationSamplingIntervalBattery', u'geoLocationSamplingIntervalCharging', u'useGPSBattery',
                  u'useGPSCharging', u'recordPhoneCalls', u'recordPhoneCallsDays', u'recordPhoneCallsTimeslot',
                  u'recordGeoLocationWithPhoneCalls', u'xmppReconnectInterval')

    @staticmethod
    def fromDBSettings(app_settings, user_profile, mobile_settings):
        from rogerthat.models import MobileSettings
        s = SettingsTO()
        for att in SettingsTO.ATTRIBUTES:
            setattr(s, att, getattr(mobile_settings, att))
        if isinstance(mobile_settings, MobileSettings):
            mobile = mobile_settings.mobile
            if mobile.operatingVersion != None:
                s.operatingVersion = mobile.operatingVersion
            else:
                s.operatingVersion = 0
            s.version = mobile_settings.version
        else:
            s.operatingVersion = 0
            s.version = 1

        if app_settings:
            s.wifiOnlyDownloads = app_settings.wifi_only_downloads or False
            s.backgroundFetchTimestamps = app_settings.background_fetch_timestamps
        else:
            s.wifiOnlyDownloads = SettingsTO.wifiOnlyDownloads.default or False
            s.backgroundFetchTimestamps = SettingsTO.backgroundFetchTimestamps.default
        
        s.consent = ConsentSettingsTO.fromUserProfile(app_settings, user_profile)
        return s

    def apply(self, settings):  # @ReservedAssignment
        for att in SettingsTO.ATTRIBUTES:
            setattr(settings, att, getattr(self, att))
        settings.timestamp = int(time.time())


class WebMobileTO(TO):
    id = unicode_property('1')  # @ReservedAssignment
    description = unicode_property('2')
    hardwareModel = unicode_property('3')

    @staticmethod
    def from_model(model):
        return WebMobileTO(id=model.id, description=model.description, hardwareModel=model.hardwareModel)


class MobileTO(TO):
    id = unicode_property('id')
    type = unicode_property('type')
    description = unicode_property('description')
    hardware_model = unicode_property('hardware_model')
    registration_timestamp = long_property('registration_timestamp')
    os_version = unicode_property('os_version')
    language = unicode_property('language')

    @staticmethod
    def from_model(model):
        return MobileTO(id=model.id, type=model.type_string, description=model.description,
                        hardware_model=model.hardwareModel, registration_timestamp=model.registrationTimestamp,
                        os_version=model.osVersion, language=model.language)


class UserStatusTO(object):
    profile = typed_property('1', UserProfileTO, False)
    registered_mobile_count = long_property('2')
    has_avatar = bool_property('3')


class PushNotificationSettingsTO(object):
    enabled = bool_property('1', default=False)


class SaveSettingsRequest(object):
    callLogging = bool_property('1')
    tracking = bool_property('2')
    push_notifications = typed_property('3', PushNotificationSettingsTO, False, default=None)


class SaveSettingsResponse(TO):
    settings = typed_property('1', SettingsTO, False)


class IdentityTO(TO):
    email = unicode_property('email')
    name = unicode_property('name')
    firstName = unicode_property('firstName', default=None)
    lastName = unicode_property('lastName', default=None)
    avatarId = long_property('avatarId')
    qualifiedIdentifier = unicode_property('qualifiedIdentifier')
    birthdate = long_property('birthdate', default=0)
    gender = long_property('gender', default=0)
    hasBirthdate = bool_property('hasBirthdate', default=False)
    hasGender = bool_property('hasGender', default=False)
    profileData = unicode_property('profileData', default=None, doc="a JSON string containing extra profile fields")
    owncloudUri = unicode_property('owncloudUri')
    owncloudUsername = unicode_property('owncloudUsername')
    owncloudPassword = unicode_property('owncloudPassword')


class LogErrorRequestTO(object):
    mobicageVersion = unicode_property('1')
    platform = long_property('2')
    platformVersion = unicode_property('3')
    errorMessage = unicode_property('4')
    description = unicode_property('5')
    timestamp = long_property('6')


class LogErrorResponseTO(object):
    pass


class UnregisterMobileRequestTO(object):
    reason = unicode_property('1', default=None)


class UnregisterMobileResponseTO(object):
    pass


class HeartBeatRequestTO(object):
    majorVersion = long_property('1')
    minorVersion = long_property('2')
    product = unicode_property('3')
    flushBackLog = bool_property('4')
    timestamp = long_property('5')
    timezone = unicode_property('6')
    buildFingerPrint = unicode_property('7')
    SDKVersion = unicode_property('8')
    networkState = unicode_property('9')
    appType = long_property('10')
    simCountry = unicode_property('11')
    simCountryCode = unicode_property('12')
    simCarrierName = unicode_property('13')
    simCarrierCode = unicode_property('14')
    netCountry = unicode_property('15')
    netCountryCode = unicode_property('16')
    netCarrierName = unicode_property('17')
    netCarrierCode = unicode_property('18')
    localeLanguage = unicode_property('19')
    localeCountry = unicode_property('20')
    timezoneDeltaGMT = long_property('21')
    deviceModelName = unicode_property('22')
    embeddedApps = unicode_list_property('23')
    deviceId = unicode_property('24')


class HeartBeatResponseTO(object):
    systemTime = long_property('1')


class GetIdentityRequestTO(object):
    pass


class GetIdentityResponseTO(object):
    identity = typed_property('1', IdentityTO, False)
    shortUrl = unicode_property('2')


class ForwardLogsRequestTO(object):
    jid = unicode_property('1')


class ForwardLogsResponseTO(object):
    pass


class IdentityUpdateRequestTO(object):
    identity = typed_property('1', IdentityTO, False)


class IdentityUpdateResponseTO(object):
    pass


class EditProfileRequestTO(TO):
    name = unicode_property('name')
    first_name = unicode_property('first_name', default=None)
    last_name = unicode_property('last_name', default=None)
    avatar = unicode_property('avatar')  # base 64
    access_token = unicode_property('access_token')
    birthdate = long_property('birthdate', default=0)
    gender = long_property('gender', default=0)
    has_birthdate = bool_property('has_birthdate', default=False)
    has_gender = bool_property('has_gender', default=False)
    extra_fields = unicode_property('extra_fields', default=None, doc="a JSON string containing extra profile fields")


class EditProfileResponseTO(object):
    pass


class ZipCodeTO(TO):
    zip_code = unicode_property('1')
    name = unicode_property('2')


class ListZipCodesRequestTO(TO):
    pass


class ListZipCodesResponseTO(TO):
    items = typed_property('1', ZipCodeTO, True)


class ListStreetsRequestTO(TO):
    zip_code = unicode_property('2')


class ListStreetsResponseTO(TO):
    items = unicode_list_property('1')


class BaseProfileAddressTO(TO):
    type = long_property('type')
    label = unicode_property('2')
    geo_location = typed_property('3', GeoPointTO, False)
    distance = long_property('4')
    street_name = unicode_property('5')
    house_nr = unicode_property('6')
    bus_nr = unicode_property('7')
    zip_code = unicode_property('8')
    city = unicode_property('9')


class ProfileAddressTO(BaseProfileAddressTO):
    uid = unicode_property('1')

    @classmethod
    def from_model(cls, address):
        # type: (UserProfileInfoAddress) -> ProfileAddressTO
        return cls(uid=address.address_uid,
                   type=address.type,
                   label=address.label,
                   geo_location=GeoPointTO(lat=address.geo_location.lat, lon=address.geo_location.lon),
                   distance=address.distance,
                   street_name=address.street_name,
                   house_nr=address.house_nr,
                   bus_nr=address.bus_nr,
                   zip_code=address.zip_code,
                   city=address.city)


class GetProfileAddressesRequestTO(TO):
    pass


class GetProfileAddressesResponseTO(TO):
    items = typed_property('2', ProfileAddressTO, True)


class AddProfileAddressRequestTO(BaseProfileAddressTO):
    pass


class AddProfileAddressResponseTO(ProfileAddressTO):
    pass


class UpdateProfileAddressRequestTO(ProfileAddressTO):
    pass


class UpdateProfileAddressResponseTO(ProfileAddressTO):
    pass


class DeleteProfileAddressesRequestTO(TO):
    uids = unicode_list_property('1')


class DeleteProfileAddressesResponseTO(TO):
    pass


class BaseProfilePhoneNumberTO(TO):
    type = long_property('type')
    label = unicode_property('label')
    number = unicode_property('number')
    

class ProfilePhoneNumberTO(BaseProfilePhoneNumberTO):
    uid = unicode_property('1')
    
    @classmethod
    def from_model(cls, model):
        # type: (UserProfileInfoPhoneNumber) -> ProfilePhoneNumberTO
        return cls(uid=model.uid,
                   type=model.type,
                   label=model.label,
                   number=model.number)
    
    @staticmethod
    def compare_objects(obj1, obj2):
        from rogerthat.models import UserPhoneNumberType
        if obj1.type == UserPhoneNumberType.MOBILE:
            return -1
        if obj2.type == UserPhoneNumberType.MOBILE:
            return 1
        if obj1.type == UserPhoneNumberType.HOME:
            return -1
        if obj2.type == UserPhoneNumberType.HOME:
            return 1
        if obj1.type == UserPhoneNumberType.WORK:
            return -1
        if obj2.type == UserPhoneNumberType.WORK:
            return 1

        return -1 if sorted([obj1.label, obj2.label])[0] == obj1.label else 1

    def __lt__(self, other):
        return ProfilePhoneNumberTO.compare_objects(self, other) < 0

    def __gt__(self, other):
        return ProfilePhoneNumberTO.compare_objects(self, other) > 0


class GetProfilePhoneNumbersRequestTO(TO):
    pass


class GetProfilePhoneNumbersResponseTO(TO):
    items = typed_property('items', ProfilePhoneNumberTO, True)


class AddProfilePhoneNumberRequestTO(BaseProfilePhoneNumberTO):
    pass


class AddProfilePhoneNumberResponseTO(ProfilePhoneNumberTO):
    pass


class UpdateProfilePhoneNumberRequestTO(ProfilePhoneNumberTO):
    pass


class UpdateProfilePhoneNumberResponseTO(ProfilePhoneNumberTO):
    pass


class DeleteProfilePhoneNumbersRequestTO(TO):
    uids = unicode_list_property('1')


class DeleteProfilePhoneNumbersResponseTO(TO):
    pass


class UpdateSettingsRequestTO(object):
    settings = typed_property('1', SettingsTO, False)


class UpdateSettingsResponseTO(object):
    pass


class UpdateApplePushDeviceTokenRequestTO(object):
    token = unicode_property('1')


class UpdateApplePushDeviceTokenResponseTO(object):
    pass


class GetIdentityQRCodeRequestTO(object):
    email = unicode_property('1')
    size = unicode_property('2')


class GetIdentityQRCodeResponseTO(object):
    qrcode = unicode_property('1')
    shortUrl = unicode_property('2')


class SetMobilePhoneNumberRequestTO(object):
    phoneNumber = unicode_property('1')


class SetMobilePhoneNumberResponseTO(object):
    pass


class ServiceIdentityInfoTO(TO):
    name = unicode_property('1')
    email = unicode_property('2')
    avatar = unicode_property('3')
    admin_emails = unicode_list_property('4')
    description = unicode_property('5')
    app_ids = unicode_list_property('6')
    app_names = unicode_list_property('7')
    default_app = unicode_property('default_app')

    @classmethod
    def fromServiceIdentity(cls, service_identity):
        from rogerthat.utils.service import remove_slash_default
        apps = [a for a in get_apps_by_id(service_identity.appIds) if a]
        meta = [e.strip() for e in service_identity.metaData.split(',') if e.strip()]
        return ServiceIdentityInfoTO(
            name=service_identity.name,
            email=remove_slash_default(service_identity.user).email(),
            avatar=service_identity.avatarUrl,
            description=service_identity.description,
            default_app=service_identity.defaultAppId,
            app_ids=[app.app_id for app in apps],
            app_names=[app.name for app in apps],
            admin_emails=[] if service_identity.metaData is None else meta,
        )


class TranslationValueTO(object):
    language = unicode_property('1')
    value = unicode_property('2')


class TranslationTO(object):
    type = long_property('1')
    key = unicode_property('2')
    values = typed_property('3', TranslationValueTO, True)


class TranslationSetTO(object):
    email = unicode_property('1')
    export_id = long_property('2')
    translations = typed_property('3', TranslationTO, True)


class LanguagesTO(object):
    default_language = unicode_property('1')
    supported_languages = unicode_list_property('2')


class SetSecureInfoRequestTO(object):
    public_key = unicode_property('1', default=None)  # deprecated since public_keys
    public_keys = typed_property('2', PublicKeyTO, True, default=[])


class SetSecureInfoResponseTO(object):
    pass


class EmbeddedAppTranslationsTO(object):
    embedded_app = unicode_property('1')
    # json encoded { 'example_translation': 'Example translation'}
    translations = unicode_property('2')

    def __init__(self, embedded_app=None, translations=None):
        self.embedded_app = embedded_app
        self.translations = translations


class UpdateEmbeddedAppTranslationsRequestTO(object):
    translations = typed_property('1', EmbeddedAppTranslationsTO, True)

    def __init__(self, translations):
        self.translations = translations or []


class UpdateEmbeddedAppTranslationsResponseTO(object):
    pass


class ExportResultTO(object):
    download_url = unicode_property('download_url')
