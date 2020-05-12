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

import json
import logging
from time import mktime

from google.appengine.api import users
from google.appengine.ext import db, ndb

from mcfw.cache import CachedModelMixIn, invalidate_model_cache
from mcfw.serialization import deserializer, register, s_model, get_list_serializer, get_list_deserializer, \
    model_deserializer, List, s_any, ds_any
from rogerthat.models import NdbModel
from rogerthat.translations import localize
from rogerthat.utils import now, get_python_stack_trace


class RpcException(Exception):
    # Used to return translated errors to the user (in the app) when they did something wrong
    def __init__(self, translation_key, app_user, **kwargs):
        from rogerthat.dal.profile import get_user_profile
        language = get_user_profile(app_user).language
        message = localize(language, translation_key, **kwargs)
        super(RpcException, self).__init__(message)


class Mobile(db.Model):
    TYPE_LEGACY_ANDROID = 1
    TYPE_LEGACY_IPHONE = 2
    TYPE_BLACKBERRY = 3
    TYPE_ANDROID_HTTP = 4
    TYPE_LEGACY_IPHONE_XMPP = 5
    TYPE_WINDOWS_PHONE = 6
    TYPE_IPHONE_HTTP_APNS_KICK = 7
    TYPE_IPHONE_HTTP_XMPP_KICK = 8
    TYPE_ANDROID_FIREBASE_HTTP = 9
    TYPES = (TYPE_LEGACY_ANDROID, TYPE_LEGACY_IPHONE, TYPE_BLACKBERRY, TYPE_ANDROID_HTTP, TYPE_LEGACY_IPHONE_XMPP,
             TYPE_WINDOWS_PHONE, TYPE_IPHONE_HTTP_APNS_KICK, TYPE_IPHONE_HTTP_XMPP_KICK, TYPE_ANDROID_FIREBASE_HTTP)
    IOS_TYPES = (TYPE_IPHONE_HTTP_APNS_KICK, TYPE_IPHONE_HTTP_XMPP_KICK, TYPE_LEGACY_IPHONE_XMPP, TYPE_LEGACY_IPHONE)
    ANDROID_TYPES = (TYPE_ANDROID_FIREBASE_HTTP, TYPE_ANDROID_HTTP, TYPE_LEGACY_ANDROID)

    @staticmethod
    def typeAsString(type_):
        if type_ not in Mobile.TYPES:
            raise ValueError()
        if type_ in Mobile.ANDROID_TYPES:
            return u"android"
        elif type_ in Mobile.IOS_TYPES:
            return u"ios"
        elif type_ == Mobile.TYPE_BLACKBERRY:
            return u"blackberry"
        elif type_ == Mobile.TYPE_WINDOWS_PHONE:
            return u"windows"

    # Lifecycle of a registered mobile.
    # Warning: if statusses are added, check the implementation of Mobile.is_phone_unregistered
    STATUS_NEW = 1
    STATUS_ACCOUNT_CREATED = 2
    STATUS_REGISTERED = 4
    STATUS_DELETE_REQUESTED = 8
    STATUS_UNREGISTERED = 16
    STATUS_ACCOUNT_DELETED = 32
    STATUSSES = (STATUS_NEW, STATUS_ACCOUNT_CREATED, STATUS_REGISTERED, \
                 STATUS_DELETE_REQUESTED, STATUS_UNREGISTERED, STATUS_ACCOUNT_DELETED)

    user = db.UserProperty()
    id = db.StringProperty()  # @ReservedAssignment
    account = db.StringProperty()
    accountPassword = db.StringProperty()
    type = db.IntegerProperty()  # @ReservedAssignment
    description = db.StringProperty()
    hardwareModel = db.StringProperty()
    phoneNumber = db.StringProperty()
    phoneNumberVerificationCode = db.StringProperty(indexed=False)
    phoneNumberVerified = db.BooleanProperty(default=False)
    timestamp = db.DateTimeProperty(auto_now=True)
    registrationTimestamp = db.IntegerProperty()
    status = db.IntegerProperty()
    operatingVersion = db.IntegerProperty()
    iOSPushId = db.StringProperty()
    simCountry = db.StringProperty(indexed=False)
    simCountryCode = db.StringProperty(indexed=False)
    simCarrierName = db.StringProperty(indexed=False)
    simCarrierCode = db.StringProperty(indexed=False)
    netCountry = db.StringProperty(indexed=False)
    netCountryCode = db.StringProperty(indexed=False)
    netCarrierName = db.StringProperty(multiline=True, indexed=False)
    netCarrierCode = db.StringProperty(indexed=False)
    osVersion = db.StringProperty(indexed=False)
    localeLanguage = db.StringProperty(indexed=False)
    localeCountry = db.StringProperty(indexed=False)
    timezone = db.StringProperty(indexed=False)
    timezoneDeltaGMT = db.IntegerProperty(indexed=False)
    ysaaa = db.BooleanProperty(indexed=False, default=False)
    deviceId = db.StringProperty(indexed=False)

    def __str__(self):
        return unicode(self.id)

    def __eq__(self, other):
        return isinstance(other, Mobile) \
                and self.key() \
                and other.key() \
                and self.id == other.id

    @classmethod
    def create_key(cls, account):
        return db.Key.from_path(cls.kind(), account)

    @property
    def language(self):
        from rogerthat.dal.profile import get_user_profile
        from rogerthat.translations import DEFAULT_LANGUAGE
        profile = get_user_profile(self.user)
        return profile.language if profile else DEFAULT_LANGUAGE

    @property
    def type_string(self):
        return self.typeAsString(self.type) if self.type else None

    @property
    def pushId(self):
        return self.iOSPushId

    @pushId.setter
    def pushId(self, value):
        self.iOSPushId = value

    @property
    def is_ios(self):
        return self.type in self.IOS_TYPES

    @property
    def is_android(self):
        return self.type in self.ANDROID_TYPES

    @property
    def is_windows_phone(self):
        return self.type in (self.TYPE_WINDOWS_PHONE)

    @property
    def app_id(self):
        from rogerthat.utils.app import get_app_id_from_app_user
        return get_app_id_from_app_user(self.user)

    @property
    def is_phone_unregistered(self):
        return self.status > Mobile.STATUS_NEW | Mobile.STATUS_ACCOUNT_CREATED | Mobile.STATUS_REGISTERED


@deserializer
def ds_mobile(stream):
    return model_deserializer(stream, Mobile)

register(Mobile, s_model, ds_mobile)

s_mobile_list = get_list_serializer(s_model)
ds_mobile_list = get_list_deserializer(ds_mobile)
register(List(Mobile), s_mobile_list, ds_mobile_list)


class ErrorPlatformVersion(NdbModel):
    platform_version = ndb.StringProperty()
    client_version = ndb.StringProperty()


class ClientError(NdbModel):
    message = ndb.TextProperty()
    description = ndb.TextProperty()
    count = ndb.IntegerProperty(default=0)
    platform = ndb.IntegerProperty()
    versions = ndb.StructuredProperty(ErrorPlatformVersion, repeated=True)
    first_occurrence_date = ndb.DateTimeProperty(auto_now_add=True)
    last_occurrence_date = ndb.DateTimeProperty(auto_now=True)

    @property
    def id(self):
        return self.key.id()

    @property
    def platform_string(self):
        return Mobile.typeAsString(self.platform) if self.platform in Mobile.TYPES else u'other'

    @property
    def formatted_time(self):
        delta_min = (now() - mktime(self.last_occurrence_date.utctimetuple())) / 60
        if delta_min < 60:
            ds = '%d minutes' % delta_min
        else:
            ds = '%d hour(s)' % (delta_min / 60)
        return u'Last seen %s ago<br>%s<br>First seen: %s' % (
            ds, self.last_occurrence_date.strftime('%Y-%m-%d %H:%M:%S'),
            self.first_occurrence_date.strftime('%Y-%m-%d %H:%M:%S'))

    @property
    def short_error(self):
        result = u''
        if self.description:
            result += u'\n'.join(self.description.splitlines()[0:3]) + u'\n'
        if self.message:
            result += u'\n'.join(self.message.splitlines()[0:4])
        return u'\n'.join(result.splitlines()[0:4])

    @classmethod
    def create_key(cls, key_name):
        return ndb.Key(cls, key_name)

    @classmethod
    def list(cls):
        return cls.query().order(-cls.last_occurrence_date)


class ClientErrorOccurrence(NdbModel):
    user = ndb.StringProperty()
    install_id = ndb.StringProperty()
    occurred_date = ndb.DateTimeProperty()
    user_str = ndb.StringProperty()


class RpcAPIResult(db.Model):
    result = db.TextProperty()
    timestamp = db.IntegerProperty()


class RpcCAPICall(db.Expando):
    timestamp = db.IntegerProperty()
    method = db.StringProperty()
    call = db.TextProperty()
    resultFunction = db.StringProperty(indexed=False)
    errorFunction = db.StringProperty(indexed=False)
    deferredKick = db.BooleanProperty(indexed=False, default=False)
    priority = db.IntegerProperty(indexed=True, default=5)

    def mobile(self):
        return Mobile.get_by_key_name(self.mobileKeyName)

    @property
    def mobileKeyName(self):
        return self.parent_key().name()


class ServiceAPIResult(db.Model):
    running = db.BooleanProperty(indexed=False)
    result = db.TextProperty()
    timestamp = db.IntegerProperty()

    @property
    def user(self):
        return users.User(self.key().name().split('/', 1)[0])

    @classmethod
    def create_key(cls, service_user, json_rpc_id):
        return db.Key.from_path(cls.kind(), '%s/%s' % (service_user.email(), json_rpc_id))


class ServiceAPICallback(db.Expando):
    timestamp = db.IntegerProperty()
    call = db.TextProperty()
    resultFunction = db.StringProperty(indexed=False)
    errorFunction = db.StringProperty(indexed=False)
    retryCount = db.IntegerProperty(indexed=False, default=0)
    targetMFR = db.BooleanProperty(indexed=False, default=False)
    monitor = db.BooleanProperty(indexed=False)
    code = db.IntegerProperty(indexed=False, default=0)
    is_solution = db.BooleanProperty(indexed=False, default=False)

    def put(self, **kwargs):
        if self.targetMFR or not self.is_solution:
            return db.Expando.put(self, **kwargs)

    @property
    def service_identifier(self):
        from rogerthat.models import ServiceIdentity
        return getattr(self, 'internal_service_identity', ServiceIdentity.DEFAULT)

    @property
    def callid(self):
        return self.key().name()

    @property
    def service_user(self):
        return users.User(self.parent_key().name())

    @property
    def user(self):
        logging.warn("ServiceAPICallback.user %s" % get_python_stack_trace())
        return self.service_user

    @property
    def service_identity_user(self):
        from rogerthat.utils.service import create_service_identity_user
        return create_service_identity_user(self.service_user, self.service_identifier)


class Session(CachedModelMixIn, db.Model):

    TYPE_ROGERTHAT = 1
    TYPE_GOOGLE = 2

    user = db.UserProperty()
    timeout = db.IntegerProperty()
    service_identity_user = db.UserProperty(indexed=False)  # used for switching between accounts
    service_users_blob = db.TextProperty()
    shop = db.BooleanProperty(indexed=False, default=False)
    layout_only = db.BooleanProperty(indexed=False, default=False)
    read_only = db.BooleanProperty(indexed=False, default=False)
    name = db.StringProperty(indexed=False)
    deleted = db.BooleanProperty(indexed=True, default=False)
    type = db.IntegerProperty(indexed=False, default=TYPE_ROGERTHAT)
    service_identity = db.StringProperty(indexed=False)  # for the moment only used for locations in solution
    parent_session_secret = db.StringProperty(indexed=False)

    _service_users = None

    @property
    def service_users(self):
        if self._service_users is None:
            if self.service_users_blob is None:
                self._service_users = list()
            else:
                self._service_users = json.loads(self.service_users_blob)
        return self._service_users

    @service_users.setter
    def service_users(self, value):
        result = list()
        for si in value:
            result.append(dict(is_default=si.is_default, service_user=si.service_user.email(), service_identity_user=si.service_identity_user.email(), name=si.name))
        self._service_users = result
        self.service_users_blob = json.dumps(result)

    def has_access(self, email):
        from rogerthat.utils.service import remove_slash_default
        if remove_slash_default(users.User(email)) == remove_slash_default(self.user):
            return True
        logging.info("Looking for access of %s in service users %s", email, self.service_users_blob)
        for si in self.service_users:
            if email in (si["service_user"], si["service_identity_user"]):
                return True
        return False

    @property
    def human_login(self):
        return not self.service_users_blob is None

    @property
    def secret(self):
        return self.key().name()

    @classmethod
    def create_key(cls, secret):
        return db.Key.from_path(cls.kind(), secret)

    def invalidateCache(self):
        invalidate_model_cache(self)


register(Session, s_any, ds_any)


class ServiceLog(db.Model):
    TYPE_CALLBACK = 1
    TYPE_CALL = 2

    STATUS_SUCCESS = 1
    STATUS_ERROR = 2
    STATUS_WAITING_FOR_RESPONSE = 3

    user = db.UserProperty()
    timestamp = db.IntegerProperty()
    type = db.IntegerProperty(indexed=False)  # @ReservedAssignment
    status = db.IntegerProperty(indexed=False)
    function = db.StringProperty(indexed=False)
    request = db.TextProperty()
    response = db.TextProperty()
    error_code = db.IntegerProperty(indexed=False)
    error_message = db.TextProperty()

    @property
    def rpc_id(self):
        return self.parent_key().name()


class NdbServiceLog(NdbModel):
    _use_memcache = False
    _use_cache = False

    TYPE_CALLBACK = 1
    TYPE_CALL = 2

    STATUS_SUCCESS = 1
    STATUS_ERROR = 2
    STATUS_WAITING_FOR_RESPONSE = 3

    user = ndb.UserProperty()
    timestamp = ndb.IntegerProperty()
    type = ndb.IntegerProperty(indexed=False)  # @ReservedAssignment
    status = ndb.IntegerProperty(indexed=False)
    function = ndb.StringProperty(indexed=False)
    request = ndb.TextProperty()
    response = ndb.TextProperty()
    error_code = ndb.IntegerProperty(indexed=False)
    error_message = ndb.TextProperty()

    @classmethod
    def _get_kind(cls):
        return ServiceLog.kind()

    @property
    def rpc_id(self):
        return self.key.parent().name()


class OutStandingFirebaseKick(db.Model):
    timestamp = db.IntegerProperty()

    @property
    def registrationID(self):
        return self.key().name()

    @classmethod
    def createKey(cls, registrationID):
        return db.Key.from_path(cls.kind(), registrationID)
