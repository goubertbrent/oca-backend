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

from collections import namedtuple
import datetime
import hashlib
import json
import logging
import re
import time
import urllib
import urlparse
import uuid
import zlib

from google.appengine.ext import db, ndb
from google.appengine.ext.db import polymodel
from google.appengine.ext.ndb.polymodel import PolyModel as NdbPolyModel
from google.appengine.ext.ndb.query import QueryOptions

from dateutil.parser import parse as parse_date
from mcfw.cache import CachedModelMixIn, invalidate_cache, invalidate_model_cache
from mcfw.properties import azzert
from mcfw.serialization import deserializer, ds_model, register, s_model, s_long, ds_long, serializer, \
    model_deserializer, s_any, ds_any
from mcfw.utils import Enum
from rogerthat.consts import IOS_APPSTORE_WEB_URI_FORMAT, \
    ANDROID_MARKET_ANDROID_URI_FORMAT, ANDROID_MARKET_WEB_URI_FORMAT, ANDROID_BETA_MARKET_WEB_URI_FORMAT
from rogerthat.models.common import NdbModel
from rogerthat.models.properties import CompressedIntegerList
from rogerthat.models.properties.app import AutoConnectedServicesProperty, AutoConnectedService
from rogerthat.models.properties.forms import FormProperty
from rogerthat.models.properties.friend import FriendDetailsProperty, FriendDetailTO
from rogerthat.models.properties.keyvalue import KeyValueProperty, KVStore
from rogerthat.models.properties.messaging import ButtonsProperty, MemberStatusesProperty, JsFlowDefinitionsProperty, \
    AttachmentsProperty, SpecializedList, EmbeddedAppProperty, JsFlowDefinitionTO
from rogerthat.models.properties.oauth import OAuthSettingsProperty
from rogerthat.models.properties.profiles import MobileDetailsProperty, \
    MobileDetailsNdbProperty, MobileDetailTO
from rogerthat.models.utils import get_meta, add_meta
from rogerthat.rpc import users
from rogerthat.rpc.models import Mobile
from rogerthat.translations import DEFAULT_LANGUAGE
from rogerthat.utils import base38, base65, llist, now, calculate_age_from_date
from rogerthat.utils.crypto import sha256_hex, encrypt
from rogerthat.utils.translations import localize_app_translation
from typing import List


try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class AppServiceFilter(Enum):
    # Searching by services filters by country of the app
    COUNTRY = 0
    # Searching by services filters by 'community_ids' property of the app
    COMMUNITIES = 1


class App(CachedModelMixIn, db.Model):
    APP_ID_ROGERTHAT = u"rogerthat"
    APP_ID_OSA_LOYALTY = u"osa-loyalty"

    APP_TYPE_ROGERTHAT = 0
    APP_TYPE_CITY_APP = 1
    APP_TYPE_ENTERPRISE = 2
    APP_TYPE_CONTENT_BRANDING = 3
    APP_TYPE_YSAAA = 4
    APP_TYPE_SECURE_DEVICE = 100

    TYPE_STRINGS = {APP_TYPE_ROGERTHAT: u"Rogerthat",
                    APP_TYPE_CITY_APP: u"City app",
                    APP_TYPE_ENTERPRISE: u"Enterprise",
                    APP_TYPE_CONTENT_BRANDING: u"Content branding",
                    APP_TYPE_YSAAA: u"YSAAA",
                    APP_TYPE_SECURE_DEVICE: u"Secure device",
                    }

    name = db.StringProperty(indexed=False)
    type = db.IntegerProperty(indexed=True)
    core_branding_hash = db.StringProperty(indexed=False)
    facebook_registration_enabled = db.BooleanProperty(indexed=False)
    facebook_app_id = db.IntegerProperty(indexed=False)
    facebook_app_secret = db.StringProperty(indexed=False)
    ios_app_id = db.StringProperty(indexed=False)
    ios_dev_team = db.StringProperty(indexed=False)
    android_app_id = db.StringProperty(indexed=False)
    user_regex = db.TextProperty(indexed=False)
    visible = db.BooleanProperty(indexed=True, default=True)
    creation_time = db.IntegerProperty(indexed=False)
    apple_push_cert = db.TextProperty(indexed=False)
    apple_push_key = db.TextProperty(indexed=False)
    apple_push_cert_valid_until = db.IntegerProperty()
    apns_key = db.TextProperty(indexed=False)
    apns_key_id = db.TextProperty(indexed=False)
    is_default = db.BooleanProperty(indexed=True)
    qrtemplate_keys = db.StringListProperty(indexed=False)
    dashboard_email_address = db.StringProperty(indexed=False)
    contact_email_address = db.StringProperty(indexed=False)
    admin_services = db.StringListProperty()
    main_service = db.StringProperty(indexed=False)
    demo = db.BooleanProperty(indexed=True, default=False)
    beta = db.BooleanProperty(indexed=False, default=False)
    secure = db.BooleanProperty(indexed=False, default=False)
    mdp_client_id = db.StringProperty(indexed=False)
    mdp_client_secret = db.StringProperty(indexed=False)
    owncloud_base_uri = db.StringProperty(indexed=False)
    owncloud_admin_username = db.StringProperty(indexed=False)
    owncloud_admin_password = db.StringProperty(indexed=False)
    disabled = db.BooleanProperty(default=False)
    country = db.StringProperty()  # 2 letter country code
    default_app_name_mapping = db.TextProperty()
    # These ids are used to limit the communities the user can choose when using this app.
    # They may also be used to filter the services the user can view, depending on the value of service_filter_type.
    community_ids = db.ListProperty(long, default=[])  # type: List[int]
    service_filter_type = db.IntegerProperty(indexed=False, default=AppServiceFilter.COUNTRY,
                                             choices=AppServiceFilter.all())

    def invalidateCache(self):
        logging.info("App '%s' removed from cache." % self.app_id)
        invalidate_model_cache(self)

    def is_in_appstores(self):
        return self.android_app_id and self.ios_app_id

    @property
    def app_id(self):
        return self.key().name()

    @property
    def type_str(self):
        azzert(self.type in self.TYPE_STRINGS)
        return self.TYPE_STRINGS[self.type]

    @property
    def ios_appstore_web_uri(self):
        return IOS_APPSTORE_WEB_URI_FORMAT % self.ios_app_id

    @property
    def ios_appstore_ios_uri(self):
        return self.ios_appstore_web_uri

    @property
    def android_market_android_uri(self):
        if self.beta:
            return ANDROID_BETA_MARKET_WEB_URI_FORMAT % self.android_app_id
        return ANDROID_MARKET_ANDROID_URI_FORMAT % self.android_app_id

    @property
    def android_market_web_uri(self):
        if self.beta:
            return ANDROID_BETA_MARKET_WEB_URI_FORMAT % self.android_app_id
        return ANDROID_MARKET_WEB_URI_FORMAT % self.android_app_id

    @property
    def supports_mdp(self):
        return self.mdp_client_id and self.mdp_client_secret

    def get_contact_email_address(self):
        return self.contact_email_address or u"info@onzestadapp.be"

    @staticmethod
    def create_key(app_id):
        return db.Key.from_path(App.kind(), app_id)

    @classmethod
    def list_by_admin_service(cls, service_email):
        return cls.all().filter('admin_services', service_email)

    @classmethod
    def list_by_community_id(cls, community_id):
        return cls.all().filter('community_ids', community_id)


class AppNameMapping(NdbModel):
    app_id = ndb.StringProperty()

    @property
    def name(self):
        return self.key.id()

    @classmethod
    def create_key(cls, name):
        return ndb.Key(cls, name)

    @classmethod
    def list_by_app(cls, app_id):
        return cls.query().filter(cls.app_id == app_id)


class NdbApp(NdbModel):
    demo = ndb.BooleanProperty()

    @property
    def app_id(self):
        return self.key.id()

    @classmethod
    def _get_kind(cls):
        return App.kind()

    @classmethod
    def create_key(cls, app_id):
        return ndb.Key(cls, app_id)


class AppTranslations(db.Model):
    """
    Contains a json object in this format:
    translations['en']['translation'] = 'test'
    """
    translations = db.BlobProperty()

    @classmethod
    def create_key(cls, app_id):
        return db.Key.from_path(cls.kind(), cls.kind(), parent=App.create_key(app_id))

    @classmethod
    def get_or_create(cls, app_id):
        key = cls.create_key(app_id)
        translations = cls.get(key)
        if not translations:
            translations = AppTranslations(key=key)
            translations.put()
        return translations

    @classmethod
    def get_by_app_id(cls, app_id):
        return cls.get(cls.create_key(app_id))

    @property
    def translations_dict(self):
        translations_dict = getattr(self, '_translations_dict', None)
        if translations_dict is None:
            self._translations_dict = json.loads(zlib.decompress(self.translations)) if self.translations else None
        return self._translations_dict

    @property
    def app_id(self):
        return self.parent_key().name()

    def get_translation(self, lang, key, **kwargs):
        D = self.translations_dict
        if D is None:
            return None
        if not lang:
            lang = DEFAULT_LANGUAGE
        lang = lang.replace('-', '_')
        if lang not in D:
            if '_' in lang:
                lang = lang.split('_')[0]
                if lang not in D:
                    lang = DEFAULT_LANGUAGE
            else:
                lang = DEFAULT_LANGUAGE
        if lang not in D:
            return None
        langdict = D[lang]
        if key not in langdict:
            if lang == DEFAULT_LANGUAGE:
                return None
            # Fall back to default language
            logging.warn("App %s translation %s not found in language %s - fallback to default", self.app_id,
                         key, lang)
            lang = DEFAULT_LANGUAGE
            if lang not in D:
                return None
            langdict = D[lang]
        if key not in langdict:
            return None
        return langdict[key] % kwargs


class UserLocation(db.Model):
    members = db.ListProperty(users.User)
    geoPoint = db.GeoPtProperty(indexed=False)
    accuracy = db.IntegerProperty(indexed=False)
    timestamp = db.IntegerProperty(indexed=False)

    @property
    def user(self):
        return users.User(self.key().name())


class _Settings(db.Model):
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 4
    THURSDAY = 8
    FRIDAY = 16
    SATERDAY = 32
    SUNDAY = 64

    WORK_DAYS = MONDAY | TUESDAY | WEDNESDAY | THURSDAY | FRIDAY
    ALL_DAYS = WORK_DAYS | SATERDAY | SUNDAY

    user = db.UserProperty()
    timestamp = db.IntegerProperty()
    recordPhoneCalls = db.BooleanProperty()
    recordPhoneCallsDays = db.IntegerProperty()
    recordPhoneCallsTimeslot = db.ListProperty(int)
    recordGeoLocationWithPhoneCalls = db.BooleanProperty()
    geoLocationTracking = db.BooleanProperty()
    geoLocationTrackingDays = db.IntegerProperty()
    geoLocationTrackingTimeslot = db.ListProperty(int)
    geoLocationSamplingIntervalBattery = db.IntegerProperty()
    geoLocationSamplingIntervalCharging = db.IntegerProperty()
    useGPSBattery = db.BooleanProperty()
    useGPSCharging = db.BooleanProperty()
    xmppReconnectInterval = db.IntegerProperty()


class Settings(_Settings):
    MINIMUM_INTERVAL = 15 * 60

    @staticmethod
    def get(user=None):
        if not user:
            user = users.get_current_user()
        db_settings = Settings.all().filter("user =", user).get()
        if not db_settings:
            db_settings = Settings()
            db_settings.user = user
            db_settings.timestamp = int(time.time())
            db_settings.recordPhoneCalls = True
            db_settings.recordPhoneCallsDays = Settings.WORK_DAYS
            db_settings.recordPhoneCallsTimeslot = [0, (24 * 3600) - 1]
            db_settings.recordGeoLocationWithPhoneCalls = True
            db_settings.geoLocationTracking = True
            db_settings.geoLocationTrackingDays = Settings.ALL_DAYS
            db_settings.geoLocationTrackingTimeslot = [0, (24 * 3600) - 1]
            db_settings.geoLocationSamplingIntervalBattery = Settings.MINIMUM_INTERVAL
            db_settings.geoLocationSamplingIntervalCharging = Settings.MINIMUM_INTERVAL
            db_settings.useGPSBattery = False
            db_settings.useGPSCharging = True
            # 15 minutes in order to able to join up with others on android
            db_settings.xmppReconnectInterval = Settings.MINIMUM_INTERVAL
            db_settings.put()
        return db_settings


class MobileSettings(CachedModelMixIn, _Settings):
    mobile = db.ReferenceProperty(Mobile)
    color = db.StringProperty()
    majorVersion = db.IntegerProperty()
    minorVersion = db.IntegerProperty()
    lastHeartBeat = db.IntegerProperty()
    version = db.IntegerProperty(default=1)

    @staticmethod
    def get(mobile=None):
        # TODO: would be better if we knew the key of MobileSettings
        if mobile is None:
            mobile = users.get_current_mobile()
        mob_settings = MobileSettings.all().filter("mobile =", mobile.key()).get()
        if not mob_settings:
            user_settings = Settings.get(mobile.user)
            mob_settings = MobileSettings()
            mob_settings.user = mobile.user
            mob_settings.mobile = mobile
            mob_settings.timestamp = int(time.time())
            mob_settings.recordPhoneCalls = True
            mob_settings.recordPhoneCallsDays = user_settings.recordPhoneCallsDays
            mob_settings.recordPhoneCallsTimeslot = user_settings.recordPhoneCallsTimeslot
            mob_settings.recordGeoLocationWithPhoneCalls = user_settings.recordGeoLocationWithPhoneCalls
            mob_settings.geoLocationTracking = user_settings.geoLocationTracking
            mob_settings.geoLocationTrackingDays = user_settings.geoLocationTrackingDays
            mob_settings.geoLocationTrackingTimeslot = user_settings.geoLocationTrackingTimeslot
            mob_settings.geoLocationSamplingIntervalBattery = user_settings.geoLocationSamplingIntervalBattery
            mob_settings.geoLocationSamplingIntervalCharging = user_settings.geoLocationSamplingIntervalCharging
            mob_settings.useGPSBattery = user_settings.useGPSBattery
            mob_settings.useGPSCharging = user_settings.useGPSCharging
            mob_settings.xmppReconnectInterval = user_settings.xmppReconnectInterval
            mob_settings.color = u"#000000"
            mob_settings.majorVersion = 0
            mob_settings.minorVersion = 0
            mob_settings.lastHeartBeat = 0
            mob_settings.put()
        return mob_settings

    def invalidateCache(self):
        from rogerthat.dal.mobile import get_mobile_settings_cached
        logging.info("MobileSettings %s removed from cache.", self.mobile.user)
        get_mobile_settings_cached.invalidate_cache(self.mobile)  # @UndefinedVariable


@deserializer
def ds_mobile_settings(stream):
    return ds_any(stream)


@serializer
def s_mobile_settings(stream, ms):
    s_any(stream, ms)


register(MobileSettings, s_mobile_settings, ds_mobile_settings)


class CellTower(db.Model):
    cid = db.IntegerProperty()
    lac = db.IntegerProperty()
    net = db.IntegerProperty()
    geoPoint = db.GeoPtProperty()


class Image(ndb.Model):
    blob = ndb.BlobProperty()

    @property
    def id(self):
        return self.key.id()

    @classmethod
    def create_key(cls, image_id):
        return ndb.Key(cls, image_id)

    @classmethod
    def url(cls, base_url, image_id):
        if base_url and image_id:
            return u'%s/unauthenticated/image/%d' % (base_url, image_id)
        return None


class Avatar(db.Model):
    user = db.UserProperty()
    picture = db.BlobProperty()


class FriendMap(db.Model):
    shareContacts = db.BooleanProperty(default=True)
    friends = db.ListProperty(users.User)
    friendDetails = FriendDetailsProperty()
    friend_details_json = db.TextProperty()
    generation = db.IntegerProperty()
    version = db.IntegerProperty(indexed=False, default=0)  # bumped every time a friend is added/removed
    
    _tmp_friend_details = None

    @property
    def user(self):
        return users.User(self.parent_key().name())

    @classmethod
    def create_key(cls, app_user):
        from rogerthat.dal import parent_key
        return db.Key.from_path(cls.kind(), app_user.email(), parent=parent_key(app_user))

    @classmethod
    def get_by_app_user(cls, app_user):
        return cls.get(cls.create_key(app_user))

    @classmethod
    def create(cls, app_user):
        return cls(key=cls.create_key(app_user), generation=0, friends=list(), friendDetails=None, friend_details_json=None)
    
    def get_friend_details(self):
        if self._tmp_friend_details is None:
            data = json.loads(self.friend_details_json) if self.friend_details_json else {}
            result = {}
            if data:
                for email, value in data.iteritems():
                    result[email] = FriendDetailTO.from_dict(value)
            elif self.friendDetails:
                for friend_detail in self.friendDetails.values():
                    result[friend_detail.email] = friend_detail
            self._tmp_friend_details = result
        return self._tmp_friend_details

    def save_friend_details(self, data):
        result = {}
        for email, value in data.iteritems():
            result[email] = value.to_dict()
        self.friend_details_json = json.dumps(result)
        self._tmp_friend_details = data
         
    def get_friend_detail_by_email(self, email):
        data = self.get_friend_details()
        if email in data:
            return data[email]
        return None

class UserData(db.Model):
    data = db.TextProperty()
    userData = KeyValueProperty() # deprecated and migrated via job (lazy also works)

    @property
    def service_identity_user(self):
        return users.User(self.key().name())

    @property
    def app_user(self):
        return users.User(self.parent_key().name())

    @classmethod
    def createKey(cls, app_user, service_identity_user):
        from rogerthat.dal import parent_key
        azzert('/' in service_identity_user.email(), 'no slash in %s' % service_identity_user.email())
        return db.Key.from_path(cls.kind(), service_identity_user.email(), parent=parent_key(app_user))


class FriendServiceIdentityConnection(db.Model):
    friend_name = db.StringProperty()  # duplicate info - for performance + listing all users
    friend_avatarId = db.IntegerProperty(indexed=False)  # duplicate info - for performance
    service_identity_email = db.StringProperty()  # Needed to find all humans connected to a svc
    app_id = db.StringProperty(indexed=True, default=App.APP_ID_ROGERTHAT)  # Needed for querying
    # TODO remove after migration _009_nuke_broadcast (models with deleted == True will be deleted)
    deleted = db.BooleanProperty(indexed=True)

    # Should always construct using this factory method
    @classmethod
    def create(cls, friend_user, friend_name, friend_avatarId, service_identity_user, app_id):
        return cls(key=cls.createKey(friend_user, service_identity_user),
                   friend_name=friend_name,
                   friend_avatarId=friend_avatarId,
                   service_identity_email=service_identity_user.email(),
                   app_id=app_id)

    @classmethod
    def createKey(cls, friend_user, service_identity_user):
        from rogerthat.dal import parent_key
        azzert('/' in service_identity_user.email(), 'no slash in %s' % service_identity_user.email())
        return db.Key.from_path(cls.kind(), service_identity_user.email(), parent=parent_key(friend_user))

    @property
    def service_identity_user(self):
        return users.User(self.key().name())

    @property
    def friend(self):
        return users.User(self.parent_key().name())

    @classmethod
    def list(cls, service_identity_email, keys_only=False):
        return cls.all(keys_only=keys_only) \
            .filter('service_identity_email', service_identity_email) \
            .order('friend_name')

    @classmethod
    def list_by_app_id(cls, service_identity_email, app_id):
        return cls.all() \
            .filter('service_identity_email', service_identity_email) \
            .filter('app_id', app_id) \
            .order('friend_name')

    @classmethod
    def list_by_app_user(cls, app_user, keys_only=False):
        from rogerthat.dal import parent_key
        return cls.all(keys_only=keys_only).ancestor(parent_key(app_user))


class FriendInvitationHistory(db.Model):
    # parent_key of invitor user or invitor service_identity
    # key = invited user or service_identity
    inviteTimestamps = db.ListProperty(int, indexed=False)
    tag = db.StringProperty(indexed=False)
    lastAttemptKey = db.StringProperty()

    @staticmethod
    def create(invitor_user, invitee_user):
        return FriendInvitationHistory(key=FriendInvitationHistory.createKey(invitor_user, invitee_user))

    @staticmethod
    def createKey(invitor_user, invitee_user):
        from rogerthat.dal import parent_key_unsafe
        from rogerthat.utils.service import remove_slash_default
        # Do not azzert /
        return db.Key.from_path(FriendInvitationHistory.kind(),
                                remove_slash_default(invitee_user).email(),
                                parent=parent_key_unsafe(remove_slash_default(invitor_user)))

    @property
    def user(self):
        return users.User(self.parent_key().name())

    @property
    def invitee(self):
        return users.User(self.key().name())


class DoNotSendMeMoreInvites(db.Model):
    pass


class Code(db.Model):
    author = db.UserProperty()
    timestamp = db.IntegerProperty()
    name = db.StringProperty()
    source = db.TextProperty()
    functions = db.StringListProperty()
    version = db.IntegerProperty()


class BaseProfile(CachedModelMixIn):

    def invalidateCache(self):
        from rogerthat.dal.profile import _get_db_profile, _get_ndb_profile
        logging.info("Profile %s removed from cache.", self.user)
        _get_db_profile.invalidate_cache(self.user)  # @UndefinedVariable
        _get_ndb_profile.invalidate_cache(self.user)  # @UndefinedVariable

    def updateCache(self):
        from rogerthat.dal.profile import _get_db_profile, _get_ndb_profile
        logging.info("Updating %s profile cache.", self.user)
        _get_db_profile.update_cache(self.user, _data=self)  # @UndefinedVariable
        _get_ndb_profile.update_cache(self.user, _data=self)  # @UndefinedVariable

    @property
    def avatarUrl(self):
        from rogerthat.settings import get_server_settings
        return u"%s/unauthenticated/mobi/cached/avatar/%s" % (get_server_settings().baseUrl, self.avatarId)

    def get_avatar_url(self, base_url):
        return u'%s/unauthenticated/mobi/cached/avatar/%s' % (base_url, self.avatarId)


class Profile(BaseProfile, polymodel.PolyModel):
    avatarId = db.IntegerProperty(indexed=False, default=-1)
    avatarHash = db.StringProperty(indexed=False)
    passwordHash = db.StringProperty(indexed=False)
    lastUsedMgmtTimestamp = db.IntegerProperty(indexed=False, default=0)
    country = db.StringProperty(indexed=False)
    timezone = db.StringProperty(indexed=False)
    timezoneDeltaGMT = db.IntegerProperty(indexed=False)
    tos_version = db.IntegerProperty(indexed=True, default=0)
    community_id = db.IntegerProperty() # todo communities

    @classmethod
    def createKey(cls, user):
        from rogerthat.dal import parent_key
        return db.Key.from_path(cls.kind(), user.email(), parent=parent_key(user))

    @property
    def user(self):
        return users.User(self.parent_key().name())


class NdbProfile(BaseProfile, NdbPolyModel):
    # since we're mixing ndb with db we need to handle the cache ourselves
    _use_cache = False
    _use_memcache = False
    avatarId = ndb.IntegerProperty(indexed=False, default=-1)
    avatarHash = ndb.StringProperty(indexed=False)
    passwordHash = ndb.StringProperty(indexed=False)
    lastUsedMgmtTimestamp = ndb.IntegerProperty(indexed=False, default=0)
    country = ndb.StringProperty(indexed=False)
    timezone = ndb.StringProperty(indexed=False)
    timezoneDeltaGMT = ndb.IntegerProperty(indexed=False)
    tos_version = ndb.IntegerProperty(indexed=True, default=0)
    community_id = ndb.IntegerProperty() # todo communities

    @classmethod
    def createKey(cls, user):
        return ndb.Key.from_old_key(Profile.createKey(user))  # @UndefinedVariable

    @property
    def user(self):
        return users.User(self.key.parent().id())

    @classmethod
    def _get_kind(cls):
        return Profile.kind()

    @classmethod
    def _class_name(cls):
        return cls._get_kind()

    @classmethod
    def _class_key(cls):
        return [cls._get_kind()]

    def _pre_put_hook(self):
        raise Exception('Use db instead of NdbProfile')


class ProfileInfo(object):

    @property
    def isServiceIdentity(self):
        raise Exception("Illegal method")


class BaseUserProfile(ProfileInfo):
    GENDER_MALE_OR_FEMALE = 0
    GENDER_MALE = 1
    GENDER_FEMALE = 2
    GENDER_CUSTOM = 3
    _GENDER_STRINGS = {GENDER_MALE_OR_FEMALE: u"MALE_OR_FEMALE",
                       GENDER_MALE: u"MALE",
                       GENDER_FEMALE: u"FEMALE",
                       GENDER_CUSTOM: u"CUSTOM"}

    @property
    def isServiceIdentity(self):
        return False

    @property
    def age(self):
        return calculate_age_from_date(
            datetime.date.fromtimestamp(self.birthdate)) if self.birthdate is not None else None

    @property
    def gender_str(self):
        if self.gender is None:
            return None
        azzert(self.gender in self._GENDER_STRINGS)
        return self._GENDER_STRINGS[self.gender]

    @classmethod
    def gender_from_string(cls, gender_str):
        for k, v in cls._GENDER_STRINGS.iteritems():
            if gender_str == v:
                return k
        return None

    @property
    def grants(self):
        if not hasattr(self, '_grants'):
            grants = {}
            for service_role in self.service_roles or []:
                service, role = service_role.split(':')
                roles = grants.setdefault(service, [])
                roles.append(role)
            self._grants = grants
        return self._grants

    def _update_grants(self):
        if hasattr(self, '_grants'):
            service_roles = []
            for service_identity, roles in self._grants.iteritems():
                for role in set(roles):
                    service_roles.append(u'%s:%s' % (service_identity, role))
            self.service_roles = service_roles

    def has_role(self, service_identity_user, role):
        service_identity = service_identity_user.email()
        azzert('/' in service_identity)
        return service_identity in self.grants and role in self.grants[service_identity]

    def grant_role(self, service_identity_user, role):
        service_identity_email = service_identity_user.email()
        azzert('/' in service_identity_email)
        self.grants.setdefault(service_identity_email, []).append(role)
        self._update_grants()

    def revoke_role(self, service_identity_user, role, skip_warning=False):
        service_identity_email = service_identity_user.email()
        azzert('/' in service_identity_email)
        if not self.has_role(service_identity_user, role):
            if not skip_warning:
                logging.warn('Cannot revoke role %s for service %s from user %s', role, service_identity_email,
                             self.user)
            return
        self.grants[service_identity_email].remove(role)
        self._update_grants()

    @classmethod
    def get_birth_day_int(cls, timestamp):
        birthdate = datetime.datetime.utcfromtimestamp(timestamp)
        month = birthdate.month * 100
        day = birthdate.day
        return month + day


class NdbUserProfile(NdbProfile, ProfileInfo):
    name = ndb.StringProperty(indexed=False)
    first_name = ndb.StringProperty(indexed=False)
    last_name = ndb.StringProperty(indexed=False)
    qualifiedIdentifier = ndb.StringProperty()
    language = ndb.StringProperty(indexed=False)
    mobiles = MobileDetailsNdbProperty()
    mobiles_json = db.TextProperty()
    ysaaa = ndb.BooleanProperty(indexed=False, default=False)
    birthdate = ndb.IntegerProperty(indexed=False)
    birth_day = ndb.IntegerProperty()  # 815 -> august 15
    gender = ndb.IntegerProperty(indexed=False)
    service_roles = ndb.StringProperty(repeated=True)  # <service_email>>:<role_id>
    version = ndb.IntegerProperty(indexed=False,
                                  default=0)  # bumped every time that FriendTO-related properties are updated
    app_id = ndb.StringProperty(indexed=True, default=App.APP_ID_ROGERTHAT)  # Needed for querying
    profileData = ndb.TextProperty()  # a JSON string containing extra profile fields
    unsubscribed_from_reminder_email = ndb.BooleanProperty(indexed=False, default=False)
    owncloud_password = ndb.StringProperty(indexed=False)

    isCreatedForService = ndb.BooleanProperty(indexed=False, default=False)
    owningServiceEmails = ndb.StringProperty(indexed=True, repeated=True)

    consent_push_notifications_shown = ndb.BooleanProperty(indexed=True, default=False)
    
    _tmp_mobiles = None
    
    def get_mobiles(self):
        if self._tmp_mobiles is None:
            data = json.loads(self.mobiles_json) if self.mobiles_json else {}
            result = {}
            if data:
                for account, value in data.iteritems():
                    result[account] = MobileDetailTO.from_dict(value)
            elif self.mobiles:
                for md in self.mobiles.values():
                    result[md.account] = md
            self._tmp_mobiles = result
        return self._tmp_mobiles

    def save_mobiles(self, data):
        logging.debug("saving mobiles not supported in ndb")
        raise NotImplementedError()

    @classmethod
    def list_by_app(cls, app_id, keys_only=False):
        qry = cls.query(default_options=QueryOptions(keys_only=keys_only))
        qry = qry.filter(cls.app_id == app_id)
        return qry

    @classmethod
    def _get_kind(cls):
        return 'Profile'

    @classmethod
    def _class_name(cls):
        return 'UserProfile'

    @classmethod
    def _class_key(cls):
        return ['Profile', 'UserProfile']

    @classmethod
    def list_by_community(cls, community_id):
        return cls.query(cls.community_id == community_id)


class UserProfile(Profile, BaseUserProfile):
    name = db.StringProperty(indexed=False)
    first_name = db.StringProperty(indexed=False)
    last_name = db.StringProperty(indexed=False)
    qualifiedIdentifier = db.StringProperty()
    language = db.StringProperty(indexed=False)
    mobiles = MobileDetailsProperty()
    mobiles_json = db.TextProperty()
    ysaaa = db.BooleanProperty(indexed=False, default=False)
    birthdate = db.IntegerProperty(indexed=False)
    birth_day = db.IntegerProperty()  # 815 -> august 15
    gender = db.IntegerProperty(indexed=False)
    service_roles = db.StringListProperty()  # <service_email>>:<role_id>
    version = db.IntegerProperty(indexed=False,
                                 default=0)  # bumped every time that FriendTO-related properties are updated
    # TODO communities: remove usage of app_id
    # todo lets keep the app_id property for the index and future cleanup of apps
    app_id = db.StringProperty(indexed=True, default=App.APP_ID_ROGERTHAT)  # Needed for querying
    profileData = db.TextProperty()  # a JSON string containing extra profile fields
    unsubscribed_from_reminder_email = db.BooleanProperty(indexed=False, default=False)
    owncloud_password = db.StringProperty(indexed=False)

    isCreatedForService = db.BooleanProperty(indexed=False, default=False)
    owningServiceEmails = db.StringListProperty(indexed=True)

    consent_push_notifications_shown = db.BooleanProperty(indexed=True, default=False)
    home_screen_id = db.StringProperty(default=u'default')
    
    _tmp_mobiles = None
    
    def get_mobiles(self):
        if self._tmp_mobiles is None:
            data = json.loads(self.mobiles_json) if self.mobiles_json else {}
            result = {}
            if data:
                for account, value in data.iteritems():
                    result[account] = MobileDetailTO.from_dict(value)
            elif self.mobiles:
                for md in self.mobiles.values():
                    result[md.account] = md
            self._tmp_mobiles = result
        return self._tmp_mobiles

    def save_mobiles(self, data):
        result = {}
        for account, value in data.iteritems():
            result[account] = value.to_dict()
        self.mobiles_json = json.dumps(result)
        self._tmp_mobiles = data

    @classmethod
    def list_by_birth_day(cls, timestamp):
        """
        Args:
            timestamp (long): current day timestamp
        Returns:
            user_profile_query (db.Query)
        """
        # Prevent additional index by filtering on 'Profile' instead of UserProfile
        return Profile.all().filter('birth_day', cls.get_birth_day_int(timestamp))

    @classmethod
    def list_by_roles(cls, app_id, service_roles):
        return cls.all().filter('app_id', app_id).filter('service_roles IN', service_roles)

    @classmethod
    def list_by_service_role_email(cls, service_user_email):
        return cls.all() \
            .filter('service_roles >=', service_user_email + '/') \
            .filter('service_roles <', service_user_email + u'/\ufffd')

    @classmethod
    def list_by_community(cls, community_id, keys_only=False):
        return cls.all(keys_only=keys_only).filter('community_id', community_id)


class UserAddressType(Enum):
    OTHER = 0
    HOME = 1
    WORK = 2


class UserProfileInfoAddress(NdbModel):
    created = ndb.DateTimeProperty(indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True)

    address_uid = ndb.StringProperty()  # hash of the complete address
    street_uid = ndb.StringProperty()  # hash of the country_code, city, zip_code and street_name

    label = ndb.StringProperty(indexed=False)

    geo_location = ndb.GeoPtProperty(indexed=False)  # type: ndb.GeoPt
    distance = ndb.IntegerProperty(indexed=False)
    type = ndb.IntegerProperty(default=UserAddressType.OTHER, choices=UserAddressType.all())

    street_name = ndb.StringProperty(indexed=False)
    house_nr = ndb.StringProperty(indexed=False)
    bus_nr = ndb.StringProperty(indexed=False)
    zip_code = ndb.StringProperty(indexed=False)
    city = ndb.StringProperty(indexed=False)
    country_code = ndb.StringProperty(indexed=False)

    @staticmethod
    def create_uid(items):
        digester = hashlib.sha256()
        for i in items:
            v = i.encode('utf8') if isinstance(i, unicode) else i
            digester.update(v.upper())
        return digester.hexdigest().upper()


class UserPhoneNumberType(Enum):
    OTHER = 0
    HOME = 1
    WORK = 2
    MOBILE = 3


class UserProfileInfoPhoneNumber(NdbModel):
    created = ndb.DateTimeProperty(indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True)

    type = ndb.IntegerProperty(default=UserPhoneNumberType.OTHER, choices=UserPhoneNumberType.all())
    label = ndb.TextProperty(indexed=False)
    number = ndb.StringProperty(indexed=False)

    @property
    def uid(self):
        return UserProfileInfoPhoneNumber.create_uid([str(self.type), self.number])

    @staticmethod
    def create_uid(items):
        digester = hashlib.sha256()
        for i in items:
            v = i.encode('utf8') if isinstance(i, unicode) else i
            digester.update(v.upper())
        return digester.hexdigest().upper()


class UserProfileInfo(NdbModel):
    addresses = ndb.StructuredProperty(UserProfileInfoAddress, repeated=True)  # type: list[UserProfileInfoAddress]
    phone_numbers = ndb.StructuredProperty(UserProfileInfoPhoneNumber, repeated=True)  # type: list[UserProfileInfoPhoneNumber]

    @property
    def app_user(self):
        return users.User(self.key.id())

    @classmethod
    def create_key(cls, app_user):
        from rogerthat.dal import parent_ndb_key
        return ndb.Key(cls,
                       app_user.email(),
                       parent=parent_ndb_key(app_user))

    @classmethod
    def list_by_address_uid(cls, address_uid):
        return cls.query().filter(cls.addresses.address_uid == address_uid)

    @classmethod
    def list_by_street_uid(cls, street_uid):
        return cls.query().filter(cls.addresses.street_uid == street_uid)

    def get_address(self, address_uid):
        for a in self.addresses:
            if a.address_uid == address_uid:
                return a
        return None

    def get_phone_number(self, uid):
        for m in self.phone_numbers:
            if m.uid == uid:
                return m
        return None


class UserConsentHistory(NdbModel):
    TYPE_TOS = u'tos'
    TYPE_PUSH_NOTIFICATIONS = u'push_notifications'

    timestamp = ndb.DateTimeProperty(auto_now_add=True)
    consent_type = ndb.StringProperty()
    data = ndb.JsonProperty(compressed=True)


class NdbFacebookUserProfile(NdbUserProfile):
    profile_url = ndb.StringProperty(indexed=False)
    access_token = ndb.StringProperty(indexed=False)

    @classmethod
    def _get_kind(cls):
        return 'Profile'

    @classmethod
    def _class_name(cls):
        return 'FacebookUserProfile'

    @classmethod
    def _class_key(cls):
        return ['Profile', 'UserProfile', 'FacebookUserProfile']


class FacebookUserProfile(UserProfile):
    profile_url = db.StringProperty(False)
    access_token = db.StringProperty(False)


class BaseServiceProfile(object):
    CALLBACK_APP_INSTALLATION_PROGRESS = 1 << 21
    CALLBACK_FORM_SUBMITTED = 1 << 22
    CALLBACK_FRIEND_INVITE_RESULT = 1
    CALLBACK_FRIEND_INVITED = 1 << 1
    CALLBACK_FRIEND_BROKE_UP = 1 << 2
    CALLBACK_FRIEND_IS_IN_ROLES = 1 << 11
    CALLBACK_FRIEND_UPDATE = 1 << 13
    CALLBACK_FRIEND_LOCATION_FIX = 1 << 16
    CALLBACK_FRIEND_REGISTER = 1 << 17
    CALLBACK_FRIEND_REGISTER_RESULT = 1 << 18
    CALLBACK_MESSAGING_RECEIVED = 1 << 3
    CALLBACK_MESSAGING_POKE = 1 << 4
    CALLBACK_MESSAGING_ACKNOWLEDGED = 1 << 7
    CALLBACK_MESSAGING_FLOW_MEMBER_RESULT = 1 << 6
    CALLBACK_MESSAGING_FORM_ACKNOWLEDGED = 1 << 5
    CALLBACK_MESSAGING_NEW_CHAT_MESSAGE = 1 << 12
    CALLBACK_MESSAGING_CHAT_DELETED = 1 << 15
    CALLBACK_MESSAGING_LIST_CHAT_MESSAGES = 1 << 20
    CALLBACK_SYSTEM_API_CALL = 1 << 8
    CALLBACK_SYSTEM_SERVICE_DELETED = 1 << 14
    CALLBACK_SYSTEM_BRANDINGS_UPDATED = 1 << 19
    CALLBACK_NEWS_CREATED = 1 << 23
    CALLBACK_NEWS_UPDATED = 1 << 24
    CALLBACK_NEWS_DELETED = 1 << 25

    CALLBACKS = (CALLBACK_APP_INSTALLATION_PROGRESS, CALLBACK_FRIEND_INVITE_RESULT, CALLBACK_FRIEND_INVITED, CALLBACK_FRIEND_BROKE_UP,
                 CALLBACK_MESSAGING_RECEIVED, CALLBACK_MESSAGING_POKE, CALLBACK_MESSAGING_FLOW_MEMBER_RESULT,
                 CALLBACK_MESSAGING_ACKNOWLEDGED, CALLBACK_MESSAGING_FORM_ACKNOWLEDGED, CALLBACK_SYSTEM_API_CALL,
                 CALLBACK_SYSTEM_SERVICE_DELETED, CALLBACK_SYSTEM_BRANDINGS_UPDATED, CALLBACK_FRIEND_IS_IN_ROLES,
                 CALLBACK_FRIEND_UPDATE, CALLBACK_MESSAGING_NEW_CHAT_MESSAGE, CALLBACK_MESSAGING_CHAT_DELETED,
                 CALLBACK_FRIEND_LOCATION_FIX, CALLBACK_FRIEND_REGISTER, CALLBACK_FRIEND_REGISTER_RESULT,
                 CALLBACK_FORM_SUBMITTED, CALLBACK_NEWS_CREATED, CALLBACK_NEWS_UPDATED, CALLBACK_NEWS_DELETED)

    DEFAULT_CALLBACKS = CALLBACK_FRIEND_INVITE_RESULT | CALLBACK_FRIEND_INVITED | CALLBACK_FRIEND_BROKE_UP | \
        CALLBACK_FRIEND_UPDATE | CALLBACK_MESSAGING_POKE | CALLBACK_MESSAGING_RECEIVED | \
        CALLBACK_MESSAGING_FLOW_MEMBER_RESULT | CALLBACK_MESSAGING_ACKNOWLEDGED |  \
        CALLBACK_MESSAGING_FORM_ACKNOWLEDGED | CALLBACK_SYSTEM_API_CALL | CALLBACK_FORM_SUBMITTED

    ORGANIZATION_TYPE_UNSPECIFIED = -1
    ORGANIZATION_TYPE_NON_PROFIT = 1
    ORGANIZATION_TYPE_PROFIT = 2
    ORGANIZATION_TYPE_CITY = 3
    ORGANIZATION_TYPE_EMERGENCY = 4
    ORGANIZATION_TYPES = [ORGANIZATION_TYPE_UNSPECIFIED, ORGANIZATION_TYPE_NON_PROFIT, ORGANIZATION_TYPE_PROFIT,
                          ORGANIZATION_TYPE_CITY, ORGANIZATION_TYPE_EMERGENCY]
    # don't forget to update ServiceProfile.localizedOrganizationType when adding an organization type

    ORGANIZATION_TYPE_TRANSLATION_KEYS = {
        ORGANIZATION_TYPE_NON_PROFIT: 'Associations',
        ORGANIZATION_TYPE_PROFIT: 'Merchants',
        ORGANIZATION_TYPE_CITY: 'Community Services',
        ORGANIZATION_TYPE_EMERGENCY: 'Care',
        ORGANIZATION_TYPE_UNSPECIFIED: 'Services',
    }

    ORGANIZATION_TYPE_ICONS = {
        ORGANIZATION_TYPE_NON_PROFIT: 'fa-users',
        ORGANIZATION_TYPE_PROFIT: 'fa-shopping-bag',
        ORGANIZATION_TYPE_CITY: '',
        ORGANIZATION_TYPE_EMERGENCY: 'fa-heart',
        ORGANIZATION_TYPE_UNSPECIFIED: '',
    }

    @property
    def usesHttpCallback(self):
        return self.callBackURI is not None

    def callbackEnabled(self, callback):
        return self.callbacks & callback == callback

    @property
    def defaultLanguage(self):
        return self.supportedLanguages[0]

    @property
    def service_user(self):
        return self.user

    def localizedOrganizationType(self, language, app_id):
        return self.localized_plural_organization_type(self.organizationType, language, app_id)

    @staticmethod
    def localized_plural_organization_type(organization_type, language, app_id):
        translation_keys = BaseServiceProfile.ORGANIZATION_TYPE_TRANSLATION_KEYS
        if organization_type not in translation_keys:
            raise ValueError('Missing translation for organizationType %s' % organization_type)
        return localize_app_translation(language, translation_keys[organization_type], app_id)

    @staticmethod
    def localized_singular_organization_type(organization_type, language, app_id):
        translation_keys = {
            ServiceProfile.ORGANIZATION_TYPE_NON_PROFIT: 'association',
            ServiceProfile.ORGANIZATION_TYPE_PROFIT: 'merchant',
            ServiceProfile.ORGANIZATION_TYPE_CITY: 'community_service',
            ServiceProfile.ORGANIZATION_TYPE_EMERGENCY: 'Care',
            ServiceProfile.ORGANIZATION_TYPE_UNSPECIFIED: 'service',
        }

        if organization_type not in translation_keys:
            raise ValueError('Missing translation for organizationType %s' % organization_type)
        return localize_app_translation(language, translation_keys[organization_type], app_id)


class NdbServiceProfile(NdbProfile, BaseServiceProfile):
    callBackURI = ndb.StringProperty(indexed=False)
    sik = ndb.StringProperty(indexed=False)
    enabled = ndb.BooleanProperty(indexed=False)
    testCallNeeded = ndb.BooleanProperty(indexed=False, default=True)
    testValue = ndb.StringProperty(indexed=False)
    callbacks = ndb.IntegerProperty(indexed=False,
                                    default=BaseServiceProfile.DEFAULT_CALLBACKS)
    lastWarningSent = ndb.IntegerProperty(indexed=False)
    aboutMenuItemLabel = ndb.StringProperty(indexed=False)
    messagesMenuItemLabel = ndb.StringProperty(indexed=False)
    shareMenuItemLabel = ndb.StringProperty(indexed=False)
    callMenuItemLabel = ndb.StringProperty(indexed=False)
    languages = ndb.StringProperty(name='supportedLanguages', indexed=False, repeated=True)
    activeTranslationSet = ndb.StringProperty(indexed=False)
    editableTranslationSet = ndb.StringProperty(indexed=False)
    solution = ndb.StringProperty(indexed=False)
    monitor = ndb.BooleanProperty(indexed=True)
    autoUpdating = ndb.BooleanProperty(indexed=False, default=False)  # Auto-updates suspended by default
    updatesPending = ndb.BooleanProperty(indexed=False, default=False)
    category_id = ndb.StringProperty(indexed=False)
    organizationType = ndb.IntegerProperty(indexed=False, default=BaseServiceProfile.ORGANIZATION_TYPE_PROFIT)
    version = ndb.IntegerProperty(indexed=False,
                                  default=0)  # bumped every time that FriendTO-related properties are updated
    expiredAt = ndb.IntegerProperty(default=0)

    @property
    def supportedLanguages(self):
        return self.languages or [DEFAULT_LANGUAGE]

    @supportedLanguages.setter
    def supportedLanguages(self, supportedLanguages):
        self.languages = supportedLanguages

    @classmethod
    def _get_kind(cls):
        return 'Profile'

    @classmethod
    def _class_name(cls):
        return 'ServiceProfile'

    @classmethod
    def _class_key(cls):
        return ['Profile', 'ServiceProfile']

    @classmethod
    def list_by_community(cls, community_id):
        return cls.query(cls.community_id == community_id)


class ServiceProfile(Profile, BaseServiceProfile):
    callBackURI = db.StringProperty(indexed=False)
    sik = db.StringProperty(indexed=False)
    enabled = db.BooleanProperty(indexed=False)
    testCallNeeded = db.BooleanProperty(indexed=False, default=True)
    testValue = db.StringProperty(indexed=False)
    callbacks = db.IntegerProperty(indexed=False,
                                   default=BaseServiceProfile.DEFAULT_CALLBACKS)
    lastWarningSent = db.IntegerProperty(indexed=False)
    aboutMenuItemLabel = db.StringProperty(indexed=False)
    messagesMenuItemLabel = db.StringProperty(indexed=False)
    shareMenuItemLabel = db.StringProperty(indexed=False)
    callMenuItemLabel = db.StringProperty(indexed=False)
    supportedLanguages = db.StringListProperty(indexed=False, default=[DEFAULT_LANGUAGE])
    activeTranslationSet = db.StringProperty(indexed=False)
    editableTranslationSet = db.StringProperty(indexed=False)
    solution = db.StringProperty(indexed=False)
    monitor = db.BooleanProperty(indexed=True)
    autoUpdating = db.BooleanProperty(indexed=False, default=False)  # Auto-updates suspended by default
    updatesPending = db.BooleanProperty(indexed=False, default=False)
    category_id = db.StringProperty(indexed=False)
    organizationType = db.IntegerProperty(indexed=False, default=BaseServiceProfile.ORGANIZATION_TYPE_PROFIT)
    version = db.IntegerProperty(indexed=False,
                                 default=0)  # bumped every time that FriendTO-related properties are updated
    expiredAt = db.IntegerProperty(default=0)


class ServiceCallBackConfig(NdbModel):
    created = ndb.DateTimeProperty()
    updated = ndb.DateTimeProperty()
    name = ndb.TextProperty()
    uri = ndb.TextProperty()
    regexes = ndb.TextProperty(repeated=True)
    callbacks = ndb.IntegerProperty(default=-1)
    custom_headers = ndb.JsonProperty(default=None)

    def is_regex_match(self, tag):
        for regex in self.regexes:
            if re.match(regex, tag):
                return True
        return False

    def is_callback_enabled(self, callback):
        if self.callbacks == -1:
            return False
        return self.callbacks & callback == callback


class ServiceCallBackSettings(NdbModel):
    configs = ndb.LocalStructuredProperty(ServiceCallBackConfig, repeated=True)  # type: List[ServiceCallBackConfig]

    def get_config(self, name):
        for config in self.configs:
            if config.name == name:
                return config
        return None

    @classmethod
    def create_key(cls, service_user):
        from rogerthat.dal import parent_ndb_key
        return ndb.Key(cls,
                       service_user.email(),
                       parent=parent_ndb_key(service_user))


class ServiceCallBackConfiguration(db.Model):
    creationTime = db.IntegerProperty(indexed=False)
    regex = db.TextProperty(indexed=False)
    callBackURI = db.StringProperty(indexed=False)

    @property
    def name(self):
        return self.key().name()

    @property
    def service_user(self):
        return users.User(self.parent_key().name())

    @classmethod
    def create_key(cls, name, service_user):
        from rogerthat.dal import parent_key
        return db.Key.from_path(cls.kind(), name, parent=parent_key(service_user))


class ProfileHashIndex(db.Model):
    user = db.UserProperty(indexed=False, required=True)

    @classmethod
    def create(cls, user):
        from rogerthat.utils import hash_user_identifier
        user_hash = hash_user_identifier(user)
        return cls(key=ProfileHashIndex.create_key(user_hash), user=user)

    @classmethod
    def create_key(cls, user_hash):
        return db.Key.from_path(cls.kind(), user_hash)


class ServiceRole(db.Model):
    TYPE_MANAGED = 'managed'
    TYPE_SYNCED = 'synced'
    TYPES = (TYPE_MANAGED, TYPE_SYNCED)

    name = db.StringProperty()
    creationTime = db.IntegerProperty(indexed=False)
    type = db.StringProperty()

    @property
    def service_user(self):
        return users.User(self.parent_key().name())

    @property
    def role_id(self):
        return self.key().id()

    @classmethod
    def create_key(cls, service_user, role_id):
        # type: (users.User, int) -> db.Key
        from rogerthat.dal import parent_key
        azzert(isinstance(role_id, (int, long)))
        return db.Key.from_path(cls.kind(), role_id, parent=parent_key(service_user))


# TODO: remove FriendCategory, it's basically unused
class FriendCategory(db.Model):
    name = db.StringProperty(indexed=False)
    avatar = db.BlobProperty()

    @staticmethod
    def create_new_key():
        return db.Key.from_path(FriendCategory.kind(), str(uuid.uuid4()))

    @property
    def id(self):
        return self.key().name()


class ServiceAPIFailures(db.Model):
    creationTime = db.IntegerProperty(indexed=False)
    failedCalls = db.IntegerProperty(indexed=False)
    failedCallBacks = db.IntegerProperty(indexed=False)

    @property
    def service_user(self):
        return users.User(self.parent_key().name())

    @staticmethod
    def key_from_service_user_email(service_user_email):
        from rogerthat.dal import parent_key
        return db.Key.from_path(ServiceAPIFailures.kind(), service_user_email,
                                parent=parent_key(users.User(service_user_email)))


class ServiceIdentity(CachedModelMixIn, db.Model, ProfileInfo):
    # In service entity group
    # KeyName will be identity identifier
    DEFAULT = u'+default+'
    FLAG_INHERIT_DESCRIPTION = 1 << 0
    FLAG_INHERIT_DESCRIPTION_BRANDING = 1 << 1
    FLAG_INHERIT_MENU_BRANDING = 1 << 2
    FLAG_INHERIT_PHONE_NUMBER = 1 << 3
    FLAG_INHERIT_PHONE_POPUP_TEXT = 1 << 4
    FLAG_INHERIT_SEARCH_CONFIG = 1 << 5
    FLAG_INHERIT_EMAIL_STATISTICS = 1 << 6
    FLAG_INHERIT_APP_IDS = 1 << 7
    FLAG_INHERIT_HOME_BRANDING = 1 << 8

    DEFAULT_FLAGS_INHERIT = FLAG_INHERIT_DESCRIPTION | FLAG_INHERIT_DESCRIPTION_BRANDING | FLAG_INHERIT_MENU_BRANDING | \
        FLAG_INHERIT_PHONE_NUMBER | FLAG_INHERIT_PHONE_POPUP_TEXT | FLAG_INHERIT_SEARCH_CONFIG | \
        FLAG_INHERIT_EMAIL_STATISTICS | FLAG_INHERIT_APP_IDS | FLAG_INHERIT_HOME_BRANDING

    name = db.StringProperty(indexed=False)
    qualifiedIdentifier = db.StringProperty()
    description = db.TextProperty()
    descriptionBranding = db.StringProperty(indexed=False)
    menuGeneration = db.IntegerProperty(indexed=False, default=0)
    menuBranding = db.StringProperty(indexed=False)
    mainPhoneNumber = db.StringProperty(indexed=False)
    shareSIDKey = db.StringProperty(indexed=False)
    shareEnabled = db.BooleanProperty(indexed=False)
    callMenuItemConfirmation = db.StringProperty(indexed=False)
    inheritanceFlags = db.IntegerProperty(indexed=False, default=0)
    creationTimestamp = db.IntegerProperty(indexed=False, default=1353906000)
    metaData = db.StringProperty(indexed=False)
    appData = db.TextProperty()  # deprecated, lazily migrated to serviceData when putting service_data
    serviceData = KeyValueProperty()
    emailStatistics = db.BooleanProperty(indexed=True, default=False)
    version = db.IntegerProperty(indexed=False,
                                 default=0)  # bumped every time that FriendTO-related properties are updated
    # TODO communities: remove usages & remove after migration
    defaultAppId = db.StringProperty(indexed=False)
    # TODO communities: remove usages (use community.default_app instead)
    appIds = db.StringListProperty(indexed=True, default=[App.APP_ID_ROGERTHAT])
    contentBrandingHash = db.StringProperty(indexed=False)
    homeBrandingHash = db.StringProperty(indexed=False)

    def invalidateCache(self):
        from rogerthat.dal.service import get_service_identity
        logging.info("Svc Identity %s removed from cache." % self.user.email())
        invalidate_cache(get_service_identity, self.user)
        if self.is_default:
            logging.info("Svc Identity %s removed from cache." % self.service_user.email())
            invalidate_cache(get_service_identity, self.service_user)

    @property
    def avatarId(self):
        from rogerthat.dal.profile import get_service_profile
        return get_service_profile(self.service_user).avatarId

    @property
    def avatarUrl(self):
        from rogerthat.dal.profile import get_service_profile
        return get_service_profile(self.service_user).avatarUrl

    @property
    def supportedLanguages(self):
        from rogerthat.dal.profile import get_service_profile
        return get_service_profile(self.service_user).supportedLanguages

    @property
    def isServiceIdentity(self):
        return True

    @property
    def identifier(self):
        return self.key().name()

    @property
    def is_default(self):
        return ServiceIdentity.DEFAULT == self.identifier

    @property
    def service_user(self):
        return users.User(self.parent_key().name())

    @property
    def user(self):
        from rogerthat.utils.service import create_service_identity_user
        return create_service_identity_user(self.service_user, self.identifier)

    @property
    def service_identity_user(self):
        return self.user

    @property
    def app_id(self):
        # TODO communities: remove usages (use community.default_app instead)
        if self.defaultAppId:
            return self.defaultAppId
        return self.appIds[0]

    @staticmethod
    def isDefaultServiceIdentityUser(service_identity_user):
        from rogerthat.utils.service import get_identity_from_service_identity_user
        return get_identity_from_service_identity_user(service_identity_user) == ServiceIdentity.DEFAULT

    @classmethod
    def keyFromUser(cls, service_identity_user):
        from rogerthat.utils.service import get_service_identity_tuple
        azzert("/" in service_identity_user.email())
        service_user, identifier = get_service_identity_tuple(service_identity_user)
        return cls.keyFromService(service_user, identifier)

    @staticmethod
    def keyFromService(service_user, identifier):
        from rogerthat.dal import parent_key
        azzert("/" not in service_user.email())
        return db.Key.from_path(ServiceIdentity.kind(), identifier, parent=parent_key(service_user))


def _validate_opening_time(prop, value):
    if value is None or len(value) == 4:
        return value

    raise ValueError('OpeningHour.time should be None or have length 4. Got "%s".' % value)


def _validate_day(prop, value):
    if 0 <= value <= 6:
        return value
    raise ValueError('%s must be a number between 0 and 6' % prop)


class OpeningHour(NdbModel):
    day = ndb.IntegerProperty(indexed=False, validator=_validate_day)
    time = ndb.TextProperty(validator=_validate_opening_time)

    @property
    def datetime(self):
        return self.time and datetime.time(hour=int(self.time[:2]), minute=int(self.time[2:]))

    @classmethod
    def from_to(cls, to):
        if not to:
            return None
        return cls(day=to.day, time=to.time)


class OpeningPeriod(NdbModel):
    # open contains a pair of day and time objects describing when the place opens:
    open = ndb.LocalStructuredProperty(OpeningHour)  # type: OpeningHour
    # close may contain a pair of day and time objects describing when the place closes.
    close = ndb.LocalStructuredProperty(OpeningHour)  # type: OpeningHour
    # Note: If a place is always open, close will be None.
    # Always-open is represented as an open period containing day with value 0 and time with value 0000, and no close.
    description = ndb.TextProperty()
    description_color = ndb.TextProperty()

    @property
    def is_open_24_hours(self):
        # type: () -> bool
        # If a place is open on a day for 24 hours, close will be None and the time is 0000
        return not self.close and self.open.time == '0000'

    @classmethod
    def from_to(cls, period):
        return cls(close=OpeningHour.from_to(period.close),
                   open=OpeningHour.from_to(period.open),
                   description=period.description,
                   description_color=period.description_color)


def _validate_description_color(prop, value):
    try:
        if value is None or len(value) == 6 and int(value, 16):
            return value
    except ValueError:
        pass
    raise ValueError('%s must be 6 letter hex string' % prop)


class OpeningHourException(NdbModel):
    start_date = ndb.DateProperty()
    end_date = ndb.DateProperty()
    description = ndb.TextProperty()
    description_color = ndb.TextProperty(validator=_validate_description_color)
    # If periods is empty -> closed
    periods = ndb.LocalStructuredProperty(OpeningPeriod, repeated=True)  # type: List[OpeningPeriod]

    @classmethod
    def from_to(cls, to):
        return cls(start_date=parse_date(to.start_date).date(),
                   end_date=parse_date(to.end_date).date(),
                   description=to.description,
                   description_color=to.description_color,
                   periods=[OpeningPeriod.from_to(period) for period in to.periods])


class OpeningHours(NdbModel):
    TYPE_TEXTUAL = u'textual'
    TYPE_STRUCTURED = u'structured'
    TYPE_NOT_RELEVANT = u'not_relevant'
    TYPES = (TYPE_TEXTUAL, TYPE_STRUCTURED, TYPE_NOT_RELEVANT)

    type = ndb.TextProperty(choices=TYPES)
    text = ndb.TextProperty()
    title = ndb.TextProperty()  # Useful for when a service has multiple opening hours (for different departments)
    periods = ndb.LocalStructuredProperty(OpeningPeriod, repeated=True)  # type: List[OpeningPeriod]
    exceptional_opening_hours = ndb.LocalStructuredProperty(OpeningHourException,
                                                            repeated=True)  # type: List[OpeningHourException]

    @property
    def id(self):
        return self.key.id().decode('utf-8')

    @classmethod
    def create_key(cls, service_user, identity):
        from rogerthat.dal import parent_ndb_key
        return ndb.Key(cls, identity, parent=parent_ndb_key(service_user))

    def sort_dates(self):
        # Ensures the periods are sorted from monday to sunday
        def _sort_period(period):
            if period.open.day == 0:
                return 7, period.open.datetime
            return period.open.day, period.open.datetime

        self.periods = sorted(self.periods, key=_sort_period)
        self.exceptional_opening_hours = sorted(self.exceptional_opening_hours, key=lambda e: e.start_date)
        for exception in self.exceptional_opening_hours:
            exception.periods = sorted(exception.periods, key=_sort_period)

    def sanitize_periods(self):
        # Removes duplicate 'open 24 hours' entries and ensures only 1 entry when a day is open 24h
        open_all_day = {period.open.day for period in self.periods if period.is_open_24_hours}
        open_all_day_entries = []
        for period in reversed(self.periods):
            open_day = period.open.day
            if period.is_open_24_hours:
                if open_day in open_all_day_entries:
                    self.periods.remove(period)
                else:
                    open_all_day_entries.append(open_day)
            elif open_day in open_all_day:
                self.periods.remove(period)

    def _pre_put_hook(self):
        self.sanitize_periods()
        self.sort_dates()


class ServiceTranslationSet(db.Model):
    # key path:
    #    mc-i18n - service_user_email
    #       ServiceTranslationSet - str(timestamp)
    ACTIVE = 0
    EDITABLE = 1
    SYNCING = 2
    ARCHIVED = 3

    description = db.StringProperty(indexed=False)
    status = db.IntegerProperty(indexed=False,
                                choices=[ACTIVE, EDITABLE, SYNCING, ARCHIVED])
    latest_export_timestamp = db.IntegerProperty(indexed=False)

    @property
    def service_user(self):
        return users.User(self.parent_key().name())

    @staticmethod
    def create_editable_set(service_user):
        creation_timestamp = now()
        # TODO: use parent_key function and migrate existing data. Then remove xg=True in
        sts = ServiceTranslationSet(parent=db.Key.from_path(u'mc-i18n', service_user.email()),
                                    key_name=str(creation_timestamp))
        sts.description = "Service translation set created at %s" % time.ctime(creation_timestamp)
        sts.status = ServiceTranslationSet.EDITABLE
        return sts


class ServiceTranslation(db.Model):
    # parent object = ServiceTranslationSet
    # key name = str(translation_type)
    #
    # zipped_translations is zipped json string of all translations of a certain type (e.g. MFLOW_TEXT)
    #   Key is string in default language of that service, value is (possibly incomplete/None) dict with translations
    #
    #   { u"How are you" : { "fr": u"Comment ca va?", "nl": u"Hoe gaat het?" },
    #     u"Cancel"      : { "fr": u"Annuler",        "nl": u"Annuleren"     },
    #     u"Incomplete"  : None,
    #   }
    #
    MFLOW_TEXT = 1
    MFLOW_BUTTON = 2
    MFLOW_FORM = 3
    MFLOW_POPUP = 4
    MFLOW_BRANDING = 5
    MFLOW_JAVASCRIPT_CODE = 6
    HOME_TEXT = 101
    HOME_BRANDING = 102
    IDENTITY_TEXT = 201
    IDENTITY_BRANDING = 202
    SID_BUTTON = 301
    BRANDING_CONTENT = 501

    MFLOW_TYPES = [MFLOW_TEXT, MFLOW_BUTTON, MFLOW_FORM, MFLOW_POPUP, MFLOW_BRANDING]
    MFLOW_TYPES_ALLOWING_LANGUAGE_FALLBACK = [MFLOW_BRANDING]
    HOME_TYPES = [HOME_TEXT, HOME_BRANDING]
    IDENTITY_TYPES = [IDENTITY_TEXT, IDENTITY_BRANDING]
    BRANDING_TYPES = [BRANDING_CONTENT]

    TYPE_MAP = {MFLOW_BRANDING: 'Message flow message branding',
                MFLOW_BUTTON: 'Message flow button caption',
                MFLOW_FORM: 'Message flow widget setting',
                MFLOW_POPUP: 'Message flow button action',
                MFLOW_TEXT: 'Message flow text',
                MFLOW_JAVASCRIPT_CODE: 'Message flow code',
                IDENTITY_BRANDING: 'Service identity branding',
                IDENTITY_TEXT: 'Service identity text',
                HOME_BRANDING: 'Service menu item branding',
                HOME_TEXT: 'Service menu item label',
                SID_BUTTON: 'QR code button caption',
                BRANDING_CONTENT: 'Branding content'}

    zipped_translations = db.BlobProperty()

    @property
    def service_translation_set(self):
        return self.parent()

    @property
    def translation_type(self):
        return int(self.key().name())

    @property
    def translation_dict(self):
        return json.loads(zlib.decompress(self.zipped_translations))

    @staticmethod
    def create(service_translation_set, translation_type, translation_dict):
        st = ServiceTranslation(parent=service_translation_set, key_name=str(translation_type))
        st.zipped_translations = zlib.compress(json.dumps(translation_dict))
        return st

    @staticmethod
    def create_key(service_translation_set, translation_type):
        return db.Key.from_path('ServiceTranslation', str(translation_type), parent=service_translation_set.key())


@deserializer
def ds_profile(stream):
    type_ = ds_long(stream)
    if type_ == 1:
        return ds_model(stream, FacebookUserProfile)
    elif type_ == 3:
        return ds_model(stream, UserProfile)
    elif type_ == 4:
        return ds_model(stream, ServiceProfile)
    else:
        raise ValueError("Unknown type code: %s" % type_)


@serializer
def s_profile(stream, profile):
    if isinstance(profile, FacebookUserProfile):
        s_long(stream, 1)
        s_model(stream, profile, FacebookUserProfile)
    elif isinstance(profile, UserProfile):
        s_long(stream, 3)
        s_model(stream, profile, UserProfile)
    elif isinstance(profile, ServiceProfile):
        s_long(stream, 4)
        s_model(stream, profile, ServiceProfile)
    else:
        raise ValueError(
            "profile is not instance of expected type Facebook/User/Service Profile, but %s" % profile.__class__.__name__)


register(Profile, s_profile, ds_profile)

register(NdbProfile, s_any, ds_any)


@deserializer
def ds_service_identity(stream):
    return ds_model(stream, ServiceIdentity)


@serializer
def s_service_identity(stream, svc_identity):
    s_model(stream, svc_identity, ServiceIdentity)


register(ServiceIdentity, s_service_identity, ds_service_identity)


@deserializer
def ds_app(stream):
    return ds_model(stream, App)


@serializer
def s_app(stream, app):
    s_model(stream, app, App)


register(App, s_app, ds_app)


class SearchConfig(db.Model):
    DEFAULT_KEY = "SEARCH"
    enabled = db.BooleanProperty(indexed=False)
    keywords = db.TextProperty()

    @classmethod
    def create_key(cls, service_identity_user):
        return db.Key.from_path(cls.kind(), cls.DEFAULT_KEY, parent=ServiceIdentity.keyFromUser(service_identity_user))

    @property
    def service_identity_user(self):
        from rogerthat.utils.service import create_service_identity_user
        si_key = self.key().parent()
        return create_service_identity_user(users.User(si_key.parent().name()), si_key.name())


class SearchConfigLocation(db.Model):
    address = db.TextProperty()
    lat = db.IntegerProperty(indexed=False)
    lon = db.IntegerProperty(indexed=False)


class ServiceAdmin(db.Model):
    user = db.UserProperty()

    @property
    def service(self):
        return users.User(self.parent_key().name())


class MyDigiPassState(db.Model):
    state = db.StringProperty(indexed=False)
    creation_time = db.DateTimeProperty(indexed=False, auto_now_add=True)

    @property
    def user(self):
        return users.User(self.key().name())

    @classmethod
    def create_key(cls, app_user):
        from rogerthat.dal import parent_key
        return db.Key.from_path(cls.kind(), app_user.email(), parent=parent_key(app_user))


class MyDigiPassProfilePointer(db.Model):
    user = db.UserProperty()
    access_token = db.StringProperty(indexed=False)

    @property
    def mdpUUID(self):
        return self.key().name()

    @property
    def profile(self):
        from rogerthat.dal import parent_key
        return Profile.get_by_key_name(self.user.email(), parent_key(self.user))

    @classmethod
    def create(cls, app_user, mdp_uuid):
        from rogerthat.dal import parent_key
        return cls(key_name=mdp_uuid, parent=parent_key(app_user))

    @classmethod
    def get_by_user(cls, app_user):
        from rogerthat.dal import parent_key
        return cls.all().ancestor(parent_key(app_user)).get()


class OpenIdSettings(NdbModel):
    PROVIDER_ITSME = 'itsme'

    client_id = ndb.StringProperty(indexed=False)
    signature_private_key = ndb.JsonProperty()
    encryption_private_key = ndb.JsonProperty()
    configuration_url = ndb.StringProperty(indexed=False)
    data = ndb.JsonProperty()

    @classmethod
    def create_key(cls, provider, name):
        return ndb.Key(cls, '%s-%s' % (provider, name))


class OAuthState(NdbModel):
    creation_time = ndb.DateTimeProperty(auto_now_add=True)
    redirect_url = ndb.StringProperty(indexed=False)
    user = ndb.StringProperty()
    app_id = ndb.StringProperty()
    scope = ndb.StringProperty()
    token = ndb.JsonProperty()

    @property
    def state(self):
        return self.key.id()

    @classmethod
    def create_key(cls, state):
        return ndb.Key(cls, state)

    @classmethod
    def list_before_date(cls, date):
        return cls.query(cls.creation_time < date)


class FacebookProfilePointer(db.Model):
    user = db.UserProperty()

    @property
    def facebookId(self):
        return self.key().name()

    @property
    def profile(self):
        from rogerthat.dal import parent_key
        return Profile.get_by_key_name(self.user.email(), parent_key(self.user))


class FacebookDiscoveryInvite(db.Model):

    @property
    def from_(self):
        return users.User(self.parent_key().name())

    @property
    def to(self):
        return users.User(self.key().name())


class ProfilePointer(db.Model):
    user = db.UserProperty(
        indexed=False)  # can be human user (invite), or service user (e.g. for ServiceInteractionDefs), or service identity user (invite)
    short_url_id = db.IntegerProperty(indexed=False)

    @staticmethod
    def get(user_code):
        return ProfilePointer.get_by_key_name(user_code)

    @staticmethod
    def create(user):
        from rogerthat.bizz.friends import userCode
        from rogerthat.bizz.profile import create_short_url
        from rogerthat.utils.service import remove_slash_default
        user = remove_slash_default(user)
        user_code = userCode(user)
        return ProfilePointer(key_name=user_code, user=user, short_url_id=create_short_url(user_code))

    @staticmethod
    def create_key(user):
        from rogerthat.bizz.friends import userCode
        from rogerthat.utils.service import remove_slash_default
        user = remove_slash_default(user)
        user_code = userCode(user)
        return db.Key.from_path(ProfilePointer.kind(), user_code)


class ProfileDiscoveryResult(db.Model):
    TYPE_GRAVATAR = 1
    TYPE_FACEBOOK = 2
    TYPE_TWITTER = 3
    TYPE_LINKEDIN = 4

    TYPES = (TYPE_GRAVATAR, TYPE_FACEBOOK, TYPE_TWITTER)

    type = db.IntegerProperty(indexed=False)
    account = db.StringProperty(indexed=False)
    name = db.StringProperty(indexed=False)
    data = db.TextProperty()
    avatar = db.BlobProperty()
    timestamp = db.IntegerProperty()

    @property
    def user(self):
        return users.User(self.parent_key().name())


class ShortURL(db.Model):
    full = db.StringProperty(indexed=False)

    @staticmethod
    def get(id_):
        return ShortURL.get_by_id(id_)

    def qr_code_content_with_base_url(self, base_url):
        return '%s/S/%s' % (base_url, base38.encode_int(self.key().id()))

    @property
    def user_code(self):
        return self.full[4:]


class APIKey(CachedModelMixIn, db.Model):
    user = db.UserProperty()
    timestamp = db.IntegerProperty(indexed=False)
    name = db.StringProperty(indexed=False)
    mfr = db.BooleanProperty(default=False)

    def invalidateCache(self):
        from rogerthat.dal.service import get_api_key, get_mfr_api_key
        get_api_key.invalidate_cache(self.api_key)  # @PydevCodeAnalysisIgnore @UndefinedVariable
        get_mfr_api_key.invalidate_cache(self.user)  # @PydevCodeAnalysisIgnore @UndefinedVariable

    @property
    def api_key(self):
        return self.key().name()


@deserializer
def ds_apikey(stream):
    return model_deserializer(stream, APIKey)


register(APIKey, s_model, ds_apikey)


class SIKKey(CachedModelMixIn, db.Model):
    user = db.UserProperty()

    def invalidateCache(self):
        from rogerthat.dal.service import get_sik
        get_sik.invalidate_cache(self.key().name())  # @PydevCodeAnalysisIgnore @UndefinedVariable


@deserializer
def ds_sikkey(stream):
    return model_deserializer(stream, SIKKey)


register(SIKKey, s_model, ds_sikkey)


class MFRSIKey(CachedModelMixIn, db.Model):
    sik = db.StringProperty(indexed=False)

    def invalidateCache(self):
        from rogerthat.dal.service import get_mfr_sik
        get_mfr_sik.invalidate_cache(users.User(self.key().name()))  # @PydevCodeAnalysisIgnore @UndefinedVariable


@deserializer
def ds_mfrsikkey(stream):
    return model_deserializer(stream, MFRSIKey)


register(MFRSIKey, s_model, ds_mfrsikkey)


class BrandingEditorConfiguration(db.Model):
    color_scheme = db.StringProperty(indexed=False)
    background_color = db.StringProperty(indexed=False)
    text_color = db.StringProperty(indexed=False)
    menu_item_color = db.StringProperty(indexed=False)
    static_content = db.TextProperty()
    static_content_mode = db.StringProperty(indexed=False)

    @staticmethod
    def create_key(branding_hash, service_user):
        from rogerthat.dal import parent_key
        return db.Key.from_path(BrandingEditorConfiguration.kind(), branding_hash, parent=parent_key(service_user))

    @property
    def service_user(self):
        return users.User(self.parent_key().name())


class Branding(CachedModelMixIn, db.Model):
    TYPE_NORMAL = 1  # This branding can be used for messages/menu/screenBranding/descriptionBranding
    TYPE_APP = 2  # This branding contains an app.html and can only be used as static branding
    TYPE_CORDOVA = 3  # This branding contains an cordova.html or index.html
    TYPES = (TYPE_NORMAL, TYPE_APP, TYPE_CORDOVA)

    TYPE_MAPPING = {
        TYPE_NORMAL: 'branding.html',
        TYPE_APP: 'app.html',
        TYPE_CORDOVA: 'index.html',
    }

    COLOR_SCHEME_LIGHT = u"light"
    COLOR_SCHEME_DARK = u"dark"
    COLOR_SCHEMES = (COLOR_SCHEME_LIGHT, COLOR_SCHEME_DARK)

    ORIENTATION_PORTRAIT = u'portrait'
    ORIENTATION_LANDSCAPE = u'landscape'
    ORIENTATION_DYNAMIC = u'dynamic'
    ORIENTATIONS = (ORIENTATION_PORTRAIT, ORIENTATION_LANDSCAPE, ORIENTATION_DYNAMIC)

    DEFAULT_COLOR_SCHEME = COLOR_SCHEME_LIGHT
    DEFAULT_MENU_ITEM_COLORS = {COLOR_SCHEME_LIGHT: u"000000", COLOR_SCHEME_DARK: u"FFFFFF"}
    DEFAULT_ORIENTATION = ORIENTATION_PORTRAIT

    CONTENT_TYPE_HTML = u"text/html"
    CONTENT_TYPE_PDF = u"application/pdf"

    DISPLAY_TYPE_WEBVIEW = u'webview'
    DISPLAY_TYPE_NATIVE = u'native'
    DISPLAY_TYPES = (DISPLAY_TYPE_WEBVIEW, DISPLAY_TYPE_NATIVE)

    description = db.StringProperty()
    blob = db.BlobProperty(indexed=False)  # deprecated
    blob_key = db.StringProperty(indexed=False)
    user = db.UserProperty()
    timestamp = db.IntegerProperty()
    pokes = db.ListProperty(db.Key)
    type = db.IntegerProperty(indexed=True)
    menu_item_color = db.StringProperty(indexed=False)
    editor_cfg_key = db.StringProperty(indexed=False)
    content_type = db.StringProperty(indexed=False)
    orientation = db.StringProperty(indexed=False, default=DEFAULT_ORIENTATION)

    @property
    def hash(self):
        return self.key().name()

    @classmethod
    def create_key(cls, hash_):
        return db.Key.from_path(cls.kind(), hash_)

    def invalidateCache(self):
        from rogerthat.dal.messaging import get_branding
        logging.info("Branding '%s' removed from cache." % self.hash)
        invalidate_cache(get_branding, self.hash)

    @classmethod
    def list_by_type(cls, service_user, branding_type):
        return cls.all().filter('user', service_user).filter('type', branding_type)

    @classmethod
    def list_by_user(cls, service_user):
        return cls.all().filter('user', service_user)

    @classmethod
    def list_by_description(cls, service_user, description):
        # type: (users.User, unicode) -> list[Branding]
        return [b for b in cls.list_by_user(service_user).filter('description', description) if b.timestamp > 0]


class AppSettings(CachedModelMixIn, db.Model):
    wifi_only_downloads = db.BooleanProperty(indexed=False, default=False)
    background_fetch_timestamps = db.ListProperty(int, indexed=False)  # seconds since midnight, UTC
    oauth = OAuthSettingsProperty()
    birthday_message_enabled = db.BooleanProperty(default=False)
    birthday_message = db.TextProperty()
    tos_enabled = db.BooleanProperty(default=True)
    ios_firebase_project_id = db.StringProperty(indexed=False, default=None)

    @property
    def app_id(self):
        return self.key().name()

    @classmethod
    def create_key(cls, app_id):
        return db.Key.from_path(cls.kind(), app_id)

    def invalidateCache(self):
        from rogerthat.dal.app import get_app_settings
        logging.info("App '%s' removed from cache." % self.app_id)
        invalidate_cache(get_app_settings, self.app_id)

    @classmethod
    def list_with_birthday_message(cls):
        return cls.all().filter('birthday_message_enabled', True)


@deserializer
def ds_app_settings(stream):
    return ds_model(stream, AppSettings)


@serializer
def s_app_settings(stream, app_settings):
    s_model(stream, app_settings, AppSettings)


register(AppSettings, s_app_settings, ds_app_settings)


class QRTemplate(db.Model):
    DEFAULT_BLUE_PACIFIC_KEY_NAME = "Blue Pacific"
    DEFAULT_BROWN_BAG_KEY_NAME = "Brown Bag"
    DEFAULT_PINK_PANTER_KEY_NAME = "Pink Panter"

    DEFAULT_COLORS = {DEFAULT_BLUE_PACIFIC_KEY_NAME: u"1C66E6",
                      DEFAULT_BROWN_BAG_KEY_NAME: u"F57505",
                      DEFAULT_PINK_PANTER_KEY_NAME: u"ED3DED"}

    description = db.StringProperty(indexed=False)
    blob = db.BlobProperty(indexed=False)
    body_color = db.ListProperty(int, indexed=False)
    timestamp = db.IntegerProperty(indexed=False)
    deleted = db.BooleanProperty(default=False)

    @property
    def user(self):
        return users.User(self.parent_key().name())

    @staticmethod
    def create_key_name(app_id, description):
        return u'%s:%s' % (app_id, description)


class ChatMembers(polymodel.PolyModel):
    members = db.StringListProperty(indexed=True)

    @property
    def parent_message_key(self):
        return self.parent_key().name()

    def permission(self):
        raise NotImplementedError()

    def is_read_only(self):
        raise NotImplementedError()

    def members_size(self):
        return sum(len(m) for m in self.members)

    @classmethod
    def create_parent_key(cls, thread_key):
        from rogerthat.dal.messaging import get_message_key
        return get_message_key(thread_key, None)

    @classmethod
    def list_by_thread_and_chat_member(cls, parent_message_key, member_app_email):
        return cls.list_by_thread(parent_message_key).filter('members =', member_app_email)

    @classmethod
    def list_by_thread_and_chat_members(cls, parent_message_key, member_app_emails):
        return cls.list_by_thread(parent_message_key).filter('members IN', member_app_emails)

    @classmethod
    def get_last_by_thread(cls, parent_message_key):
        return cls.list_by_thread(parent_message_key).order('-__key__').get()

    @classmethod
    def list_by_chat_member(cls, member_app_email, keys_only=False):
        return cls.all(keys_only=keys_only).filter('members =', member_app_email)

    @classmethod
    def list_by_thread(cls, parent_message_key):
        return cls.all().ancestor(cls.create_parent_key(parent_message_key))

    @classmethod
    def count_members(cls, parent_message_key):
        c = 0
        for m in cls.all().ancestor(cls.create_parent_key(parent_message_key)):
            c += len(m.members)
        return c


class ChatAdminMembers(ChatMembers):

    def permission(self):
        from rogerthat.bizz.messaging import ChatMemberStatus
        return ChatMemberStatus.ADMIN

    def is_read_only(self):
        return False


class ChatWriterMembers(ChatMembers):

    def permission(self):
        from rogerthat.bizz.messaging import ChatMemberStatus
        return ChatMemberStatus.WRITER

    def is_read_only(self):
        return False


class ChatReaderMembers(ChatMembers):

    def permission(self):
        from rogerthat.bizz.messaging import ChatMemberStatus
        return ChatMemberStatus.READER

    def is_read_only(self):
        return True


class AbstractChatJob(db.Model):
    user = db.UserProperty(indexed=False, required=True)
    guid = db.StringProperty(indexed=True, required=True)

    @property
    def parent_message_key(self):
        return self.parent_key().name()

    @classmethod
    def create_parent_key(cls, parent_message_key):
        from rogerthat.dal.messaging import get_message_key
        return get_message_key(parent_message_key, None)

    @classmethod
    def list_by_guid(cls, parent_message_key, guid):
        return cls.all().ancestor(cls.create_parent_key(parent_message_key)).filter('guid', guid)


class DeleteMemberFromChatJob(AbstractChatJob):
    pass


class AddMemberToChatJob(AbstractChatJob):
    permission = db.StringProperty(indexed=False)


class UpdateChatMemberJob(AbstractChatJob):
    permission = db.StringProperty(indexed=False)


class ThreadAvatar(db.Model):
    avatar = db.BlobProperty()
    avatar_hash = db.StringProperty(indexed=False)

    @property
    def parent_message_key(self):
        return self.parent_key().name()

    @classmethod
    def create_key(cls, parent_message_key):
        return db.Key.from_path(cls.kind(), parent_message_key,
                                parent=db.Key.from_path(Message.kind(), parent_message_key))

    @classmethod
    def create(cls, parent_message_key, avatar):
        return cls(key=cls.create_key(parent_message_key),
                   avatar=db.Blob(avatar),
                   avatar_hash=sha256_hex(avatar))


class Message(db.Expando, polymodel.PolyModel):
    TYPE = 1
    TYPE_FORM_MESSAGE = 2

    FLAG_ALLOW_DISMISS = 1
    FLAG_ALLOW_CUSTOM_REPLY = 1 << 1
    FLAG_ALLOW_REPLY = 1 << 2
    FLAG_ALLOW_REPLY_ALL = 1 << 3
    FLAG_SHARED_MEMBERS = 1 << 4
    FLAG_LOCKED = 1 << 5
    FLAG_AUTO_LOCK = 1 << 6
    FLAG_SENT_BY_MFR = 1 << 7
    FLAG_SENT_BY_JS_MFR = 1 << 8
    FLAG_DYNAMIC_CHAT = 1 << 9
    FLAG_NOT_REMOVABLE = 1 << 10
    FLAG_ALLOW_CHAT_BUTTONS = 1 << 11
    FLAG_CHAT_STICKY = 1 << 12
    FLAG_ALLOW_CHAT_PICTURE = 1 << 13
    FLAG_ALLOW_CHAT_VIDEO = 1 << 14
    FLAG_ALLOW_CHAT_PRIORITY = 1 << 15
    FLAG_ALLOW_CHAT_STICKY = 1 << 16
    FLAG_ALLOW_CHAT_PAYMENTS = 1 << 17
    FLAGS = (FLAG_ALLOW_DISMISS, FLAG_ALLOW_CUSTOM_REPLY, FLAG_ALLOW_REPLY, FLAG_ALLOW_REPLY_ALL, FLAG_SHARED_MEMBERS,
             FLAG_LOCKED, FLAG_AUTO_LOCK, FLAG_SENT_BY_MFR, FLAG_SENT_BY_JS_MFR, FLAG_DYNAMIC_CHAT, FLAG_NOT_REMOVABLE,
             FLAG_ALLOW_CHAT_BUTTONS, FLAG_CHAT_STICKY, FLAG_ALLOW_CHAT_PICTURE, FLAG_ALLOW_CHAT_VIDEO,
             FLAG_ALLOW_CHAT_PRIORITY, FLAG_ALLOW_CHAT_STICKY, FLAG_ALLOW_CHAT_PAYMENTS)

    ALERT_FLAG_SILENT = 1
    ALERT_FLAG_VIBRATE = 2
    ALERT_FLAG_RING_5 = 4
    ALERT_FLAG_RING_15 = 8
    ALERT_FLAG_RING_30 = 16
    ALERT_FLAG_RING_60 = 32
    ALERT_FLAG_INTERVAL_5 = 64
    ALERT_FLAG_INTERVAL_15 = 128
    ALERT_FLAG_INTERVAL_30 = 256
    ALERT_FLAG_INTERVAL_60 = 512
    ALERT_FLAG_INTERVAL_300 = 1024
    ALERT_FLAG_INTERVAL_900 = 2048
    ALERT_FLAG_INTERVAL_3600 = 4096

    UI_FLAG_EXPECT_NEXT_WAIT_5 = 1
    UI_FLAG_AUTHORIZE_LOCATION = 2
    UI_FLAGS = (UI_FLAG_EXPECT_NEXT_WAIT_5, UI_FLAG_AUTHORIZE_LOCATION)

    ALERT_FLAGS = (ALERT_FLAG_SILENT, ALERT_FLAG_VIBRATE, ALERT_FLAG_RING_5, ALERT_FLAG_RING_15, ALERT_FLAG_RING_30,
                   ALERT_FLAG_RING_60, ALERT_FLAG_INTERVAL_5, ALERT_FLAG_INTERVAL_15, ALERT_FLAG_INTERVAL_30,
                   ALERT_FLAG_INTERVAL_60, ALERT_FLAG_INTERVAL_300, ALERT_FLAG_INTERVAL_900, ALERT_FLAG_INTERVAL_3600)
    RING_ALERT_FLAGS = (ALERT_FLAG_RING_5, ALERT_FLAG_RING_15, ALERT_FLAG_RING_30, ALERT_FLAG_RING_60)
    INTERVAL_ALERT_FLAGS = (ALERT_FLAG_INTERVAL_5, ALERT_FLAG_INTERVAL_15, ALERT_FLAG_INTERVAL_30,
                            ALERT_FLAG_INTERVAL_60, ALERT_FLAG_INTERVAL_300, ALERT_FLAG_INTERVAL_900,
                            ALERT_FLAG_INTERVAL_3600)

    MEMBER_INDEX_STATUS_NOT_RECEIVED = '1'
    MEMBER_INDEX_STATUS_SHOW_IN_INBOX = '2'
    MEMBER_INDEX_STATUS_NOT_DELETED = '3'
    MEMBER_INDEX_STATUSSES = (MEMBER_INDEX_STATUS_NOT_RECEIVED, MEMBER_INDEX_STATUS_SHOW_IN_INBOX,
                              MEMBER_INDEX_STATUS_NOT_DELETED)
    SERVICE_MESSAGE_DEFAULT_MEMBER_INDEX_STATUSSES = (MEMBER_INDEX_STATUS_NOT_RECEIVED,
                                                      MEMBER_INDEX_STATUS_SHOW_IN_INBOX,
                                                      MEMBER_INDEX_STATUS_NOT_DELETED)
    USER_MESSAGE_DEFAULT_MEMBER_INDEX_STATUSSES = (MEMBER_INDEX_STATUS_NOT_RECEIVED,
                                                   MEMBER_INDEX_STATUS_NOT_DELETED)

    PRIORITY_NORMAL = 1
    PRIORITY_HIGH = 2
    PRIORITY_URGENT = 3
    PRIORITY_URGENT_WITH_ALARM = 4

    PRIORITIES = (PRIORITY_NORMAL, PRIORITY_HIGH, PRIORITY_URGENT, PRIORITY_URGENT_WITH_ALARM)

    sender = db.UserProperty(indexed=False)
    members = db.ListProperty(users.User, indexed=False)
    flags = db.IntegerProperty(indexed=False)
    originalFlags = db.IntegerProperty(indexed=False)
    alert_flags = db.IntegerProperty(indexed=False)
    timeout = db.IntegerProperty(indexed=False)
    branding = db.StringProperty(indexed=False)
    message = db.TextProperty()
    buttons = ButtonsProperty()
    memberStatusses = MemberStatusesProperty()
    creationTimestamp = db.IntegerProperty()
    generation = db.IntegerProperty(indexed=False)
    childMessages = db.ListProperty(db.Key, indexed=False)
    tag = db.TextProperty()
    timestamp = db.IntegerProperty()
    dismiss_button_ui_flags = db.IntegerProperty(indexed=False)
    member_status_index = db.StringListProperty()
    sender_type = db.IntegerProperty()
    attachments = AttachmentsProperty()
    service_api_updates = db.UserProperty(indexed=False)
    thread_avatar_hash = db.StringProperty(indexed=False)  # -------|
    thread_background_color = db.StringProperty(indexed=False)  # --| Equal for all messages in the thread
    thread_text_color = db.StringProperty(indexed=False)  # --------|
    priority = db.IntegerProperty(indexed=False)
    default_priority = db.IntegerProperty(indexed=False)  # --------|
    default_sticky = db.BooleanProperty(indexed=False)  # ----------| Only on parent message
    step_id = db.StringProperty(indexed=False)  # used for FlowStatistics
    embedded_app = EmbeddedAppProperty()

    @property
    def sharedMembers(self):
        return self.flags & Message.FLAG_SHARED_MEMBERS == self.FLAG_SHARED_MEMBERS

    @property
    def mkey(self):
        return self.key().name()

    @property
    def pkey(self):
        return self.parent_key().name() if self.parent_key() else None

    @property
    def isRootMessage(self):
        return self.parent_key() == None

    @staticmethod
    def statusIndexValue(member, status):
        return "%s@%s" % (status, member.email())

    def hasStatusIndex(self, member, status):
        statusses = self.member_status_index or []
        for stat in statusses:
            if stat == Message.statusIndexValue(member, status):
                return True
        return False

    def addStatusIndex(self, member, status):
        statusses = set(self.member_status_index or [])
        for mem in llist(member):
            for stat in llist(status):
                azzert(stat in Message.MEMBER_INDEX_STATUSSES)
                statusses.add(Message.statusIndexValue(mem, stat))
                if stat == Message.MEMBER_INDEX_STATUS_NOT_RECEIVED:
                    statusses.add(Message.MEMBER_INDEX_STATUS_NOT_RECEIVED)
        self.member_status_index = list(statusses)

    def removeStatusIndex(self, member, status):
        statusses = self.member_status_index or []
        for mem in llist(member):
            for stat in llist(status):
                azzert(stat in Message.MEMBER_INDEX_STATUSSES)
                value = Message.statusIndexValue(mem, stat)
                if value in statusses:
                    statusses.remove(value)
                    logging.debug('Removing a member_status_index for message %s: %s', self.mkey, value)

                    # Check if this was the last member with MEMBER_INDEX_STATUS_NOT_RECEIVED
                    if stat == Message.MEMBER_INDEX_STATUS_NOT_RECEIVED:
                        if Message.MEMBER_INDEX_STATUS_NOT_RECEIVED in statusses:
                            for remaining_status in statusses:
                                if remaining_status.startswith("%s@" % Message.MEMBER_INDEX_STATUS_NOT_RECEIVED):
                                    break
                            else:
                                # We did not break ... this means this was the last member with
                                # MEMBER_INDEX_STATUS_NOT_RECEIVED
                                statusses.remove(Message.MEMBER_INDEX_STATUS_NOT_RECEIVED)
                                logging.debug('Removing a member_status_index for message %s: %s',
                                              self.mkey, Message.MEMBER_INDEX_STATUS_NOT_RECEIVED)

        self.member_status_index = statusses


class LocationMessage(ndb.Model):
    receiver = ndb.StringProperty(indexed=False)

    @property
    def message_key(self):
        return ndb.Key(Message.kind(), self.message_id)

    @property
    def message_id(self):
        return self.key.string_id().decode('utf-8')

    @classmethod
    def create_key(cls, app_user, message_id):
        from rogerthat.dal import parent_ndb_key
        return ndb.Key(cls, message_id, parent=parent_ndb_key(app_user))

    @classmethod
    def list_by_user(cls, app_user):
        from rogerthat.dal import parent_ndb_key
        return cls.query(ancestor=parent_ndb_key(app_user))


class FormMessage(Message):
    TYPE = Message.TYPE_FORM_MESSAGE
    form = FormProperty()


class SmartphoneChoice(db.Model):
    ANDROID = 1
    IPHONE = 2
    BLACKBERRY = 3
    WINDOWSPHONE = 4
    SYMBIAN = 5
    PALM = 6
    OTHER = 7

    choice = db.IntegerProperty(indexed=False)


class ServiceMenuDef(db.Model):
    label = db.StringProperty(indexed=False)
    tag = db.TextProperty()
    timestamp = db.IntegerProperty(indexed=False)
    icon = db.BlobProperty()  # None if itemColor is None
    iconHash = db.StringProperty(indexed=False)  # None if itemColor is None
    iconName = db.StringProperty(indexed=False)
    iconColor = db.StringProperty(indexed=False)
    screenBranding = db.StringProperty(indexed=False)
    staticFlowKey = db.StringProperty(indexed=True)
    link = db.TextProperty()
    isExternalLink = db.BooleanProperty(indexed=False, default=False)
    requestUserLink = db.BooleanProperty(indexed=False, default=False)
    requiresWifi = db.BooleanProperty(indexed=False, default=False)
    runInBackground = db.BooleanProperty(indexed=False, default=True)
    roles = db.ListProperty(int, indexed=True)
    action = db.IntegerProperty(default=0)  # Sort order of 'actions' displayed on client. 0 = not displayed as action
    fallThrough = db.BooleanProperty(indexed=False, default=False)
    form_id = db.IntegerProperty()
    form_version = db.IntegerProperty(indexed=False)
    embeddedApp = db.StringProperty(indexed=False)

    @staticmethod
    def createKey(coords, service_user):
        from rogerthat.dal import parent_key
        return db.Key.from_path(ServiceMenuDef.kind(), "x".join((str(x) for x in coords)),
                                parent=parent_key(service_user))

    @property
    def service(self):
        return users.User(self.parent_key().name())

    @property
    def coords(self):
        return [int(c) for c in self.key().name().split('x')]

    @property
    def hashed_tag(self):
        return ServiceMenuDef.hash_tag(self.tag)

    @staticmethod
    def hash_tag(tag):
        return None if tag is None else unicode(hashlib.sha256(tag.encode('utf-8')).hexdigest())

    @classmethod
    def list_with_action(cls, service_user):
        return cls.list_by_service(service_user).filter('action >', 0).order('action')

    @classmethod
    def list_by_service(cls, service_user):
        from rogerthat.dal import parent_key
        return cls.all().ancestor(parent_key(service_user))

    @classmethod
    def list_by_form(cls, service_user, form_id):
        from rogerthat.dal import parent_key
        return cls.all().ancestor(parent_key(service_user)).filter(cls.form_id.name, form_id)


class NdbServiceMenuDef(NdbModel):
    label = ndb.StringProperty(indexed=False)
    tag = ndb.TextProperty()
    timestamp = ndb.IntegerProperty(indexed=False)
    icon = ndb.BlobProperty()  # None if itemColor is None
    iconHash = ndb.StringProperty(indexed=False)  # None if itemColor is None
    iconName = ndb.StringProperty(indexed=False)
    iconColor = ndb.StringProperty(indexed=False)
    screenBranding = ndb.StringProperty(indexed=False)
    staticFlowKey = ndb.StringProperty(indexed=True)
    link = ndb.TextProperty()
    isExternalLink = ndb.BooleanProperty(indexed=False, default=False)
    requiresWifi = ndb.BooleanProperty(indexed=False, default=False)
    runInBackground = ndb.BooleanProperty(indexed=False, default=True)
    roles = ndb.IntegerProperty(indexed=True, repeated=True)
    action = ndb.IntegerProperty(default=0)  # Sort order of 'actions' displayed on client. 0 = not displayed as action
    fallThrough = ndb.BooleanProperty(indexed=False, default=False)

    @classmethod
    def _get_kind(cls):
        return ServiceMenuDef.kind()

    @classmethod
    def list_by_service(cls, svc_user):
        from rogerthat.dal import parent_ndb_key
        return cls.query(ancestor=parent_ndb_key(svc_user))


class ServiceInteractionDef(db.Model):
    TAG_INVITE = "__invite__"

    description = db.TextProperty()
    tag = db.TextProperty()
    timestamp = db.IntegerProperty()
    qrTemplate = db.ReferenceProperty(QRTemplate, indexed=False)
    shortUrl = db.ReferenceProperty(ShortURL, indexed=False)
    deleted = db.BooleanProperty(default=False)
    totalScanCount = db.IntegerProperty(indexed=False, default=0)
    scannedFromRogerthatCount = db.IntegerProperty(indexed=False, default=0)
    scannedFromOutsideRogerthatOnSupportedPlatformCount = db.IntegerProperty(indexed=False, default=0)
    scannedFromOutsideRogerthatOnUnsupportedPlatformCount = db.IntegerProperty(indexed=False, default=0)
    service_identity = db.StringProperty()  # Needed to find all QR codes for a service identity
    multilanguage = db.BooleanProperty(default=False)
    staticFlowKey = db.StringProperty(indexed=True)
    branding = db.StringProperty(indexed=False)

    @property
    def user(self):
        return users.User(self.parent_key().name())

    @property
    def service_identity_user(self):
        from rogerthat.utils.service import create_service_identity_user
        return create_service_identity_user(self.user, self.service_identity or ServiceIdentity.DEFAULT)

    @property
    def SIDKey(self):
        return str(self.key())


class PokeTagMap(db.Model):
    tag = db.TextProperty()

    @property
    def service(self):
        return users.User(self.parent_key().name())

    @property
    def hash(self):
        return self.key().name()

    @classmethod
    def create_key(cls, hashed_poke, service_user):
        from rogerthat.dal import parent_key
        return db.Key.from_path(cls.kind(), hashed_poke, parent=parent_key(service_user))


class ServiceMenuDefTagMap(PokeTagMap):
    timestamp = db.IntegerProperty()


class UserInteraction(db.Model):
    INTERACTION_WELCOME = 1
    INTERACTION_DEMO = 2  # deprecated
    INTERACTION_YOUR_SERVICE_HERE = 4  # deprecated
    INTERACTIONS = (INTERACTION_WELCOME, INTERACTION_DEMO, INTERACTION_YOUR_SERVICE_HERE)

    interactions = db.IntegerProperty(indexed=False, default=0)
    services = db.StringListProperty(indexed=False, default=[])

    @property
    def user(self):
        return users.User(self.key().name())


class CustomMessageFlowDesign(object):
    # Used to start a message flow by XML
    xml = None


class MessageFlowDesign(db.Model):
    STATUS_VALID = 0
    STATUS_BROKEN = 1
    STATUS_SUBFLOW_BROKEN = 2
    STATUSSES = (STATUS_VALID, STATUS_BROKEN, STATUS_SUBFLOW_BROKEN)

    name = db.StringProperty()
    language = db.StringProperty(indexed=False)  # DO NOT USE!!! This is a property of the MFD javascript toolkit
    definition = db.TextProperty()
    status = db.IntegerProperty(default=STATUS_VALID)
    validation_error = db.TextProperty()
    design_timestamp = db.IntegerProperty(indexed=False)
    deleted = db.BooleanProperty(indexed=True)
    sub_flows = db.ListProperty(db.Key)
    broken_sub_flows = db.ListProperty(db.Key)
    xml = db.TextProperty()
    model_version = db.IntegerProperty(indexed=False)
    # version 2: added "results flush" action
    multilanguage = db.BooleanProperty(indexed=True, default=False)
    i18n_warning = db.TextProperty()
    js_flow_definitions = JsFlowDefinitionsProperty()
    js_flow_definitions_json = db.TextProperty()
    
    _tmp_js_flow_definitions = None

    @property
    def user(self):
        return users.User(self.parent_key().name())

    @classmethod
    def list_by_service_user(cls, service_user):
        from rogerthat.dal import parent_key
        return cls.all().ancestor(parent_key(service_user)).filter('status', cls.STATUS_VALID)
    
    def get_js_flow_definitions(self):
        if self._tmp_js_flow_definitions is None:
            data = json.loads(self.js_flow_definitions_json) if self.js_flow_definitions_json else {}
            result = {}
            if data:
                for lang, value in data.iteritems():
                    result[lang] = JsFlowDefinitionTO.from_dict(value)
            elif self.js_flow_definitions:
                for jfd in self.js_flow_definitions:
                    result[jfd.language] = jfd
            self._tmp_js_flow_definitions = result
        return self._tmp_js_flow_definitions

    def save_js_flow_definitions(self, data):
        result = {}
        for lang, value in data.iteritems():
            result[lang] = value.to_dict()
        self.js_flow_definitions_json = json.dumps(result)
        self._tmp_js_flow_definitions = data
        
    def get_js_flow_definition_by_language(self, lang):
        data = self.get_js_flow_definitions()
        for lang in data:
            return data[lang]
        return None
    
    def get_js_flow_definition_by_hash(self, static_flow_hash):
        data = self.get_js_flow_definitions()
        for _, value in data.iteritems():
            if value.hash_ == static_flow_hash:
                return value
        return None


class MessageFlowDesignBackup(db.Model):
    definition = db.TextProperty()
    design_timestamp = db.IntegerProperty(indexed=False)


class MessageFlowRunRecord(db.Model):
    _POST_RESULT_CALLBACK = 1

    flags = db.IntegerProperty(indexed=False, default=0)
    tag = db.TextProperty()
    service_identity = db.StringProperty()  # e.g. info@example.com/+default+ or info@example.com/otheridentity
    creationtime = db.IntegerProperty()
    flow_params = db.TextProperty()

    @property
    def messageFlowRunId(self):
        return self.key().name().split('/')[-1]

    @staticmethod
    def createKeyName(service_user, guid):
        return "%s/%s" % (service_user.email(), guid)

    def _set_post_result_callback(self, value):
        if value:
            self.flags |= MessageFlowRunRecord._POST_RESULT_CALLBACK
        else:
            self.flags &= ~MessageFlowRunRecord._POST_RESULT_CALLBACK

    post_result_callback = property(fget=lambda
                                    self: self.flags & MessageFlowRunRecord._POST_RESULT_CALLBACK == MessageFlowRunRecord._POST_RESULT_CALLBACK,
                                    fset=_set_post_result_callback)


class UserInvitationSecret(db.Model):
    STATUS_CREATED = 1
    STATUS_SENT = 2
    STATUS_REDIRECTED = 3
    STATUS_USED = 4
    STATUSSES = (STATUS_CREATED, STATUS_SENT, STATUS_REDIRECTED, STATUS_USED)

    status = db.IntegerProperty(indexed=False)
    creation_timestamp = db.IntegerProperty(indexed=False)
    sent_timestamp = db.IntegerProperty(indexed=False, default=0)
    redirected_timestamp = db.IntegerProperty(indexed=False, default=0)
    phone_number = db.StringProperty(indexed=False)
    email = db.UserProperty(indexed=False)
    used_timestamp = db.IntegerProperty(indexed=False, default=0)
    used_for_user = db.UserProperty(indexed=False)
    service_tag = db.TextProperty()
    origin = db.StringProperty(indexed=False)

    @property
    def secret(self):
        return unicode(base65.encode_int(self.key().id()))

    @property
    def user(self):
        return users.User(self.parent_key().name())


class LocationRequest(db.Model):
    timestamp = db.IntegerProperty(indexed=False)

    @property
    def friend(self):
        return users.User(self.parent_key().name())

    @property
    def user(self):
        return users.User(self.key().name())


class StartDebuggingRequest(db.Model):
    timestamp = db.IntegerProperty(indexed=False)

    @property
    def user(self):
        return users.User(self.parent_key().name())

    @property
    def target_id(self):
        return self.key().name()

    @staticmethod
    def create_key(app_user, target_id):  # target_id = mobile_id (branding debug) or xmpp_target_jid (admin debug)
        from rogerthat.dal import parent_key
        return db.Key.from_path(StartDebuggingRequest.kind(), target_id, parent=parent_key(app_user))


class InstallationStatus(Enum):
    STARTED = 'started'
    IN_PROGRESS = 'in_progress'
    FINISHED = 'finished'


class Installation(db.Model):
    version = db.StringProperty(indexed=False)
    platform = db.IntegerProperty()
    timestamp = db.IntegerProperty()
    app_id = db.StringProperty()
    status = db.StringProperty(choices=InstallationStatus.all())
    service_identity_user = db.UserProperty(indexed=False)
    service_callback_result = db.StringProperty(indexed=False)
    auto_connected_services = db.StringListProperty(indexed=False)
    roles = db.TextProperty()
    qr_url = db.StringProperty(indexed=False)
    oauth_state = db.StringProperty(indexed=False)
    mobile = db.ReferenceProperty(Mobile)
    profile = db.ReferenceProperty(UserProfile)

    @property
    def id(self):
        return self.key().name()

    @property
    def platform_string(self):
        return self.platform and Mobile.typeAsString(self.platform)

    @classmethod
    def list_by_app(cls, app_id):
        return cls.all().filter('app_id', app_id).order('-timestamp')


class Registration(db.Model):
    version = db.IntegerProperty(indexed=False)
    timestamp = db.IntegerProperty()
    device_id = db.StringProperty(indexed=False)
    pin = db.IntegerProperty(indexed=False)
    mobile = db.ReferenceProperty(Mobile)
    timesleft = db.IntegerProperty(indexed=False)
    installation = db.ReferenceProperty(Installation)
    request_id = db.StringProperty(indexed=False)
    language = db.StringProperty(indexed=False)
    device_names = db.StringListProperty(indexed=False)

    @property
    def identifier(self):
        return self.key().name()

    @property
    def user(self):
        return users.User(self.parent_key().name())

    @classmethod
    def list_by_mobile(cls, mobile):
        return cls.all().filter('mobile', mobile)


class InstallationLog(db.Model):
    timestamp = db.IntegerProperty()
    description = db.StringProperty(indexed=False, multiline=True)
    pin = db.IntegerProperty()

    @property
    def time(self):
        return time.strftime("%a %d %b %Y\n%H:%M:%S GMT", time.localtime(self.timestamp))

    @classmethod
    def list_by_installation(cls, installation):
        return cls.all().ancestor(installation).order('timestamp')


class ActivationLog(db.Model):
    timestamp = db.IntegerProperty()
    email = db.StringProperty(indexed=True)
    mobile = db.ReferenceProperty(Mobile)
    description = db.TextProperty()

    @property
    def time(self):
        return time.strftime("%a %d %b %Y\n%H:%M:%S GMT", time.localtime(self.timestamp))

    @property
    def platform_string(self):
        try:
            return Mobile.typeAsString(self.mobile.type) if self.mobile else ""
        except ValueError:
            return "ValueError %s" % self.mobile.type

    @property
    def version_string(self):
        return self.mobile.osVersion if self.mobile else ""

    @property
    def mobile_string(self):
        return "%s - %s" % (self.platform_string, self.version_string) if self.mobile else ''


class LogAnalysis(db.Model):
    analyzed_until = db.IntegerProperty(indexed=False)


class TransferResult(db.Model):
    STATUS_PENDING = 1
    STATUS_VERIFIED = 2
    STATUS_FAILED = 3
    service_identity_user = db.UserProperty()
    total_chunks = db.IntegerProperty(indexed=False)
    photo_hash = db.StringProperty(indexed=False)
    content_type = db.StringProperty()

    status = db.IntegerProperty(indexed=False)
    timestamp = db.IntegerProperty()

    @staticmethod
    def create_key(parent_message_key, message_key):
        azzert(message_key)
        key = urllib.urlencode(
            (('pmk', parent_message_key), ('mk', message_key)) if parent_message_key else (('mk', message_key),))
        return db.Key.from_path(TransferResult.kind(), key)

    def _get_value_from_key(self, value):
        key = urlparse.parse_qs(self.key().name())
        val = key.get(value)
        if val:
            return val[0]
        return None

    @staticmethod
    def get_message_key_from_key(transfer_result_key):
        key = urlparse.parse_qs(transfer_result_key.name())
        val = key.get('mk')
        return val[0] if val else None

    @staticmethod
    def get_parent_message_key_from_key(transfer_result_key):
        key = urlparse.parse_qs(transfer_result_key.name())
        val = key.get('pmk')
        return val[0] if val else None

    @property
    def parent_message_key(self):
        return self._get_value_from_key('pmk')

    @property
    def message_key(self):
        return self._get_value_from_key('mk')


class TransferChunk(db.Model):
    content = db.BlobProperty(indexed=False)
    number = db.IntegerProperty(indexed=True)
    timestamp = db.IntegerProperty(indexed=False)

    @property
    def transfer_result_key(self):
        return self.parent_key()


class FlowResultMailFollowUp(db.Model):
    member = db.UserProperty(indexed=False)
    parent_message_key = db.StringProperty(indexed=False)
    service_user = db.UserProperty(indexed=False)
    service_identity = db.StringProperty(indexed=False)
    subject = db.StringProperty(indexed=False)
    addresses = db.StringListProperty(indexed=False)


class CurrentlyForwardingLogs(db.Model):
    TYPE_XMPP = 1
    TYPE_GAE_CHANNEL_API = 2

    xmpp_target = db.StringProperty(indexed=True)
    xmpp_target_password = db.StringProperty(indexed=True)
    type = db.IntegerProperty(indexed=False, default=TYPE_XMPP)

    @classmethod
    def create_parent_key(cls):
        return db.Key.from_path(cls.kind(), 'ancestor')

    @classmethod
    def create_key(cls, app_user):
        return db.Key.from_path(cls.kind(), app_user.email(), parent=cls.create_parent_key())

    @property
    def email(self):
        return self.key().name()

    @property
    def app_user(self):
        return users.User(self.email)

    @property
    def human_user(self):
        from rogerthat.utils.app import get_app_user_tuple_by_email
        return get_app_user_tuple_by_email(self.email)[0]

    @property
    def app_id(self):
        from rogerthat.utils.app import get_app_user_tuple_by_email
        return get_app_user_tuple_by_email(self.email)[1]

    @property
    def app_name(self):
        from rogerthat.dal.app import get_app_name_by_id
        return get_app_name_by_id(self.app_id)


class ServiceIdentityStatistic(db.Expando):
    number_of_users = db.IntegerProperty()
    gained_last_week = db.IntegerProperty(default=0)
    lost_last_week = db.IntegerProperty(default=0)
    users_gained = db.ListProperty(int, indexed=False)
    users_lost = db.ListProperty(int, indexed=False)
    last_entry_day = db.IntegerProperty(default=0)  # 20140128
    last_ten_users_gained = db.StringListProperty(indexed=False)
    last_ten_users_lost = db.StringListProperty(indexed=False)
    recommends_via_rogerthat = db.ListProperty(int, indexed=False)
    recommends_via_email = db.ListProperty(int, indexed=False)
    mip_labels = db.StringListProperty(indexed=False)

    @staticmethod
    def create_key(service_identity_user):
        from rogerthat.dal import parent_key
        from rogerthat.utils.service import add_slash_default
        from rogerthat.utils.service import get_service_user_from_service_identity_user
        service_identity_user = add_slash_default(service_identity_user)
        service_user = get_service_user_from_service_identity_user(service_identity_user)
        return db.Key.from_path(ServiceIdentityStatistic.kind(), service_identity_user.email(),
                                parent=parent_key(service_user))

    @property
    def service_identity_user(self):
        return users.User(self.key().name())

    @property
    def service_user(self):
        return users.User(self.parent_key().name())


class CompressedIntegerListExpando(db.Expando):
    _attribute_prefix = None

    def __getattr__(self, name):
        attr = super(CompressedIntegerListExpando, self).__getattr__(name)
        if name == '_attribute_prefix':
            return attr

        attribute_prefix = self._attribute_prefix
        if not attribute_prefix:
            raise ValueError()

        if not name.startswith(attribute_prefix):
            return attr

        return CompressedIntegerList(attr, self, name)

    def __setattr__(self, name, value):
        attribute_prefix = self._attribute_prefix
        if not attribute_prefix:
            raise ValueError()

        if name.startswith(attribute_prefix):
            if isinstance(value, CompressedIntegerList):
                value = db.Blob(str(value))
            elif isinstance(value, list):
                value = db.Blob(str(CompressedIntegerList(value, self, name)))
            elif isinstance(value, basestring):
                pass
            else:
                raise ValueError('Unexpected value for property %s: %s' % (name, type(value)))

        super(CompressedIntegerListExpando, self).__setattr__(name, value)


class FlowStatistics(CompressedIntegerListExpando):
    '''
    Has dynamic properties in the following format:
    step(_<step_id>_<status sent/received/read/acked>_<btn_id if status==acked>)+
    - The value of these properties is a list with a counter per day.
    -- The first item of this list is the oldest counter.
    -- The last item of this list is the counter for <last_entry_day>.
    -- The counters list contains maximum 1000 entries.

    Example 1: self.labels = ['msgA']; self.step_0_read = [5, 0, 0, 10]
    - msgA is the start message of the flow
    - msgA is read 10 times at <last_entry_day> and 5 times 3 days before <last_entry_day>

    Example 2: self.labels = ['msgA', 'btn1', 'msgB']; self.step_0_1_2_sent = [0, 0, 0, 1]
    - msgB is reached 1 time via btn1 of msgA at <last_entry_day>
    '''
    _attribute_prefix = 'step_'
    labels = db.StringListProperty()  # list with step IDs and button IDs
    last_entry_day = db.IntegerProperty(default=0)  # 20140128

    STATUS_SENT = 'sent'
    STATUS_RECEIVED = 'received'
    STATUS_READ = 'read'
    STATUS_ACKED = 'acked'
    STATUSES = (STATUS_SENT, STATUS_RECEIVED, STATUS_READ, STATUS_ACKED)

    StepMetadata = namedtuple('Step', 'breadcrumbs step_id status btn_id')

    def _get_label_index_str(self, label):
        if not label:
            return ''
        try:
            return str(self.labels.index(label))
        except ValueError:
            self.labels.append(label)
            return str(len(self.labels) - 1)

    def _get_status_list_name(self, breadcrumbs, step_id, status, btn_id=None):
        def parts():
            yield 'step'
            for breadcrumb in breadcrumbs:
                yield self._get_label_index_str(breadcrumb)
            yield self._get_label_index_str(step_id)
            yield status
            if status == self.STATUS_ACKED:
                yield self._get_label_index_str(btn_id)

        return '_'.join(parts())

    def get_status_list_tuple(self, breadcrumbs, step_id, status, btn_id=None):
        prop_name = self._get_status_list_name(breadcrumbs, step_id, status, btn_id)
        status_list = getattr(self, prop_name, None)
        if status_list is None:
            status_list = CompressedIntegerList([0], self, prop_name)
            setattr(self, prop_name, status_list)
        return status_list, prop_name

    def get_status_list(self, breadcrumbs, step_id, status, btn_id=None):
        return self.get_status_list_tuple(breadcrumbs, step_id, status, btn_id)[0]

    def add(self, breadcrumbs, step_id, status, btn_id=None):
        status_list, status_list_name = self.get_status_list_tuple(breadcrumbs, step_id, status, btn_id)
        status_list[-1] += 1
        return status_list, status_list_name

    def _get_label(self, label_index_str):
        if label_index_str:
            return self.labels[int(label_index_str)]
        return None

    def parse_step_property(self, prop_name):
        splitted = prop_name.split('_')
        azzert(splitted.pop(0) == 'step')
        if splitted[-2] == self.STATUS_ACKED:
            btn_idx = splitted.pop(-1)
        else:
            btn_idx = None

        status = splitted.pop(-1)
        step_idx = splitted.pop(-1)

        return self.StepMetadata(breadcrumbs=map(self._get_label, splitted),
                                 step_id=self._get_label(step_idx),
                                 status=status,
                                 btn_id=self._get_label(btn_idx))

    def get_step_properties(self):
        return [p for p in self.dynamic_properties() if p.startswith('step_')]

    def _get_labels(self, matcher_func, days=1):
        lbls = dict()
        for prop_name in self.dynamic_properties():
            if matcher_func(prop_name):
                status_list = getattr(self, prop_name)
                for days_ago in xrange(days):
                    if status_list[days_ago] > 0:
                        splitted = prop_name.split('_')
                        idx_str = splitted[-2]
                        if idx_str == self.STATUS_ACKED:
                            idx_str = splitted[-1]
                        lbl = self.labels[int(idx_str)] if idx_str else None
                        lbls[lbl] = days_ago
                        break
        return sorted(lbls, key=lbls.get)  # sorted, most recent occurrence first

    def get_button_ids(self, breadcrumbs, step_id, days=1):
        prefix = self._get_status_list_name(breadcrumbs, step_id, self.STATUS_ACKED, None)

        def has_prefix(prop_name):
            return prop_name.startswith(prefix)

        return self._get_labels(has_prefix, days)

    def get_next_step_ids(self, breadcrumbs, days=1):
        prefix = 'step_%s' % '_'.join(map(self._get_label_index_str, breadcrumbs))

        def is_next_step(prop_name):
            return prop_name.endswith('_sent') \
                and prop_name.startswith(prefix) \
                and prop_name.count('_') == len(breadcrumbs) + 2

        return self._get_labels(is_next_step, days)

    def set_today(self, today=None):
        if today is None:
            today = datetime.datetime.utcnow().date()
        if self.last_entry_day == 0:  # new model
            delta = 0
        else:
            delta = (today - self.last_entry_datetime_date).days

        if delta > 0:
            for prop_name in self.get_step_properties():
                status_list = getattr(self, prop_name)
                status_list.ljust(delta, 0, 1000)

        self.last_entry_day = int("%d%02d%02d" % (today.year, today.month, today.day))

    @property
    def last_entry_datetime_date(self):
        s = str(self.last_entry_day)
        return datetime.date(int(s[0:4]), int(s[4:6]), int(s[6:8]))

    @property
    def tag(self):
        return self.key().name()

    @property
    def service_identity(self):
        return self.parent_key().name()

    @property
    def service_user(self):
        return users.User(self.parent_key().parent().name())

    @property
    def service_identity_user(self):
        from rogerthat.utils.service import create_service_identity_user
        return create_service_identity_user(self.service_user, self.service_identity)

    @classmethod
    def create_parent_key(cls, service_identity_user):
        from rogerthat.dal import parent_key
        from rogerthat.utils.service import get_service_identity_tuple
        service_user, service_identity = get_service_identity_tuple(service_identity_user)
        service_parent_key = parent_key(service_user)
        return db.Key.from_path(service_parent_key.kind(), service_identity, parent=service_parent_key)

    @classmethod
    def create_key(cls, tag, service_identity_user):
        return db.Key.from_path(cls.kind(), tag, parent=cls.create_parent_key(service_identity_user))

    @classmethod
    def list_by_service_identity_user(cls, service_identity_user):
        return cls.all().ancestor(cls.create_parent_key(service_identity_user))

    @classmethod
    def list_by_service_user(cls, service_user):
        from rogerthat.dal import parent_key
        return cls.all().ancestor(parent_key(service_user))


class JSEmbedding(db.Model):
    creation_time = db.IntegerProperty(indexed=False)
    content = db.BlobProperty(indexed=False)
    hash = db.StringProperty(indexed=False)  # Zip Hash
    hash_files = db.StringProperty(indexed=False)

    @property
    def name(self):
        return self.key().name()


class Group(db.Model):
    name = db.StringProperty(indexed=False)
    avatar = db.BlobProperty(indexed=False)
    avatar_hash = db.StringProperty(indexed=True)
    members = db.ListProperty(unicode, indexed=True)

    @property
    def guid(self):
        return self.key().name()

    @property
    def user(self):
        return users.User(self.parent_key().name())

    @staticmethod
    def create_key(app_user, guid):
        from rogerthat.dal import parent_key
        return db.Key.from_path(Group.kind(), guid, parent=parent_key(app_user))


class ServiceLocationTracker(db.Model):
    creation_time = db.IntegerProperty(indexed=True)
    until = db.IntegerProperty(indexed=True)
    enabled = db.BooleanProperty(indexed=True)
    service_identity_user = db.UserProperty(indexed=True)
    notified = db.BooleanProperty(indexed=False, default=False)

    @property
    def user(self):
        return users.User(self.parent_key().name())

    @classmethod
    def create_key(cls, app_user, key):
        from rogerthat.dal import parent_key
        return db.Key.from_path(cls.kind(), key, parent=parent_key(app_user))

    def encrypted_key(self):
        from rogerthat.utils.service import get_service_user_from_service_identity_user
        service_user = get_service_user_from_service_identity_user(self.service_identity_user)
        return encrypt(service_user, str(self.key()))


class UserDataExport(db.Model):
    creation_time = db.IntegerProperty()
    data_export_email = db.StringProperty()

    @property
    def user(self):
        return users.User(self.parent_key().name())

    @classmethod
    def create_key(cls, app_user, date):
        from rogerthat.dal import parent_key
        return db.Key.from_path(cls.kind(), date, parent=parent_key(app_user))


class Report(ndb.Model):
    timestamp = ndb.DateTimeProperty(auto_now_add=True)
    reported_by = ndb.UserProperty(indexed=False)
    type = ndb.StringProperty(indexed=True)
    reason = ndb.StringProperty(indexed=False)
    object = ndb.JsonProperty(compressed=False)


class ZipCode(NdbModel):
    zip_code = ndb.StringProperty()
    name = ndb.StringProperty()


class ProfileZipCodes(NdbModel):
    zip_codes = ndb.LocalStructuredProperty(ZipCode, repeated=True)

    @property
    def country_code(self):
        return self.key.id().encode('utf-8')

    @classmethod
    def create_key(cls, country_code):
        return ndb.Key(cls, country_code)


class ProfileStreets(NdbModel):
    streets = ndb.StringProperty(indexed=False, repeated=True)

    @property
    def zip_code(self):
        return self.key.id().encode('utf-8')

    @property
    def country_code(self):
        return self.key.parent().id().encode('utf-8')

    @classmethod
    def create_key(cls, country_code, zip_code):
        return ndb.Key(cls, zip_code, parent=ndb.Key(cls, country_code))


class UserContextScope(Enum):
    NAME = 'user.name'
    EMAIL = 'user.email' # deprecated
    EMAIL_ADDRESSES = 'user.email_addresses' # todo implement
    ADDRESSES = 'user.addresses'
    PHONE_NUMBERS = 'user.phone_numbers'


class UserContextLink(NdbModel):
    created = ndb.DateTimeProperty(auto_now_add=True)
    service_user = ndb.UserProperty()
    link = ndb.StringProperty()
    scopes = ndb.StringProperty(repeated=True)

    @property
    def uid(self):
        return self.key.id().decode('utf8')

    @staticmethod
    def create_uid(items):
        digester = hashlib.sha256()
        for i in items:
            v = i.encode('utf8') if isinstance(i, unicode) else i
            digester.update(v.upper())
        return digester.hexdigest().upper()

    @classmethod
    def create_key(cls, uid):
        return ndb.Key(cls, uid)


class UserContext(NdbModel):
    created = ndb.DateTimeProperty(auto_now_add=True)
    app_user = ndb.UserProperty(indexed=False)
    link_uid = ndb.StringProperty()
    scopes = ndb.StringProperty(repeated=True, indexed=False)

    @property
    def uid(self):
        return self.key.id().decode('utf8')

    @classmethod
    def create_key(cls, uid):
        return ndb.Key(cls, uid)

    @classmethod
    def list_before_date(cls, date):
        return cls.query(cls.created < date)
