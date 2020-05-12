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
from contextlib import closing
import json
import logging
import os
from types import NoneType
import urllib
import urlparse
import uuid
from zipfile import ZipFile

from google.appengine.api import images, search
from google.appengine.ext import db, deferred, ndb
from typing import Optional

from mcfw.cache import cached, invalidate_cache
from mcfw.consts import MISSING
from mcfw.imaging import recolor_png
from mcfw.properties import azzert
from mcfw.rpc import arguments, returns, serialize_complex_value
from mcfw.utils import normalize_search_string, chunks
from rogerthat.bizz.embedded_applications import get_embedded_application, EmbeddedApplicationNotFoundException
from rogerthat.bizz.features import Features, mobile_supports_feature
from rogerthat.bizz.forms import get_form
from rogerthat.bizz.friend_helper import FriendHelper
from rogerthat.bizz.friends import userCode, invited_response_receiver, process_invited_response, \
    create_accept_decline_buttons, INVITE_SERVICE_ADMIN
from rogerthat.bizz.i18n import check_i18n_status_of_message_flows, get_translator
from rogerthat.bizz.job.update_friends import schedule_update_a_friend_of_service_user, \
    schedule_update_all_friends_of_service_user, create_update_friend_requests, convert_friend, \
    do_update_friend_request
from rogerthat.bizz.maps.services import cleanup_map_index, add_map_index, \
    save_map_service
from rogerthat.bizz.maps.services.places import get_place_details
from rogerthat.bizz.messaging import BrandingNotFoundException, sendMessage, sendForm, ReservedTagException
from rogerthat.bizz.profile import update_friends, create_user_profile, update_password_hash, _validate_name, \
    create_service_profile
from rogerthat.bizz.qrtemplate import store_template
from rogerthat.bizz.rtemail import generate_auto_login_url, EMAIL_REGEX
from rogerthat.bizz.service.mfd import get_message_flow_by_key_or_name
from rogerthat.bizz.service.mfd.gen import MessageFlowRun
from rogerthat.bizz.system import unregister_mobile
from rogerthat.capi.services import receiveApiCallResult, updateUserData
from rogerthat.consts import MC_DASHBOARD, OFFICIALLY_SUPPORTED_LANGUAGES, MC_RESERVED_TAG_PREFIX, FA_ICONS
from rogerthat.dal import parent_key, put_and_invalidate_cache, app
from rogerthat.dal.app import get_app_by_user, get_app_by_id, get_apps_by_keys
from rogerthat.dal.friend import get_friends_map, get_friends_map_key_by_user, get_friend_category_by_id
from rogerthat.dal.messaging import get_message, get_branding
from rogerthat.dal.mfd import get_service_message_flow_design_key_by_name
from rogerthat.dal.mobile import get_user_active_mobiles, get_mobile_key_by_account
from rogerthat.dal.profile import get_search_config, is_trial_service, get_service_profile, get_user_profile, \
    get_profile_infos, get_profile_info, is_service_identity_user, get_trial_service_by_account, get_search_locations, \
    get_service_or_user_profile, get_profile_key
from rogerthat.dal.roles import get_service_admins, get_service_identities_via_user_roles, get_service_roles_by_ids
from rogerthat.dal.service import get_api_keys, get_api_key, get_api_key_count, get_sik, get_service_interaction_def, \
    get_service_menu_item_by_coordinates, get_service_identity, get_friend_serviceidentity_connection, \
    get_default_service_identity, get_service_identity_not_cached, get_service_identities, get_child_identities, \
    get_service_interaction_defs, get_users_connected_to_service_identity, log_service_activity, \
    get_service_identities_by_service_identity_users, get_regex_callback_configurations, \
    get_regex_callback_configurations_cached
from rogerthat.models import Profile, APIKey, SIKKey, ServiceEmail, ServiceInteractionDef, ShortURL, \
    QRTemplate, Message, MFRSIKey, ServiceMenuDef, Branding, PokeTagMap, ServiceProfile, UserProfile, ServiceIdentity, \
    SearchConfigLocation, ProfilePointer, FacebookProfilePointer, MessageFlowDesign, ServiceTranslation, \
    ServiceMenuDefTagMap, UserData, FacebookUserProfile, App, MessageFlowRunRecord, ServiceCallBackConfiguration, \
    FriendServiceIdentityConnection, FriendMap, UserContext
from rogerthat.models.properties.friend import FriendDetail, FriendDetails
from rogerthat.models.properties.keyvalue import KVStore, InvalidKeyError
from rogerthat.models.settings import ServiceInfo
from rogerthat.models.utils import allocate_id, allocate_ids
from rogerthat.rpc import users
from rogerthat.rpc.models import ServiceAPICallback, ServiceLog, RpcCAPICall, Mobile
from rogerthat.rpc.rpc import mapping, logError
from rogerthat.rpc.service import logServiceError, ServiceApiException, ERROR_CODE_UNKNOWN_ERROR, \
    ERROR_CODE_WARNING_THRESHOLD, BusinessException, SERVICE_API_CALLBACK_MAPPING
from rogerthat.service.api.friends import invited
from rogerthat.service.api.test import test
from rogerthat.settings import get_server_settings
from rogerthat.templates import render
from rogerthat.to.activity import GeoPointWithTimestampTO, GEO_POINT_FACTOR
from rogerthat.to.friends import UpdateFriendRequestTO, FriendTO, ServiceMenuDetailTO, ServiceMenuItemLinkTO, \
    FRIEND_TYPE_SERVICE
from rogerthat.to.messaging import BaseMemberTO, UserMemberTO
from rogerthat.to.messaging.service_callback_results import PokeCallbackResultTO, FlowCallbackResultTypeTO, \
    MessageCallbackResultTypeTO, FormCallbackResultTypeTO
from rogerthat.to.profile import SearchConfigTO
from rogerthat.to.qr import QRDetailsTO
from rogerthat.to.service import ServiceConfigurationTO, APIKeyTO, LibraryMenuIconTO, FindServiceResponseTO, \
    FindServiceItemTO, FindServiceCategoryTO, ServiceIdentityDetailsTO, ServiceLanguagesTO, UserDetailsTO, \
    ReceiveApiCallResultResponseTO, ReceiveApiCallResultRequestTO, SendApiCallCallbackResultTO, \
    ServiceCallbackConfigurationTO, UpdateUserDataResponseTO, ServiceCallbackConfigurationRegexTO, \
    UpdateUserDataRequestTO
from rogerthat.translations import localize, DEFAULT_LANGUAGE
from rogerthat.utils import now, channel, generate_random_key, parse_color, slog, \
    is_flag_set, get_full_language_string, get_officially_supported_languages, try_or_defer, \
    bizz_check, base38, send_mail
from rogerthat.utils.app import get_human_user_from_app_user, get_app_id_from_app_user, create_app_user_by_email
from rogerthat.utils.crypto import md5_hex, sha256_hex
from rogerthat.utils.languages import convert_web_lang_to_iso_lang
from rogerthat.utils.location import haversine, VERY_FAR
from rogerthat.utils.service import get_service_user_from_service_identity_user, create_service_identity_user, \
    get_service_identity_tuple, is_valid_service_identifier, remove_slash_default
from rogerthat.utils.transactions import run_in_transaction, run_in_xg_transaction, on_trans_committed, \
    on_trans_rollbacked


try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

CURRENT_DIR = os.path.dirname(__file__)
ICON_LIBRARY_PATH = os.path.join(CURRENT_DIR, 'icons.zip')

SERVICE_INDEX = "SERVICE_INDEX"
SERVICE_LOCATION_INDEX = "SERVICE_LOCATION_INDEX"

SERVICE_IN_TROUBLE_TAG = u"service_trouble"
IGNORE_SERVICE_TROUBLE_ID = u"ignore_service_trouble"
DISABLE_SERVICE_TROUBLE_ID = u"disable_service_trouble"

MENU_ITEM_LABEL_ATTRS = ['aboutMenuItemLabel', 'messagesMenuItemLabel', 'callMenuItemLabel', 'shareMenuItemLabel']

QR_TEMPLATE_BLUE_PACIFIC = u"Blue Pacific"
QR_TEMPLATE_BROWN_BAG = u"Brown Bag"
QR_TEMPLATE_PINK_PANTHER = u"Pink Panther"
QR_TEMPLATE_BLACK_HAND = u"Black Hand"

DISABLED_BROADCAST_TYPES_USER_DATA_KEY = '%sdisabledBroadcastTypes' % MC_RESERVED_TAG_PREFIX
BROADCAST_TYPES_SERVICE_DATA_KEY = '%sbroadcastTypes' % MC_RESERVED_TAG_PREFIX


class TestCallbackFailedException(ServiceApiException):

    def __init__(self):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_TEST + 0, "Test callback failed")


class ServiceIdentityDoesNotExistException(ServiceApiException):

    def __init__(self, service_identity):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_SERVICE + 0,
                                     u"Service identity does not exist", service_identity=service_identity)


class InvalidValueException(ServiceApiException):

    def __init__(self, property_, reason):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_SERVICE + 1,
                                     u"Invalid value", property=property_, reason=reason)


class InvalidMenuItemCoordinatesException(ServiceApiException):

    def __init__(self):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_SERVICE + 2,
                                     u"A menu item has an x, y and page coordinate, with x and y smaller than 4")


class ReservedMenuItemException(ServiceApiException):

    def __init__(self):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_SERVICE + 3,
                                     u"This menu item is reserved")


class CanNotDeleteBroadcastTypesException(ServiceApiException):

    def __init__(self):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_SERVICE + 4,
                                     u"There are still broadcast settings menu items.")


class InvalidBroadcastTypeException(ServiceApiException):

    def __init__(self, broadcast_type):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_SERVICE + 5,
                                     u"Invalid broadcast type", broadcast_type=broadcast_type)


class DuplicateBroadcastTypeException(ServiceApiException):

    def __init__(self, broadcast_type):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_SERVICE + 6,
                                     u"Duplicate broadcast type", broadcast_type=broadcast_type)


class InvalidNameException(ServiceApiException):

    def __init__(self, message):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_SERVICE + 8,
                                     "Invalid name, it must be shorter than 50 characters.", reason=message)


class ServiceAlreadyExistsException(ServiceApiException):

    def __init__(self):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_SERVICE + 9,
                                     u"Service with that e-mail address already exists")


class UnsupportedLanguageException(ServiceApiException):

    def __init__(self):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_SERVICE + 10,
                                     u"This language is not supported")


class FriendNotFoundException(ServiceApiException):

    def __init__(self):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_SERVICE + 11,
                                     u"User not in friends list")


class InvalidJsonStringException(ServiceApiException):

    def __init__(self):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_SERVICE + 12,
                                     u"Can not parse data as json object")


class AvatarImageNotSquareException(ServiceApiException):

    def __init__(self):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_SERVICE + 13,
                                     u"Expected a square input image")


class CategoryNotFoundException(ServiceApiException):

    def __init__(self):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_SERVICE + 14,
                                     u"Category not found")


class CallbackNotDefinedException(ServiceApiException):

    def __init__(self, function):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_SERVICE + 15,
                                     u"Callback not defined", function=function)


class InvalidAppIdException(ServiceApiException):

    def __init__(self, app_id):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_SERVICE + 17,
                                     u"Invalid app_id", app_id=app_id)


class UnsupportedAppIdException(ServiceApiException):

    def __init__(self, app_id):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_SERVICE + 18,
                                     u"Unsupported app_id", app_id=app_id)


class RoleNotFoundException(ServiceApiException):

    def __init__(self, role_id):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_SERVICE + 19,
                                     u"Role does not exist", role_id=role_id)


class RoleAlreadyExistsException(ServiceApiException):

    def __init__(self, name):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_SERVICE + 20,
                                     u"Role with this name already exists", name=name)


class InvalidRoleTypeException(ServiceApiException):

    def __init__(self, type_):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_SERVICE + 21,
                                     u"Invalid role type", type=type_)


class DeleteRoleFailedHasMembersException(ServiceApiException):

    def __init__(self, role_id):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_SERVICE + 22,
                                     u"Cannot delete role which is still granted to people.", role_id=role_id)


class DeleteRoleFailedHasSMDException(ServiceApiException):

    def __init__(self, role_id):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_SERVICE + 23,
                                     u"Cannot delete role which is still connected to a service menu item",
                                     role_id=role_id)


class UserWithThisEmailAddressAlreadyExistsException(ServiceApiException):

    def __init__(self, email):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_SERVICE + 24,
                                     u"An account with this e-mail address already exists", email=email)


class AppOperationDeniedException(ServiceApiException):

    def __init__(self, app_id):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_SERVICE + 25,
                                     u"No permission to manage app", app_id=app_id)


class ServiceWithEmailDoesNotExistsException(ServiceApiException):

    def __init__(self, service_identity_email):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_SERVICE + 26,
                                     u"There is no service with this email",
                                     service_identity_email=service_identity_email)


class MyDigiPassNotSupportedException(ServiceApiException):

    def __init__(self, unsupported_app_ids):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_SERVICE + 28,
                                     u"Not all supported apps of this service implement MYDIGIPASS.",
                                     unsupported_app_ids=unsupported_app_ids)


class AppFailedToResovelUrlException(ServiceApiException):

    def __init__(self, url):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_SERVICE + 32,
                                     u"Failed to resolve url", url=url)


class AppFailedToCreateUserProfileWithExistingServiceException(ServiceApiException):

    def __init__(self, email):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_SERVICE + 33,
                                     u"Failed to create user profile with the same email as a service account",
                                     email=email)


class InvalidKeyException(ServiceApiException):

    def __init__(self, key):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_SERVICE + 34,
                                     u"Invalid key", key=key)


class DuplicateCategoryIdException(ServiceApiException):

    def __init__(self, category_id):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_SERVICE + 35,
                                     u"Duplicate category id", category_id=category_id)


class DuplicateItemIdException(ServiceApiException):

    def __init__(self, category_id, item_id):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_SERVICE + 36,
                                     u"Duplicate item id", category_id=category_id, item_id=item_id)


class SigningNotSupportedException(ServiceApiException):

    def __init__(self, unsupported_app_ids):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_SERVICE + 37,
                                     u"Not all supported apps of this service implement signing. Apps: %s" % ', '.join(
                                         unsupported_app_ids),
                                     unsupported_app_ids=unsupported_app_ids)


class InvalidSignPayloadException(ServiceApiException):

    def __init__(self):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_SERVICE + 38,
                                     u'Invalid payload. Make sure the payload is base64 encoded properly.')


class ExportBrandingsException(ServiceApiException):

    def __init__(self, errors):
        message = 'The following items must be updated to use the newest version of the ' \
                  'branding with the same description:\n%s' % ' \n'.join(errors)
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_SERVICE + 39, message)


class InvalidGroupTypeException(ServiceApiException):

    def __init__(self, group_type):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_SERVICE + 40,
                                     u"Invalid group type", group_type=group_type)


@returns(users.User)
@arguments(service_user=users.User, service_identity=unicode)
def get_and_validate_service_identity_user(service_user, service_identity):
    if not service_identity or service_identity == MISSING:
        service_identity = ServiceIdentity.DEFAULT

    azzert(':' not in service_user.email(), "service_user.email() should not contain :")

    service_identity_user = create_service_identity_user(service_user, service_identity)

    if service_identity != ServiceIdentity.DEFAULT and get_service_identity(service_identity_user) is None:
        raise ServiceIdentityDoesNotExistException(service_identity=service_identity)

    return service_identity_user


@returns(NoneType)
@arguments(service_user=users.User, qualified_identifier=unicode)
def promote_trial_service(service_user, qualified_identifier):
    ts = get_trial_service_by_account(service_user)

    def trans():
        service_identity = get_default_service_identity(service_user)
        service_identity.qualifiedIdentifier = qualified_identifier
        service_identity.put()
        db.delete(ts)

    xg_on = db.create_transaction_options(xg=True)
    db.run_in_transaction_options(xg_on, trans)


@returns(ServiceConfigurationTO)
@arguments(service_user=users.User)
def get_configuration(service_user):
    profile = get_service_profile(service_user)
    conf = ServiceConfigurationTO()
    conf.callBackURI = profile.callBackURI
    if not profile.sik:

        def trans():
            profile = get_service_profile(service_user, cached=False)
            profile.sik = unicode(generate_random_key())
            sik = SIKKey(key_name=profile.sik)
            sik.user = service_user
            sik.put()
            profile.put()
            return profile

        xg_on = db.create_transaction_options(xg=True)
        profile = db.run_in_transaction_options(xg_on, trans)
    conf.sik = profile.sik
    conf.apiKeys = [APIKeyTO.fromDBAPIKey(k) for k in get_api_keys(service_user)]
    conf.enabled = profile.enabled
    conf.callBackFromJid = u"bot@callback.rogerth.at"
    conf.needsTestCall = profile.testCallNeeded
    conf.callbacks = profile.callbacks
    conf.autoUpdating = profile.autoUpdating
    conf.updatesPending = profile.updatesPending
    conf.autoLoginUrl = generate_auto_login_url(service_user)

    if profile.enabled and profile.callBackURI == "mobidick" and conf.apiKeys:
        settings = get_server_settings()
        conf.mobidickUrl = u"%s/create_session?%s" % (
            settings.mobidickAddress, urllib.urlencode((("ak", conf.apiKeys[0].key), ("sik", conf.sik))))
    else:
        conf.mobidickUrl = None
    conf.actions = [] if conf.mobidickUrl else list(get_configuration_actions(service_user))
    conf.regexCallbackConfigurations = []
    for scc in get_regex_callback_configurations(service_user):
        conf.regexCallbackConfigurations.append(ServiceCallbackConfigurationRegexTO.fromModel(scc))
    return conf


@returns(ServiceLanguagesTO)
@arguments(service_user=users.User)
def get_service_translation_configuration(service_user):
    service_profile = get_service_profile(service_user)
    translationTO = ServiceLanguagesTO()
    translationTO.defaultLanguage = service_profile.defaultLanguage
    translationTO.defaultLanguageStr = get_full_language_string(service_profile.defaultLanguage)
    translationTO.allLanguages = get_officially_supported_languages(iso_format=False)
    translationTO.allLanguagesStr = map(get_full_language_string, translationTO.allLanguages)
    translationTO.nonDefaultSupportedLanguages = sorted(service_profile.supportedLanguages[1:],
                                                        cmp=lambda x, y: 1 if get_full_language_string(
                                                            x) > get_full_language_string(y) else -1)
    return translationTO


@returns(NoneType)
@arguments(service_profile=ServiceProfile, uri=unicode, callbacks=long)
def configure_profile(service_profile, uri, callbacks=long):
    service_profile.testCallNeeded = True
    service_profile.enabled = False
    service_profile.callBackURI = uri
    service_profile.callbacks = callbacks


@returns(NoneType)
@arguments(service_profile=ServiceProfile)
def configure_profile_for_mobidick(service_profile):
    service_profile.testCallNeeded = False
    service_profile.enabled = True
    service_profile.callBackURI = "mobidick"
    callbacks = 0
    for cb in ServiceProfile.CALLBACKS:
        callbacks |= cb
    service_profile.callbacks = callbacks


@returns(NoneType)
@arguments(service_user=users.User)
def configure_mobidick(service_user):
    api_keys = list(get_api_keys(service_user))
    if not api_keys:
        generate_api_key(service_user, "mobidick")

    def trans():
        profile = get_service_profile(service_user, cached=False)
        configure_profile_for_mobidick(profile)
        profile.put()

    db.run_in_transaction(trans)


@returns(NoneType)
@arguments(service_user=users.User, function=unicode, enabled=bool)
def enable_callback_by_function(service_user, function, enabled):
    if function in SERVICE_API_CALLBACK_MAPPING:
        enable_callback(service_user, SERVICE_API_CALLBACK_MAPPING[function], enabled)
    else:
        raise CallbackNotDefinedException(function)


@returns(NoneType)
@arguments(service_user=users.User, callback=int, enabled=bool)
def enable_callback(service_user, callback, enabled):
    azzert(callback in ServiceProfile.CALLBACKS)

    def trans():
        profile = get_service_profile(service_user)
        if enabled:
            profile.callbacks |= callback
        else:
            profile.callbacks &= ~callback
        profile.version += 1
        profile.put()

    xg_on = db.create_transaction_options(xg=True)
    db.run_in_transaction_options(xg_on, trans)


@returns(unicode)
@arguments(sid=ServiceInteractionDef)
def get_service_interact_short_url(sid):
    # type: (ServiceInteractionDef) -> unicode
    # Get the ShortURL its id without fetching the entity
    shorturl_id = ServiceInteractionDef.shortUrl.get_value_for_datastore(sid).id()
    encoded_short_url = base38.encode_int(shorturl_id)
    return '%s/M/%s' % (get_server_settings().baseUrl, encoded_short_url)


@returns(unicode)
@arguments(sid=ServiceInteractionDef)
def get_service_interact_qr_code_url(sid):
    # type: (ServiceInteractionDef) -> unicode
    shorturl_id = ServiceInteractionDef.shortUrl.get_value_for_datastore(sid).id()
    encoded_short_url = base38.encode_int(shorturl_id)
    return u'%s/S/%s' % (get_server_settings().baseUrl, encoded_short_url)


@returns([unicode])
@arguments(service_user=users.User)
def get_configuration_actions(service_user):
    profile = get_service_profile(service_user)
    if not get_api_key_count(service_user):
        yield u"Generate API keys to use from your service code."
    if not profile.callBackURI:
        yield u"Configure callback api."
    if not profile.sik:
        yield u"Generate your service identifier key."
    if profile.testCallNeeded:
        yield u"Execute the test callback, to validate the configuration."


@returns(NoneType)
@arguments(service_user=users.User)
def create_default_qr_templates(service_user):
    si = get_service_identity(create_service_identity_user(service_user, ServiceIdentity.DEFAULT))
    app = get_app_by_id(si.app_id)
    for k in app.qrtemplate_keys:
        qr_template = QRTemplate.get_by_key_name(k)
        azzert(qr_template, u"QRTemplate of %s with key %s did not exist" % (si.app_id, k))
        store_template(service_user, qr_template.blob, qr_template.description,
                       u"".join(("%X" % c).rjust(2, '0') for c in qr_template.body_color))


@returns(unicode)
@arguments(app_id=unicode, description=unicode)
def create_qr_template_key_name(app_id, description):
    return QRTemplate.create_key_name(app_id, description)


@returns(tuple)
@arguments(key_name=unicode)
def get_qr_templete_key_name_info(key_name):
    info = key_name.split(":", 1)
    return info[0], info[1]


@returns(tuple)
@arguments(app_id=unicode, color=[int])
def get_default_qr_template_by_app_id(app_id, color=None):
    app = get_app_by_id(app_id)
    azzert(app.qrtemplate_keys, u'%s has no QR templates defined' % app_id)
    qr_template = QRTemplate.get_by_key_name(app.qrtemplate_keys[0])
    azzert(qr_template, u"Default QRTemplate of %s with key %s did not exist" % (app_id, app.qrtemplate_keys[0]))
    return qr_template, color or map(int, qr_template.body_color)


@returns(NoneType)
@arguments(service_user=users.User, identifier=unicode)
def delete_service_identity(service_user, identifier):
    from rogerthat.bizz.news import delete_news_items_service_identity_user

    if identifier == ServiceIdentity.DEFAULT:
        raise BusinessException("Delete failed. Cannot delete default Service Identity.")
    service_identity_user = create_service_identity_user(service_user, identifier)

    @db.non_transactional
    def _count_connected_users(service_identity_user):
        return len(get_users_connected_to_service_identity(service_identity_user, None, 1)[0])

    def trans():
        service_identity = get_service_identity(service_identity_user)
        if service_identity is None:
            raise BusinessException("Delete failed. This service identity does not exist!")
        if len(get_service_interaction_defs(service_user, identifier, None)["defs"]) > 0:
            raise BusinessException("Delete failed. This service identity still has QR codes pointing to it.")
        if _count_connected_users(service_identity_user) > 0:
            raise BusinessException("Delete failed. This service identity still has connected friends.")
        # cleanup any previous index entry
        email = service_identity_user.email()
        svc_index = search.Index(name=SERVICE_INDEX)
        loc_index = search.Index(name=SERVICE_LOCATION_INDEX)
        on_trans_committed(_cleanup_search_index, email, svc_index, loc_index)
        on_trans_committed(cleanup_map_index, service_identity_user)
        if service_identity.serviceData:
            service_identity.serviceData.clear()
        service_identity.delete()

        on_trans_committed(delete_news_items_service_identity_user, service_identity_user)
        on_trans_committed(channel.send_message, service_user, u'rogerthat.services.identity.refresh')

    db.run_in_transaction(trans)


@returns(unicode)
@arguments(service_user=users.User, service_identifier=unicode, app_id=unicode, tag=unicode)
def _create_recommendation_qr_code(service_user, service_identifier, app_id, tag=ServiceInteractionDef.TAG_INVITE):
    logging.info("Creating recommendation QR for %s/%s" % (service_user.email(), service_identifier))
    qrtemplate, _ = get_default_qr_template_by_app_id(app_id)
    sid = _create_qrs(service_user, service_identifier, u"Connect", [tag], qrtemplate, None)[0][0]
    sid.deleted = True
    sid.put()
    return str(sid.key())


@returns(NoneType)
@arguments(to=ServiceIdentityDetailsTO, si=ServiceIdentity)
def _populate_service_identity(to, si):
    """
    Args:
        to (ServiceIdentityDetailsTO)
        si (ServiceIdentity)
    """

    @db.non_transactional
    def get_default_supported_app_ids():
        default_app = app.get_default_app()
        return [default_app.app_id] if default_app else [App.APP_ID_ROGERTHAT]

    is_default = si.identifier == ServiceIdentity.DEFAULT
    # Comparing with True because values could be MISSING

    dsi = None
    for p in ServiceIdentityDetailsTO.INHERITANCE_PROPERTIES:
        if getattr(to, p) is True:
            if is_default:
                raise InvalidValueException(p)
            dsi = get_default_service_identity(si.service_user)
            break

    # Do not touch menuGeneration and creation timestamp

    if to.name is not MISSING:
        si.name = to.name

    # Do not update MISSING properties
    if to.description_use_default is True:
        si.description = dsi.description
    elif to.description is not MISSING:
        si.description = to.description

    if to.description_branding_use_default is True:
        si.descriptionBranding = dsi.descriptionBranding
    elif to.description_branding is not MISSING:
        si.descriptionBranding = to.description_branding

    if to.menu_branding_use_default is True:
        si.menuBranding = dsi.menuBranding
    elif to.menu_branding is not MISSING:
        si.menuBranding = to.menu_branding

    if to.phone_number_use_default is True:
        si.mainPhoneNumber = dsi.mainPhoneNumber
    elif to.phone_number is not MISSING:
        si.mainPhoneNumber = to.phone_number

    if to.phone_call_popup_use_default is True:
        si.callMenuItemConfirmation = dsi.callMenuItemConfirmation
    elif to.phone_call_popup is not MISSING:
        si.callMenuItemConfirmation = to.phone_call_popup

    if to.admin_emails is not MISSING:
        si.metaData = ",".join(to.admin_emails)
    if to.app_data is not MISSING:
        si.appData = None
        if to.app_data:
            try:
                data_object = json.loads(to.app_data)
            except:
                raise InvalidJsonStringException()
            if data_object is None:
                raise InvalidJsonStringException()
            if not isinstance(data_object, dict):
                raise InvalidJsonStringException()

            if si.serviceData is None:
                si.serviceData = KVStore(si.key())
            else:
                si.serviceData.clear()
            si.serviceData.from_json_dict(data_object)

    if to.qualified_identifier is not MISSING:
        si.qualifiedIdentifier = to.qualified_identifier
    if to.recommend_enabled is not MISSING:
        si.shareEnabled = to.recommend_enabled
    elif si.shareEnabled is None:
        si.shareEnabled = False  # in case shareEnabled is not set yet, set it to False

    if to.email_statistics_use_default is True:
        si.emailStatistics = dsi.emailStatistics
    elif to.email_statistics is not MISSING:
        si.emailStatistics = to.email_statistics

    if to.app_ids_use_default is True:
        app_ids_difference = set(si.appIds).symmetric_difference(dsi.appIds)
        si.defaultAppId = dsi.defaultAppId
        si.appIds = dsi.appIds
    elif to.app_ids is not MISSING:
        app_ids_difference = set(si.appIds).symmetric_difference(to.app_ids)
        si.appIds = to.app_ids or get_default_supported_app_ids()
    else:
        app_ids_difference = None
    if app_ids_difference:
        supported_app_ids = get_default_supported_app_ids()
        si.defaultAppId = to.app_ids[0] if to.app_ids else supported_app_ids[0]
        si.appIds = to.app_ids or supported_app_ids

    if to.content_branding_hash is not MISSING:
        si.contentBrandingHash = to.content_branding_hash

    if to.home_branding_use_default is True:
        si.homeBrandingHash = dsi.homeBrandingHash
    elif to.home_branding_hash is not MISSING:
        si.homeBrandingHash = to.home_branding_hash

    si.inheritanceFlags = 0
    # Comparing with True again because values could be MISSING
    if to.description_use_default is True:
        si.inheritanceFlags |= ServiceIdentity.FLAG_INHERIT_DESCRIPTION
    if to.description_branding_use_default is True:
        si.inheritanceFlags |= ServiceIdentity.FLAG_INHERIT_DESCRIPTION_BRANDING
    if to.menu_branding_use_default is True:
        si.inheritanceFlags |= ServiceIdentity.FLAG_INHERIT_MENU_BRANDING
    if to.phone_number_use_default is True:
        si.inheritanceFlags |= ServiceIdentity.FLAG_INHERIT_PHONE_NUMBER
    if to.phone_call_popup_use_default is True:
        si.inheritanceFlags |= ServiceIdentity.FLAG_INHERIT_PHONE_POPUP_TEXT
    if to.search_use_default is True:
        si.inheritanceFlags |= ServiceIdentity.FLAG_INHERIT_SEARCH_CONFIG
    if to.email_statistics_use_default is True:
        si.inheritanceFlags |= ServiceIdentity.FLAG_INHERIT_EMAIL_STATISTICS
    if to.app_ids_use_default is True:
        si.inheritanceFlags |= ServiceIdentity.FLAG_INHERIT_APP_IDS
    if to.home_branding_use_default is True:
        si.inheritanceFlags |= ServiceIdentity.FLAG_INHERIT_HOME_BRANDING


def _validate_service_identity(to, is_trial):
    if to.identifier is MISSING or not to.identifier or not is_valid_service_identifier(to.identifier):
        raise InvalidValueException(u"identifier", u"Identifier should contain lowercase characters a-z or 0-9 or .-_")
    if to.name is not MISSING:
        if not to.name:
            raise InvalidValueException(u"name", u"Name is a required field")
        try:
            to.name = _validate_name(to.name)
        except ValueError as e:
            logging.debug("Invalid name", exc_info=1)
            raise InvalidNameException(e.message)
        if EMAIL_REGEX.match(to.name):
            raise InvalidValueException(u"name", u'Name cannot be an e-mail address')
    if is_trial and to.search_config is not MISSING and to.search_config and to.search_config.enabled:
        raise InvalidValueException(u"search_config", u'Service search & discovery is not supported for trial accounts')


@returns(ServiceIdentity)
@arguments(service_user=users.User, to=ServiceIdentityDetailsTO)
def create_service_identity(service_user, to):
    if to.identifier == ServiceIdentity.DEFAULT:
        raise InvalidValueException(u"identifier", u"Cannot create default Service Identity")
    if to.name is MISSING:
        raise InvalidValueException(u"name", u"Name is a required field")
    is_trial = is_trial_service(service_user)
    _validate_service_identity(to, is_trial)

    azzert(get_service_profile(service_user))
    service_identity_user = create_service_identity_user(service_user, to.identifier)

    default_svc_identity_user = create_service_identity_user(service_user, ServiceIdentity.DEFAULT)
    default_si = get_service_identity(default_svc_identity_user)
    default_share_sid = ServiceInteractionDef.get(default_si.shareSIDKey)
    app_id = to.app_ids[0] if to.app_ids is not MISSING and to.app_ids else app.get_default_app().app_id
    share_sid_key = _create_recommendation_qr_code(service_user, to.identifier, app_id, default_share_sid.tag)

    def trans():
        if get_service_identity_not_cached(service_identity_user) is not None:
            raise BusinessException("This service identity already exists!")

        si_key = ServiceIdentity.keyFromUser(service_identity_user)
        si = ServiceIdentity(key=si_key)
        si.serviceData = KVStore(si_key)
        _populate_service_identity(to, si)
        si.shareSIDKey = share_sid_key
        si.creationTimestamp = now()
        si.menuGeneration = 0
        si.version = 1
        si.put()
        ProfilePointer.create(si.user).put()
        if not is_trial:
            if to.search_use_default is True:
                default_search_config, default_locations = get_search_config(default_svc_identity_user)
                update_search_config(service_identity_user,
                                     SearchConfigTO.fromDBSearchConfig(default_search_config, default_locations))
            else:
                update_search_config(service_identity_user, to.search_config, accept_missing=True)

        return si

    si = run_in_transaction(trans, xg=True)
    channel.send_message(service_user, u'rogerthat.services.identity.refresh')
    return si


@returns(ServiceIdentity)
@arguments(service_user=users.User, to=ServiceIdentityDetailsTO)
def update_service_identity(service_user, to):
    is_trial = is_trial_service(service_user)
    _validate_service_identity(to, is_trial)

    service_identity_user = create_service_identity_user(service_user, to.identifier)
    if get_service_identity(service_identity_user) is None:
        raise ServiceIdentityDoesNotExistException(to.identifier)

    if not to.menu_branding_use_default and to.menu_branding:
        b = get_branding(to.menu_branding)
        if b.type != Branding.TYPE_NORMAL:
            raise InvalidValueException(u"menu_branding", u"This branding cannot be used as menu branding")

    if not to.description_branding_use_default and to.description_branding:
        b = get_branding(to.description_branding)
        if b.type != Branding.TYPE_NORMAL:
            raise InvalidValueException(u"description_branding",
                                        u"This branding cannot be used as description branding")

    if not to.home_branding_use_default and to.home_branding_hash:
        b = get_branding(to.home_branding_hash)
        if b.type == Branding.TYPE_NORMAL:
            raise InvalidValueException(u"home_branding_hash",
                                        u"This branding cannot be used as home branding")

    azzert(get_service_profile(service_user))

    def trans():
        si_key = ServiceIdentity.keyFromUser(service_identity_user)
        si = ServiceIdentity.get(si_key)
        _populate_service_identity(to, si)
        si.version += 1
        si.put()

        if not is_trial:
            if to.search_use_default is True:
                default_svc_identity_user = create_service_identity_user(service_user, ServiceIdentity.DEFAULT)
                default_search_config, default_locations = get_search_config(default_svc_identity_user)
                update_search_config(service_identity_user,
                                     SearchConfigTO.fromDBSearchConfig(default_search_config, default_locations))
            elif to.search_config is not MISSING:
                update_search_config(service_identity_user, to.search_config)

        update_friends(si)
        if to.identifier == ServiceIdentity.DEFAULT:
            deferred.defer(_update_inheriting_service_identities, si_key, is_trial, _transactional=True)
        return si

    xg_on = db.create_transaction_options(xg=True)
    si = db.run_in_transaction_options(xg_on, trans)
    channel.send_message(service_user, u'rogerthat.services.identity.refresh')
    return si


@returns(ServiceIdentity)
@arguments(service_user=users.User, to=ServiceIdentityDetailsTO)
def create_or_update_service_identity(service_user, to):
    if to.identifier is MISSING:
        to.identifier = ServiceIdentity.DEFAULT
    service_identity_user = create_service_identity_user(service_user, to.identifier)

    f = update_service_identity if get_service_identity(service_identity_user) else create_service_identity
    f(service_user, to)


@returns(NoneType)
@arguments(default_service_identity_key=db.Key, is_trial=bool)
def _update_inheriting_service_identities(default_service_identity_key, is_trial):
    azzert(default_service_identity_key.name() == ServiceIdentity.DEFAULT)

    def trans(default_service_identity_key):
        default_service_identity = db.get(default_service_identity_key)
        default_search_initialized = False
        default_search_config = default_locations = None

        service_identities_modified = []
        search_config_update_list = []

        for child_identity in get_child_identities(default_service_identity.service_user):
            if child_identity.inheritanceFlags & ~ServiceIdentity.FLAG_INHERIT_SEARCH_CONFIG != 0:
                if is_flag_set(ServiceIdentity.FLAG_INHERIT_DESCRIPTION, child_identity.inheritanceFlags):
                    child_identity.description = default_service_identity.description
                if is_flag_set(ServiceIdentity.FLAG_INHERIT_DESCRIPTION_BRANDING, child_identity.inheritanceFlags):
                    child_identity.descriptionBranding = default_service_identity.descriptionBranding
                if is_flag_set(ServiceIdentity.FLAG_INHERIT_MENU_BRANDING, child_identity.inheritanceFlags):
                    child_identity.menuBranding = default_service_identity.menuBranding
                if is_flag_set(ServiceIdentity.FLAG_INHERIT_PHONE_NUMBER, child_identity.inheritanceFlags):
                    child_identity.mainPhoneNumber = default_service_identity.mainPhoneNumber
                if is_flag_set(ServiceIdentity.FLAG_INHERIT_PHONE_POPUP_TEXT, child_identity.inheritanceFlags):
                    child_identity.callMenuItemConfirmation = default_service_identity.callMenuItemConfirmation
                if is_flag_set(ServiceIdentity.FLAG_INHERIT_HOME_BRANDING, child_identity.inheritanceFlags):
                    child_identity.homeBrandingHash = default_service_identity.homeBrandingHash
                child_identity.version += 1
                service_identities_modified.append(child_identity)
            if not is_trial and is_flag_set(ServiceIdentity.FLAG_INHERIT_SEARCH_CONFIG,
                                            child_identity.inheritanceFlags):
                if not default_search_initialized:
                    default_search_config, default_locations = get_search_config(default_service_identity.user)
                    default_search_initialized = True
                search_config_update_list.append(
                    (child_identity.user, SearchConfigTO.fromDBSearchConfig(default_search_config, default_locations)))

        if service_identities_modified:
            put_and_invalidate_cache(*service_identities_modified)

        return service_identities_modified, search_config_update_list

    service_identities_modified, search_config_update_list = db.run_in_transaction(trans, default_service_identity_key)
    if service_identities_modified:
        map(update_friends, service_identities_modified)

    # Make sure to update search config only AFTER the service identities have been stored
    if not is_trial:
        for search_config_update_entry in search_config_update_list:
            update_search_config(*search_config_update_entry)


@returns(NoneType)
@arguments(service_identity_user=users.User, search_config=SearchConfigTO)
def update_search_config(service_identity_user, search_config):
    from rogerthat.bizz.news import update_visibility_news_items

    if search_config is MISSING or search_config is None:
        search_config = SearchConfigTO()
        search_config.enabled = False
        search_config.keywords = None
        search_config.locations = list()

    def trans():
        sc, locs = get_search_config(service_identity_user)
        old_search_enabled = sc.enabled
        sc.enabled = search_config.enabled
        sc.keywords = search_config.keywords
        db.delete_async(locs)
        if search_config.locations is not MISSING:
            for loc in search_config.locations:
                lc = SearchConfigLocation(parent=sc)
                lc.address = loc.address
                lc.lat = loc.lat
                lc.lon = loc.lon
                db.put_async(lc)
        deferred.defer(re_index, service_identity_user, _transactional=True)
        if old_search_enabled != search_config.enabled:
            deferred.defer(update_visibility_news_items, service_identity_user, sc.enabled, _transactional=True)
        db.put_async(sc)

    if db.is_in_transaction():
        return trans()
    else:
        xg_on = db.create_transaction_options(xg=True)
        return db.run_in_transaction_options(xg_on, trans)


@returns(ServiceProfile)
@arguments(user=users.User)
def convert_user_to_service(user):
    from rogerthat.bizz.news import create_default_news_settings
    profile = get_user_profile(user)
    # Deny conversion when user has still friends
    friendMap = get_friends_map(user)
    if friendMap.friends:
        raise ValueError("Cannot convert to service when user still has friends!")
    # Unregister mobiles
    for mobile in get_user_active_mobiles(user):
        unregister_mobile(user, mobile)

    share_sid_key = _create_recommendation_qr_code(user, ServiceIdentity.DEFAULT, get_app_id_from_app_user(user))

    # Create ServiceProfile
    def trans():
        service_profile = ServiceProfile(key=profile.key())
        # Copy all properties of Profile
        for prop in (p for p in Profile.properties().iterkeys() if p != '_class'):
            setattr(service_profile, prop, getattr(profile, prop))
        service_profile.testCallNeeded = True
        service_profile.put()

        si = ServiceIdentity(
            key=ServiceIdentity.keyFromUser(create_service_identity_user(user, ServiceIdentity.DEFAULT)))
        si.shareSIDKey = share_sid_key
        si.shareEnabled = False
        si.name = profile.name
        si.defaultAppId = App.APP_ID_ROGERTHAT
        si.appIds = [App.APP_ID_ROGERTHAT]
        si.put()
        ProfilePointer.create(si.user).put()

        # Create some default qr templates
        if QRTemplate.gql("WHERE ANCESTOR IS :1", parent_key(user)).count() == 0:
            deferred.defer(create_default_qr_templates, user, _transactional=True)
        deferred.defer(create_default_news_settings, user, service_profile.organizationType, _transactional=True)

        return service_profile

    xg_on = db.create_transaction_options(xg=True)
    service_profile = db.run_in_transaction_options(xg_on, trans)

    if isinstance(profile, FacebookUserProfile):
        db.delete(FacebookProfilePointer.all().filter("user =", user).fetch(None))

    return service_profile


@returns(ServiceConfigurationTO)
@arguments(service_user=users.User, name=unicode)
def generate_api_key(service_user, name):
    _generate_api_key(name, service_user).put()
    return get_configuration(service_user)


@returns(MFRSIKey)
@arguments(service_identity_user=users.User)
def get_mfr_sik(service_identity_user):
    from rogerthat.dal.service import get_mfr_sik as get_mfr_sik_dal
    svc_user = get_service_user_from_service_identity_user(service_identity_user)
    sik = get_mfr_sik_dal(svc_user)
    if not sik:
        sik = MFRSIKey(key_name=svc_user.email(), parent=parent_key(svc_user))
        sik.sik = generate_random_key()
        sik.put()
    return sik


@returns(APIKey)
@arguments(service_identity_user=users.User)
def get_mfr_api_key(service_identity_user):
    from rogerthat.dal.service import get_mfr_api_key as get_mfr_api_key_dal
    svc_user = get_service_user_from_service_identity_user(service_identity_user)
    api_key = get_mfr_api_key_dal(svc_user)
    if not api_key:
        api_key = _generate_api_key("mfr_api_key", svc_user)
        api_key.mfr = True
        api_key.put()
    return api_key


@returns(ServiceConfigurationTO)
@arguments(service_user=users.User, key=unicode)
def delete_api_key(service_user, key):
    ak = get_api_key(key)
    if ak:
        azzert(ak.user == service_user)
        ak.delete()
        if not any(get_configuration_actions(service_user)):
            profile = get_service_profile(service_user)
            profile.testCallNeeded = True
            profile.enabled = False
            profile.put()
    return get_configuration(service_user)


def _disable_svc(service_user, admin_user):
    service_profile = get_service_profile(service_user)
    service_profile.enabled = False
    service_profile.put()
    logging.warning('Admin user %s disables troubled service %s' % (admin_user.email(), service_user.email()))


@returns(NoneType)
@arguments(message=Message)
def ack_service_in_trouble(message):
    azzert(message.tag == SERVICE_IN_TROUBLE_TAG)
    service_user = message.troubled_service_user
    admin_user = message.troubled_admin_user
    if message.memberStatusses[message.members.index(admin_user)].button_index == message.buttons[
            DISABLE_SERVICE_TROUBLE_ID].index:
        try_or_defer(_disable_svc, service_user, admin_user)
    else:
        logging.info('Admin user %s does not disable troubled service %s' % (admin_user.email(), service_user.email()))


@returns(ServiceConfigurationTO)
@arguments(service_user=users.User)
def enable_service(service_user):
    azzert(not any(get_configuration_actions(service_user)))

    def trans():
        # enable profile
        profile = get_service_profile(service_user, cached=False)
        profile.enabled = True
        # enable records for processing
        from rogerthat.bizz.job.reschedule_service_api_callback_records import run
        timestamp = now()
        deferred.defer(run, timestamp, service_user, _transactional=True)
        # send mail
        text = render("service_enabled", None, {})
        html = render("service_enabled_html", None, {})
        se = ServiceEmail(parent=parent_key(service_user), timestamp=timestamp, messageText=text, messageHtml=html,
                          subject="Your Rogerthat service has been enabled.")
        profile.put()  # XXX:
        se.put()  # These two puts should be done in one call
        return se  # But profile needs cache update support for this --> use put_and_invalidate cache

    se = db.run_in_transaction(trans)
    settings = get_server_settings()
    send_mail(settings.senderEmail, service_user.email(), se.subject, se.messageText, html=se.messageHtml)
    return get_configuration(service_user)


@returns(NoneType)
@arguments(service_profile=ServiceProfile, reason=unicode)
def send_callback_delivery_warning(service_profile, reason):
    if service_profile.lastWarningSent and (service_profile.lastWarningSent + 3600) > now():
        return

    def trans():
        profile = get_service_profile(service_profile.user, cached=False)
        profile.lastWarningSent = now()
        profile.put()
        return profile

    db.run_in_transaction(trans)
    admins = [UserMemberTO(users.User(a.user_email), Message.ALERT_FLAG_VIBRATE | Message.ALERT_FLAG_RING_15) for a in
              get_service_admins(service_profile.user)]

    subject = "Rogerthat service %s will soon be disabled" % service_profile.user.email()
    text = render("service_soon_disabled", None, {"reason": reason})
    html = render("service_soon_disabled_html", None, {"reason": reason})

    settings = get_server_settings()
    emails = [a.member.email() for a in admins] + [service_profile.user.email()]
    bcc_emails = ['services@onzestadapp.be']
    send_mail(settings.senderEmail, emails, subject, text, html=html, bcc_emails=bcc_emails)


@returns(ServiceConfigurationTO)
@arguments(service_user=users.User, reason=unicode)
def disable_service(service_user, reason):

    def trans():
        # disable profile
        profile = get_service_profile(service_user, cached=False)
        profile.enabled = False
        # disable records for processing
        from rogerthat.bizz.job.unschedule_service_api_callback_records import run
        deferred.defer(run, service_user, _transactional=True)
        # send mail
        text = render("service_disabled", None, {"reason": reason})
        html = render("service_disabled_html", None, {"reason": reason})
        se = ServiceEmail(parent=parent_key(service_user), timestamp=now(), messageText=text, messageHtml=html,
                          subject="Rogerthat service %s has been disabled!" % profile.user.email())
        profile.put()  # XXX:
        se.put()  # These two puts should be done in one call
        return se  # But profile needs cache update support for this --> use put_and_invalidate cache

    se = db.run_in_transaction(trans)
    admins = [UserMemberTO(users.User(a.user_email),
                           Message.ALERT_FLAG_VIBRATE | Message.ALERT_FLAG_RING_5 | Message.ALERT_FLAG_INTERVAL_5) for a
              in get_service_admins(service_user)]
    settings = get_server_settings()
    emails = [a.member.email() for a in admins] + [service_user.email()]
    bcc_emails = ['services@onzestadapp.be']
    send_mail(settings.senderEmail, emails, se.subject, se.messageText, html=se.messageHtml, bcc_emails=bcc_emails)
    return get_configuration(service_user)


@returns(ServiceConfigurationTO)
@arguments(service_user=users.User, httpURI=unicode)
def update_callback_configuration(service_user, httpURI):

    def trans():
        profile = get_service_profile(service_user, cached=False)
        profile.callBackURI = httpURI.strip() if httpURI else None
        if httpURI == "mobidick":
            profile.testCallNeeded = False
            profile.enabled = True
        else:
            profile.testCallNeeded = bool(httpURI)
            profile.enabled = False
        profile.put()

    db.run_in_transaction(trans)
    return get_configuration(service_user)


@returns(ServiceConfigurationTO)
@arguments(service_user=users.User, name=unicode, regex=unicode, httpURI=unicode)
def create_callback_configuration(service_user, name, regex, httpURI):

    def trans():
        callback_config_key = ServiceCallBackConfiguration.create_key(name, service_user)
        callback_config = ServiceCallBackConfiguration.get(callback_config_key)
        if not callback_config:
            callback_config = ServiceCallBackConfiguration(key=callback_config_key)
        callback_config.creationTime = now()
        callback_config.regex = regex
        callback_config.callBackURI = httpURI.strip() if httpURI else None
        callback_config.put()

    db.run_in_transaction(trans)

    invalidate_cache(get_regex_callback_configurations_cached, service_user)

    return get_configuration(service_user)


@returns()
@arguments(service_user=users.User, name=unicode)
def test_callback_configuration(service_user, name):
    callback_config = ServiceCallBackConfiguration.get(ServiceCallBackConfiguration.create_key(name, service_user))
    if callback_config:
        from google.appengine.api.memcache import set  # @UnresolvedImport
        set(service_user.email() + "_interactive_logs", True, 300)
        perform_test_callback(service_user, callback_name=name)


@returns(ServiceConfigurationTO)
@arguments(service_user=users.User, name=unicode)
def delete_callback_configuration(service_user, name):
    callback_config = ServiceCallBackConfiguration.get(ServiceCallBackConfiguration.create_key(name, service_user))
    if callback_config:
        callback_config.delete()

    invalidate_cache(get_regex_callback_configurations_cached, service_user)
    return get_configuration(service_user)


@returns(NoneType)
@arguments(service_user=users.User, language=unicode, enabled=bool)
def set_supported_language(service_user, language, enabled):
    if language not in OFFICIALLY_SUPPORTED_LANGUAGES:
        logging.error("Trying to set non-supported language %s for service %s" % (language, service_user.email()))
        return

    def trans():
        profile = get_service_profile(service_user, cached=False)
        if language in profile.supportedLanguages:
            # Language is currently supported
            if enabled:
                logging.warning(
                    "Trying to enable already enabled language %s of service %s" % (language, service_user.email()))
                return
            if profile.supportedLanguages.index(language) == 0:
                logging.error(
                    "Trying to modify status of default language %s of service %s" % (language, service_user.email()))
                return
            profile.supportedLanguages.remove(language)
            profile.put()
        else:
            # Language is currently not supported
            if not enabled:
                logging.warning(
                    "Trying to disable already disabled language %s of service %s" % (language, service_user.email()))
                return
            profile.supportedLanguages.append(language)
            profile.put()

    db.run_in_transaction(trans)
    deferred.defer(check_i18n_status_of_message_flows, service_user)


@returns(ServiceConfigurationTO)
@arguments(service_user=users.User)
def regenerate_sik(service_user):

    def trans():
        profile = get_service_profile(service_user, cached=False)
        if profile.sik:
            sik = get_sik(profile.sik)
            if sik:
                sik.delete()
        profile.sik = unicode(generate_random_key())
        sik = SIKKey(key_name=profile.sik)
        sik.user = service_user
        sik.put()
        profile.testCallNeeded = True
        profile.enabled = False
        profile.put()

    xg_on = db.create_transaction_options(xg=True)
    db.run_in_transaction_options(xg_on, trans)
    return get_configuration(service_user)


@returns(NoneType)
@arguments(svc_user=users.User, sid_id=(int, long), description=unicode, tag=unicode, static_flow=unicode,
           branding_hash=unicode)
def update_qr(svc_user, sid_id, description, tag, static_flow, branding_hash=None):
    if branding_hash and not get_branding(branding_hash):
        raise BrandingNotFoundException()
    sid = get_service_interaction_def(svc_user, sid_id)
    sid.staticFlowKey = str(get_service_message_flow_design_key_by_name(svc_user, static_flow)) if static_flow else None
    sid.tag = tag
    sid.description = description
    sid.branding = branding_hash
    sid.put()


@returns(QRDetailsTO)
@arguments(svc_user=users.User, description=unicode, tag=unicode, template_key=unicode, service_identifier=unicode,
           static_flow=unicode, branding_hash=unicode)
def create_qr(svc_user, description, tag, template_key, service_identifier, static_flow, branding_hash=None):
    return bulk_create_qr(svc_user, description, [tag], template_key, service_identifier, static_flow, branding_hash)[0]


@returns([QRDetailsTO])
@arguments(svc_user=users.User, description=(unicode, [unicode]), tags=[unicode], template_key=unicode,
           service_identifier=unicode, static_flow=unicode, branding_hash=unicode)
def bulk_create_qr(svc_user, description, tags, template_key, service_identifier, static_flow, branding_hash=None):
    service_identity_user = create_service_identity_user(svc_user, service_identifier)
    azzert(is_service_identity_user(service_identity_user))

    for tag in tags:
        if tag.startswith(MC_RESERVED_TAG_PREFIX):
            raise ReservedTagException()

    if branding_hash and not get_branding(branding_hash):
        raise BrandingNotFoundException()

    if template_key and template_key != MISSING:
        qr_template = QRTemplate.get_by_id(int(template_key[2:], 16), parent_key(svc_user))
    else:
        qr_template = None

    static_flow_key = str(get_service_message_flow_design_key_by_name(svc_user, static_flow)) if static_flow else None
    r = _create_qrs(svc_user, service_identifier, description, tags, qr_template, static_flow_key, branding_hash)
    results = []
    for sid, id_, user_code in r:
        result = QRDetailsTO()
        result.image_uri = u"%s/si/%s/%s" % (get_server_settings().baseUrl, user_code, id_)
        result.content_uri = get_service_interact_qr_code_url(sid)
        result.email_uri = get_service_interact_short_url(sid) + "?email"
        result.sms_uri = get_service_interact_short_url(sid)
        results.append(result)
    return results


@db.non_transactional
def get_shorturl_for_qr(service_user, sid_id):
    user_code = userCode(service_user)
    return (ShortURL(key=db.Key.from_path(ShortURL.kind(), allocate_id(ShortURL)),
                     full="/q/s/%s/%s" % (user_code, sid_id)),
            user_code)


@returns([tuple])
@arguments(svc_user=users.User, service_identifier=unicode, description=(unicode, [unicode]), tags=[unicode],
           qr_template=QRTemplate, static_flow_key=unicode, branding=unicode)
def _create_qrs(svc_user, service_identifier, description, tags, qr_template, static_flow_key, branding=None):
    if isinstance(description, list):
        if len(description) != len(tags):
            raise InvalidValueException('description',
                                        'There should be as much descriptions as tags. Got %s tags, %s descriptions.'
                                        % (len(tags), len(description)))

        def descriptions():
            return iter(description)

    else:

        def descriptions():
            for _ in xrange(len(tags)):
                yield description

    parent = parent_key(svc_user)
    ids = allocate_ids(ServiceInteractionDef, len(tags), parent)
    su_and_user_codes = [get_shorturl_for_qr(svc_user, id_) for id_ in ids]
    sus = []
    user_codes = []
    for su, user_code in su_and_user_codes:
        sus.append(su)
        user_codes.append(user_code)
    for chunk in chunks(sus, 200):
        db.put(chunk)

    def cleanup_short_urls(short_urls):
        db.delete(short_urls)

    def trans():
        on_trans_rollbacked(cleanup_short_urls, sus)
        to_put = list()
        result = list()
        for id_, tag, su, user_code, descr in zip(ids, tags, sus, user_codes, descriptions()):
            sid = ServiceInteractionDef(key=db.Key.from_path(ServiceInteractionDef.kind(), id_, parent=parent),
                                        description=descr, tag=tag, timestamp=now(),
                                        service_identity=service_identifier, staticFlowKey=static_flow_key,
                                        branding=branding)
            sid.qrTemplate = qr_template
            sid.shortUrl = su
            to_put.append(sid)
            result.append((sid, id_, user_code))
        for chunk in chunks(to_put, 200):
            db.put(chunk)
        return result

    return run_in_transaction(trans, xg=True)


@returns(NoneType)
@arguments(service_user=users.User, sid=(int, long))
def delete_qr(service_user, sid):
    sid = ServiceInteractionDef.get_by_id(sid, parent=parent_key(service_user))
    sid.deleted = True
    sid.put()


@returns(NoneType)
@arguments(app_user=users.User, service_identity_user=users.User, tag=unicode, context=unicode,
           message_flow_run_id=unicode, timestamp=(int, NoneType))
def poke_service_with_tag(app_user, service_identity_user, tag, context=None, message_flow_run_id=None,
                          timestamp=None):
    from rogerthat.bizz.service.mfr import _create_message_flow_run
    user_profile = get_user_profile(app_user)
    is_connected = (get_friend_serviceidentity_connection(app_user, service_identity_user) is not None)
    svc_user, identifier = get_service_identity_tuple(service_identity_user)
    human_user_email = get_human_user_from_app_user(app_user).email()
    if is_connected:
        from rogerthat.service.api.messaging import poke
        result_key = message_flow_run_id or str(uuid.uuid4())

        def trans():
            if message_flow_run_id:
                key_name = MessageFlowRunRecord.createKeyName(svc_user, message_flow_run_id)
                if not MessageFlowRunRecord.get_by_key_name(key_name):
                    _create_message_flow_run(svc_user, service_identity_user, message_flow_run_id, True, tag)

            poke_call = poke(poke_service_callback_response_receiver, logServiceError, get_service_profile(svc_user),
                             email=human_user_email, tag=tag, result_key=result_key, context=context,
                             service_identity=identifier, timestamp=timestamp or 0,
                             user_details=[UserDetailsTO.fromUserProfile(user_profile)],
                             DO_NOT_SAVE_RPCCALL_OBJECTS=True)
            if poke_call:  # None if poke callback is not implemented
                poke_call.message_flow_run_id = message_flow_run_id
                poke_call.result_key = result_key
                poke_call.member = app_user
                poke_call.context = context
                poke_call.put()

        xg_on = db.create_transaction_options(xg=True)
        db.run_in_transaction_options(xg_on, trans)
    else:
        language = user_profile.language or DEFAULT_LANGUAGE
        from rogerthat.bizz.friends import ORIGIN_USER_POKE

        def trans():
            if message_flow_run_id:
                key_name = MessageFlowRunRecord.createKeyName(svc_user, message_flow_run_id)
                if not MessageFlowRunRecord.get_by_key_name(key_name):
                    _create_message_flow_run(svc_user, service_identity_user, message_flow_run_id, True, tag)

            capi_call = invited(invited_response_receiver, logServiceError, get_service_profile(svc_user),
                                email=human_user_email, name=user_profile.name, message=None, tag=tag,
                                language=language, service_identity=identifier,
                                user_details=[UserDetailsTO.fromUserProfile(user_profile)],
                                origin=ORIGIN_USER_POKE, DO_NOT_SAVE_RPCCALL_OBJECTS=True)
            if capi_call:  # None if friend.invited callback is not implemented ==> invited_response_receiver
                capi_call.invitor = app_user
                capi_call.invitee = service_identity_user
                capi_call.servicetag = tag
                capi_call.poke = True
                capi_call.message_flow_run_id = message_flow_run_id
                capi_call.origin = ORIGIN_USER_POKE
                capi_call.context = context
                capi_call.put()
            else:
                deferred.defer(process_invited_response, svc_user, service_identity_user, identifier, app_user,
                               service_identity_user, tag, ORIGIN_USER_POKE, True, context, message_flow_run_id,
                               _transactional=True)

        xg_on = db.create_transaction_options(xg=True)
        db.run_in_transaction_options(xg_on, trans)

    slog('T', app_user.email(), "com.mobicage.api.services.startAction", service=service_identity_user.email(), tag=tag,
         context=context)


@returns(NoneType)
@arguments(user=users.User, service_identity_user=users.User, sid=unicode, context=unicode, message_flow_run_id=unicode,
           timestamp=(int, NoneType))
def poke_service(user, service_identity_user, sid, context=None, message_flow_run_id=None, timestamp=None):
    service_identity = get_service_identity(service_identity_user)
    azzert(service_identity)
    if sid:
        if "?" in sid:
            sid = sid[:sid.index("?")]  # strip off the query parameters added by shortner.py
        sid = get_service_interaction_def(service_identity.service_user, int(sid))
        azzert(sid)
    tag = sid.tag if sid else None

    poke_service_with_tag(user, service_identity_user, tag, context, message_flow_run_id, timestamp)


@returns(NoneType)
@arguments(user=users.User, service_identity_user=users.User, hashed_tag=unicode, context=unicode,
           timestamp=(int, NoneType))
def poke_service_by_hashed_tag(user, service_identity_user, hashed_tag, context=None, timestamp=None):
    service_identity = get_service_identity(service_identity_user)
    azzert(service_identity)
    mapped_poke = PokeTagMap.get_by_key_name(hashed_tag, parent=parent_key(service_identity.service_user))
    poke_service_with_tag(user, service_identity_user, mapped_poke.tag if mapped_poke else hashed_tag, context,
                          timestamp=timestamp)


@returns(unicode)
@arguments(app_user=users.User, link=unicode)
def get_user_link(app_user, link):
    uid = uuid.uuid4().hex
    uc = UserContext(key=UserContext.create_key(uid),
                     app_user=app_user)
    uc.put()

    parsed_url = urlparse.urlparse(link)
    query_params = urlparse.parse_qs(parsed_url.query)
    query_params['ocaContext'] = [uid]
    query_pairs = [(k, v) for k, vlist in query_params.iteritems() for v in vlist]
    return urlparse.urlunparse((parsed_url.scheme,
                                parsed_url.netloc,
                                parsed_url.path,
                                parsed_url.params,
                                urllib.urlencode(query_pairs),
                                parsed_url.fragment))


@returns(NoneType)
@arguments(user=users.User, service_identity_user=users.User, coords=[int], context=unicode, menuGeneration=int,
           message_flow_run_id=unicode, hashed_tag=unicode, timestamp=(int, NoneType))
def press_menu_item(user, service_identity_user, coords, context, menuGeneration, message_flow_run_id=None,
                    hashed_tag=None, timestamp=None):
    service_identity = get_service_identity(service_identity_user)
    if service_identity.menuGeneration == menuGeneration:
        smd = get_service_menu_item_by_coordinates(service_identity_user, coords)
        if smd:
            from rogerthat.bizz.service.mfr import start_flow
            if smd.staticFlowKey and not message_flow_run_id:
                logging.info("User did not start static flow. Starting flow now.")
                message_flow_run_id = str(uuid.uuid4())
                start_flow(service_identity_user, None, smd.staticFlowKey, [user], False, True, smd.tag, context,
                           key=message_flow_run_id)
            elif not smd.staticFlowKey and not message_flow_run_id and smd.isBroadcastSettings:
                from rogerthat.bizz.service.broadcast import generate_broadcast_settings_flow_def
                from rogerthat.bizz.service.mfd import to_xml_unicode
                helper = FriendHelper.from_data_store(service_identity_user, FRIEND_TYPE_SERVICE)
                mfds = generate_broadcast_settings_flow_def(helper, get_user_profile(user))
                azzert(mfds, "Expected broadcast settings.")
                mfd = MessageFlowDesign()
                mfd.xml = to_xml_unicode(mfds, 'messageFlowDefinitionSet', True)
                start_flow(service_identity_user, None, mfd, [user], False, True, smd.tag, context,
                           key=message_flow_run_id, allow_reserved_tag=True)

            if (smd.form_id and not mobile_supports_feature(users.get_current_mobile(), Features.FORMS)) or \
                    (smd.embeddedApp and not mobile_supports_feature(users.get_current_mobile(), Features.EMBEDDED_APPS_IN_SMI)):
                # For clients that do not support this yet send a message telling them to update.
                user_profile = get_user_profile(user)
                update_app_msg = localize(user_profile.language, 'update_app_to_use_feat')
                branding = service_identity.descriptionBranding
                member = UserMemberTO(user)
                sendMessage(service_identity_user, [member], Message.FLAG_ALLOW_DISMISS, 0, None, update_app_msg, [],
                            None, branding, smd.tag, 0, context)
                return
            else:
                poke_service_with_tag(user, service_identity_user, smd.tag, context, message_flow_run_id, timestamp)
            from rogerthat.bizz import log_analysis
            slog(msg_="Press menu item", function_=log_analysis.SERVICE_STATS, service=service_identity_user.email(),
                 tag=smd.label, type_=log_analysis.SERVICE_STATS_TYPE_MIP)

        elif coords == [3, 0, 0]:  # coordinates of share
            pass
        else:
            logging.error("Generation match (%s == %s), but service menu icon %s not found."
                          % (menuGeneration, service_identity.menuGeneration, coords))

    elif message_flow_run_id and hashed_tag:
        logging.info("User started a static flow, but his menu was out of date")
        mapped_tag = ServiceMenuDefTagMap.get_by_key_name(hashed_tag, parent=parent_key(service_identity.service_user))
        if mapped_tag:
            poke_service_with_tag(user, service_identity_user, mapped_tag.tag, context, message_flow_run_id, timestamp)
        else:
            logging.error("Generation mismatch (%s != %s) and mapped tag %s not found."
                          % (menuGeneration, service_identity.menuGeneration, hashed_tag))

    else:
        deferred.defer(_warn_user_menu_outdated, service_identity_user, user, _transactional=db.is_in_transaction())


@arguments(context=ServiceAPICallback, result=object)
def handle_fast_callback(context, result):
    capi_call = context

    if result:
        sender_service_identity_user = capi_call.service_identity_user

        error = None
        try:
            if isinstance(result.value, FlowCallbackResultTypeTO):
                type_ = FlowCallbackResultTypeTO
                from rogerthat.bizz.service.mfr import MessageFlowNotFoundException, MessageFlowNotValidException, \
                    start_local_flow
                if result.value.flow.startswith(u'<?xml'):
                    xml = result.value.flow
                else:
                    mfd = get_message_flow_by_key_or_name(capi_call.service_user, result.value.flow)
                    if not mfd or not mfd.user == capi_call.service_user:
                        raise MessageFlowNotFoundException()

                    if mfd.status != MessageFlowDesign.STATUS_VALID:
                        raise MessageFlowNotValidException(mfd.validation_error)
                    xml = mfd.xml

                start_local_flow(sender_service_identity_user,
                                 getattr(capi_call, 'parent_message_key', None),
                                 xml,
                                 [capi_call.member],
                                 context=getattr(capi_call, 'context', None),
                                 parent_message_key=getattr(capi_call, 'parent_message_key', None),
                                 tag=MISSING.default(result.value.tag, None),
                                 force_language=MISSING.default(result.value.force_language, None),
                                 flow_params=MISSING.default(result.value.flow_params, None))

            elif isinstance(result.value, MessageCallbackResultTypeTO):
                type_ = MessageCallbackResultTypeTO
                parent_message_key = getattr(capi_call, 'parent_message_key', None)
                if not parent_message_key:
                    members = [UserMemberTO(capi_call.member, result.value.alert_flags)]
                else:
                    message_object = get_message(parent_message_key, None)
                    members = [UserMemberTO(member, result.value.alert_flags) for member in message_object.members]
                sendMessage(sender_service_identity_user, members,
                            result.value.flags, 0, parent_message_key, result.value.message,
                            result.value.answers, None, result.value.branding, result.value.tag,
                            result.value.dismiss_button_ui_flags, getattr(capi_call, 'context', None),
                            attachments=result.value.attachments,
                            key=capi_call.result_key, is_mfr=capi_call.targetMFR,
                            step_id=MISSING.default(result.value.step_id, None))

            elif isinstance(result.value, FormCallbackResultTypeTO):
                type_ = FormCallbackResultTypeTO
                sendForm(sender_service_identity_user, getattr(capi_call, 'parent_message_key', None), capi_call.member,
                         result.value.message, result.value.form, result.value.flags, result.value.branding,
                         result.value.tag, result.value.alert_flags, getattr(capi_call, 'context', None),
                         attachments=result.value.attachments,
                         key=capi_call.result_key, is_mfr=capi_call.targetMFR,
                         step_id=MISSING.default(result.value.step_id, None))

        except ServiceApiException, sae:
            if (sae.code >= ERROR_CODE_WARNING_THRESHOLD):
                logging.warning("Service api exception occurred", exc_info=1)
            else:
                logging.exception("Severe Service API Exception")
            error = {'code': sae.code, 'message': sae.message}
            error.update(sae.fields)
        except:
            server_settings = get_server_settings()
            erroruuid = str(uuid.uuid4())
            logging.exception("Unknown exception occurred: error id %s" % erroruuid)
            error = {'code': ERROR_CODE_UNKNOWN_ERROR,
                     'message': 'An unknown error occurred. Please contact %s and mention error id %s' % (
                         server_settings.supportEmail, erroruuid)}
        if error is not None:
            function = None
            request = json.dumps({'params': serialize_complex_value(result.value, type_, False, skip_missing=True)})
            response = json.dumps({'result': None, 'error': error})
            log_service_activity(capi_call.service_user, str(uuid.uuid4()), ServiceLog.TYPE_CALL,
                                 ServiceLog.STATUS_ERROR, function, request, response, error['code'], error['message'])


@mapping(u'message.poke.response_handler')
@returns(NoneType)
@arguments(context=ServiceAPICallback, result=PokeCallbackResultTO)
def poke_service_callback_response_receiver(context, result):
    if not getattr(context, "message_flow_run_id", None):
        handle_fast_callback(context, result)


@returns()
@arguments(service_user=users.User, enable_on_success=bool, callback_name=unicode)
def perform_test_callback(service_user, enable_on_success=False, callback_name=None):
    logging.info("Preparing service object by setting the test-value ...")

    def trans():
        profile = get_service_profile(service_user, cached=False)
        profile.testValue = unicode(uuid.uuid4())
        profile.put()
        return profile

    profile = db.run_in_transaction(trans)

    logging.info("Scheduling test-callback ...")
    context = test(test_callback_response_receiver, logServiceError, profile, value=profile.testValue,
                   callback_name=callback_name)
    context.enable_on_success = enable_on_success
    context.callback_name = callback_name
    context.put()


@mapping(u'test_api_callback_response_handler')
@returns(NoneType)
@arguments(context=ServiceAPICallback, result=unicode)
def test_callback_response_receiver(context, result):
    profile = get_service_profile(context.service_user)

    if profile.testValue != result:
        raise TestCallbackFailedException()

    azzert(profile.testValue == result)
    if not context.callback_name:
        profile.testCallNeeded = False
        if hasattr(context, 'enable_on_success') and context.enable_on_success:
            profile.enabled = True
        profile.put()

    channel.send_message(context.service_user, u'rogerthat.service.testCallSucceeded',
                         callback_name=context.callback_name)


@returns(bool)
@arguments(service=users.User, admin=users.User)
def invite_service_admin(service, admin):
    service_identity, admin_user_profile = get_profile_infos([service, admin],
                                                             expected_types=[ServiceIdentity, UserProfile],
                                                             allow_none_in_results=True)
    if not admin_user_profile:
        return False

    m = """Hi %s,
service %s wants to add you as an administrator.
""" % (admin_user_profile.name, service_identity.name)
    message = sendMessage(MC_DASHBOARD, [UserMemberTO(admin)], Message.FLAG_AUTO_LOCK, 0, None, m,
                          create_accept_decline_buttons(admin_user_profile.language), None,
                          get_app_by_user(admin).core_branding_hash, INVITE_SERVICE_ADMIN, is_mfr=False)
    message.service = service
    message.admin = admin
    message.put()
    return True


def _get_custom_icon_library(user):
    if user:
        custom_icons_filename = user.email().encode('utf-8').replace('@', '.')
        custom_icons_path = os.path.join(CURRENT_DIR, "%s.zip" % custom_icons_filename)
        if os.path.exists(custom_icons_path):
            return (custom_icons_path, unicode(custom_icons_filename + '-'))
    return None


@returns([LibraryMenuIconTO])
@arguments(user=users.User)
def list_icon_library(user=None):
    icon_libraries = []  # list with tuples: (<path to ZIP>, <icon name prefix>)
    custom_library = _get_custom_icon_library(user)
    if custom_library:
        icon_libraries.insert(0, custom_library)

    result = list()

    for lib, prefix in icon_libraries:
        zipf = ZipFile(lib)
        try:
            for file_name in zipf.namelist():
                if os.path.dirname(file_name) == '50':
                    smi = LibraryMenuIconTO()
                    smi.name = unicode(os.path.splitext(os.path.basename(file_name))[0])
                    if not smi.name:  # file_name is the directory
                        continue
                    smi.name = prefix + smi.name
                    smi.label = smi.name
                    result.append(smi)
        finally:
            zipf.close()

    for icon in FA_ICONS:
        name = icon.replace(u'fa-', u'').replace(u'-', u' ')
        iconTO = LibraryMenuIconTO()
        iconTO.name = icon
        iconTO.label = name
        result.append(iconTO)
    return sorted(result, key=lambda k: k.label)


@cached(2, lifetime=0, request=True, memcache=False, datastore="icon-from-library")
@returns(str)
@arguments(name=unicode, size=int)
def get_icon_from_library(name, size=512):
    if '-' in name:
        custom_libs = [f for f in os.listdir(CURRENT_DIR) if f != 'icons.zip' and f.endswith('.zip')]
        for custom_lib_file in custom_libs:
            custom_lib_name = os.path.splitext(custom_lib_file)[0]  # removing the .zip extension
            if name.startswith(custom_lib_name):
                icon_filename = name.split('-', 1)[1]
                zipf = ZipFile(os.path.join(CURRENT_DIR, custom_lib_file))
                try:
                    return zipf.read("%s/%s.png" % (size, icon_filename))
                except KeyError:
                    logging.exception("Did not found icon '%s'. Falling back to default library." % name)
                finally:
                    zipf.close()

    zipf = ZipFile(ICON_LIBRARY_PATH)
    try:
        return zipf.read("%s/%s.png" % (size, name))
    except KeyError:
        return zipf.read("%s/%s.png" % (size, "anonymous"))  # show question mark for custom icons
    finally:
        zipf.close()


def _validate_coordinates(coords):
    if not coords or len(coords) != 3:
        raise InvalidMenuItemCoordinatesException()
    if not (-1 < coords[0] < 4):
        raise InvalidMenuItemCoordinatesException()
    if not (-1 < coords[1] < 4):
        raise InvalidMenuItemCoordinatesException()
    if coords[2] < 0:
        raise InvalidMenuItemCoordinatesException()
    if coords[2] == 0 and coords[1] == 0:
        raise ReservedMenuItemException()


def _validate_roles(service_user, role_ids):
    for role_id, role in zip(role_ids, get_service_roles_by_ids(service_user, role_ids)):
        if not role:
            raise RoleNotFoundException(role_id)


@returns(NoneType)
@arguments(service_user=users.User, icon_name=unicode, icon_color=unicode, label=unicode, tag=unicode, coords=[int],
           screen_branding=unicode, static_flow_name=unicode, requires_wifi=bool, run_in_background=bool,
           roles=[(int, long)], is_broadcast_settings=bool, broadcast_branding=unicode, action=int,
           link=ServiceMenuItemLinkTO, fall_through=bool, form_id=(int, long, NoneType), embedded_app=unicode)
def create_menu_item(service_user, icon_name, icon_color, label, tag, coords, screen_branding=None,
                     static_flow_name=None, requires_wifi=False, run_in_background=False, roles=None,
                     is_broadcast_settings=False, broadcast_branding=None, action=0, link=None, fall_through=False,
                     form_id=None, embedded_app=None):
    _validate_coordinates(coords)
    if roles is None:
        roles = []
    else:
        _validate_roles(service_user, roles)
    if not icon_name:
        raise InvalidValueException(u"icon_name", u"Icon name required")
    if not label:
        raise InvalidValueException("label", u"Label required")
    azzert(service_user)

    if is_broadcast_settings:
        tag = ServiceMenuDef.TAG_MC_BROADCAST_SETTINGS
        channel.send_message(service_user, u'rogerthat.broadcast.changes')
    elif not tag:
        raise InvalidValueException("tag", u"Tag required")
    elif tag.startswith(MC_RESERVED_TAG_PREFIX):
        raise ReservedTagException()

    try:
        png_bytes = get_icon_from_library(icon_name)
    except:
        logging.exception("Failed to get icon '%s' from library.", icon_name)
        raise InvalidValueException("icon_name", u"Icon not found")

    if icon_color:
        if icon_color.startswith('#'):
            icon_color = icon_color[1:]
        try:
            color = parse_color(icon_color)
        except:
            raise InvalidValueException("icon_color", u"Invalid color")
        else:
            png_bytes = recolor_png(png_bytes, (0, 0, 0), color)
            icon_blob = db.Blob(png_bytes)
            icon_hash = md5_hex(png_bytes)
    else:
        icon_color = icon_blob = icon_hash = None

    static_flow_key = str(
        get_service_message_flow_design_key_by_name(service_user, static_flow_name)) if static_flow_name else None

    web_page = link and link.url.strip()
    if web_page:
        if ':' not in web_page:
            web_page = 'http://' + web_page
        elif '://' not in web_page:
            # Eg. if tel:xxx is used, we convert it to tel://xxx because the clients only support this kind of notation
            web_page = web_page.replace(':', '://', 1)
    external_web_page = bool(web_page) and (
        ServiceMenuItemLinkTO.external.default if link.external is MISSING else link.external)  # @UndefinedVariable
    request_user_link = bool(web_page) and (
        ServiceMenuItemLinkTO.request_user_link.default if link.request_user_link is MISSING else link.request_user_link)  # @UndefinedVariable

    if form_id:
        form = get_form(form_id, service_user)
    if embedded_app:
        try:
            # Check if exists
            get_embedded_application(embedded_app)
        except EmbeddedApplicationNotFoundException:
            raise InvalidValueException('embedded_app', u'Embedded app with id "%s" not found' % embedded_app)

    def trans(screen_branding):
        if web_page and not screen_branding:
            old_smd = get_service_menu_item_by_coordinates(service_user, coords)
            if not old_smd or old_smd.link != web_page or not old_smd.screenBranding:
                screen_branding = _create_branding_for_link(service_user, link, coords, label)

        smd = ServiceMenuDef(key=ServiceMenuDef.createKey(coords, service_user), label=label,
                             tag=tag, timestamp=now(), icon=icon_blob, iconHash=icon_hash,
                             iconName=icon_name, iconColor=icon_color, screenBranding=screen_branding,
                             staticFlowKey=static_flow_key, isBroadcastSettings=is_broadcast_settings,
                             requiresWifi=requires_wifi, runInBackground=run_in_background, roles=roles, action=action,
                             link=web_page, isExternalLink=external_web_page, requestUserLink=request_user_link,
                             fallThrough=fall_through, embeddedApp=embedded_app)
        if form_id:
            smd.form_id = form.id
            smd.form_version = form.version

        mapped_tag = ServiceMenuDefTagMap(key_name=smd.hashed_tag, parent=parent_key(service_user),
                                          timestamp=smd.timestamp, tag=smd.tag)
        to_put = [smd, mapped_tag]

        if is_broadcast_settings:
            service_profile = get_service_profile(service_user)
            bizz_check(service_profile.broadcastTypes,
                       u"You can not create a broadcast settings menu item if there are no broadcast types. You can add new broadcast types at Broadcast center.")
            if broadcast_branding != service_profile.broadcastBranding:
                service_profile.broadcastBranding = broadcast_branding
                service_profile.addFlag(ServiceProfile.FLAG_CLEAR_BROADCAST_SETTINGS_CACHE)
                to_put.append(service_profile)

        put_and_invalidate_cache(*to_put)

        bump_menuGeneration_of_all_identities_and_update_friends(service_user)

    run_in_xg_transaction(trans, screen_branding)


def _create_branding_for_link(service_user, link, coords, label):
    '''Create a branding as backwards compatible solution for service menu items with a link'''
    from rogerthat.bizz.branding import store_branding_zip
    text = localize(get_service_profile(service_user).defaultLanguage, u'open_link', link=label)
    with closing(StringIO()) as stream:
        with ZipFile(stream, 'w') as zip_file:
            html = u'''<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        <meta property="rt:external-url" content="%s"/>
    </head>
    <body style="width: 100%%; height: 100%%;">
        <div style="width: 100%%; height: 100%%; overflow: auto; display: table;">
            <a style="display: table-cell; vertical-align: middle; text-align: center;" href="%s">%s</a>
        </div>
    </body>
</html>''' % (link.url, link.url, text)
            zip_file.writestr('app.html', html.encode('utf-8'))
            branding = store_branding_zip(service_user, zip_file,
                                          u'Backwards compatible branding for menu item %s with a link' % coords)
            branding.timestamp = -branding.timestamp  # logically deleted
            branding.put()
    return branding.hash


@returns(NoneType)
@arguments(service_user=users.User, source_coords=[int], target_coords=[int])
def move_menu_item(service_user, source_coords, target_coords):
    _validate_coordinates(source_coords)
    _validate_coordinates(target_coords)

    def trans():
        smd = get_service_menu_item_by_coordinates(service_user, source_coords)

        new_smd = ServiceMenuDef(key=ServiceMenuDef.createKey(target_coords, service_user))
        for prop in (p for p in ServiceMenuDef.properties().iterkeys() if p != '_class'):
            setattr(new_smd, prop, getattr(smd, prop))
        new_smd.put()

        smd.delete()
        bump_menuGeneration_of_all_identities_and_update_friends(service_user)

    db.run_in_transaction(trans)


@returns(NoneType)
@arguments(service_user=users.User, column=int, label=unicode)
def set_reserved_item_caption(service_user, column, label):
    if column < 0 or column > 3:
        raise InvalidMenuItemCoordinatesException()

    def trans():
        service_profile = get_service_profile(service_user)
        logging.info("Updating %s's %s to %s" % (service_user.email(), MENU_ITEM_LABEL_ATTRS[column], label))
        setattr(service_profile, MENU_ITEM_LABEL_ATTRS[column], label)
        service_profile.version += 1
        service_profile.put()
        schedule_update_all_friends_of_service_user(service_profile)

    db.run_in_transaction(trans)


@returns(bool)
@arguments(service_user=users.User, coords=[int])
def delete_menu_item(service_user, coords):
    _validate_coordinates(coords)

    def trans():
        smi = get_service_menu_item_by_coordinates(service_user, coords)
        if smi:
            smi.delete()
            bump_menuGeneration_of_all_identities_and_update_friends(service_user)
        return smi

    smi = run_in_transaction(trans)
    if smi and smi.isBroadcastSettings:
        channel.send_message(service_user, u'rogerthat.broadcast.changes')

    return bool(smi)


@returns(NoneType)
@arguments(service_user=users.User)
def bump_menuGeneration_of_all_identities_and_update_friends(service_user):
    service_identities = list(get_service_identities(service_user))
    for service_identity in service_identities:
        service_identity.menuGeneration += 1
        service_identity.version += 1

        logging.debug('debugging_branding bump_menuGeneration_of_all_identities_and_update_friends %s service_identity.menuGeneration %s service_identity.version %s',
                      service_identity.identifier, service_identity.menuGeneration, service_identity.version)

    put_and_invalidate_cache(*service_identities)
    if db.is_in_transaction():
        service_profile_or_user = get_service_profile(service_user)
    else:
        service_profile_or_user = service_user
    schedule_update_all_friends_of_service_user(service_profile_or_user)


@returns(ServiceMenuDetailTO)
@arguments(service_user=users.User)
def get_menu(service_user):
    service_identity_user = create_service_identity_user(service_user)
    helper = FriendHelper.from_data_store(service_identity_user, FRIEND_TYPE_SERVICE)
    return ServiceMenuDetailTO.from_model(helper, False)


@returns(unicode)
@arguments(helper=FriendHelper, user_profile=UserProfile)
def calculate_icon_color_from_branding(helper, user_profile):
    # type: (FriendHelper, UserProfile) -> unicode
    icon_color = None
    si = helper.get_profile_info()
    if si.menuBranding:
        branding_hash = si.menuBranding
        if user_profile:
            translator = helper.get_translator()
            branding_hash = translator.translate(ServiceTranslation.HOME_BRANDING, branding_hash, user_profile.language)
        branding = helper.get_branding(branding_hash)
        icon_color = branding.menu_item_color
    if not icon_color:
        icon_color = Branding.DEFAULT_MENU_ITEM_COLORS[Branding.DEFAULT_COLOR_SCHEME]
    return icon_color


@returns(tuple)
@arguments(smd=ServiceMenuDef, service_identity_user=users.User, target_user=users.User)
def get_menu_icon(smd, service_identity_user, target_user=None):
    if smd.icon:
        return str(smd.icon), smd.iconHash

    user_profile = get_user_profile(target_user) if target_user else None
    helper = FriendHelper.from_data_store(service_identity_user, FRIEND_TYPE_SERVICE)
    icon_color = calculate_icon_color_from_branding(helper, user_profile)

    icon = _render_dynamic_menu_icon_cached(smd.iconName, icon_color)
    icon_hash = get_menu_icon_hash(smd.iconName, icon_color)
    return icon, icon_hash


@db.non_transactional()
@cached(2, 0, datastore="dynamic_menu_icon")
@returns(str)
@arguments(icon_name=unicode, icon_color=unicode)
def _render_dynamic_menu_icon_cached(icon_name, icon_color):
    color = parse_color(icon_color)
    png_bytes = get_icon_from_library(icon_name)
    png_bytes = recolor_png(png_bytes, (0, 0, 0), color)
    return png_bytes


@returns(unicode)
@arguments(icon_name=str, icon_color=unicode)
def get_menu_icon_hash(icon_name, icon_color):
    return unicode(md5_hex(icon_name + ';' + icon_color))


@db.non_transactional()
@cached(1, 0, datastore="menu_icon")
@returns(str)
@arguments(icon=str, size=int)
def render_menu_icon(icon, size):
    return images.resize(icon, size, size)


@returns(NoneType)
@arguments(email=unicode, svc_index=search.Index, loc_index=search.Index)
def _cleanup_search_index(email, svc_index, loc_index):
    svc_index.delete([email])
    cursor = search.Cursor()
    while True:
        query = search.Query(query_string='service:"%s"' % email, options=search.QueryOptions(cursor=cursor, limit=10))
        search_result = loc_index.search(query)
        loc_index.delete([r.doc_id for r in search_result.results])
        if search_result.number_found != 10:
            break
        cursor = search_result.cursor


@returns(NoneType)
@arguments(service_identity_user=users.User)
def remove_service_identity_from_index(service_identity_user):
    svc_index = search.Index(name=SERVICE_INDEX)
    loc_index = search.Index(name=SERVICE_LOCATION_INDEX)

    email = service_identity_user.email()

    _cleanup_search_index(email, svc_index, loc_index)
    cleanup_map_index(service_identity_user)


def get_search_fields(service_user, service_identity_user, sc):
    from rogerthat.bizz.app import get_app
    service_identity = get_service_identity(service_identity_user)
    service_profile = get_service_profile(service_user)
    service_menu_item_labels = []
    service_menu_item_hashed_tags = []
    for item in ServiceMenuDef.list_with_action(service_user):
        service_menu_item_labels.append(item.label)
        service_menu_item_hashed_tags.append(item.hashed_tag)

    fields = [search.AtomField(name='service', value=service_identity_user.email()),
              search.TextField(name='qualified_identifier', value=service_identity.qualifiedIdentifier),
              search.TextField(name='name', value=service_identity.name.lower()),
              search.TextField(name='description', value=service_identity.description),
              search.TextField(name='keywords', value=sc.keywords),
              search.TextField(name='app_ids', value=" ".join(service_identity.appIds)),
              search.TextField(name='action_labels', value=' - '.join(service_menu_item_labels)),
              search.TextField(name='action_tags', value=' '.join(service_menu_item_hashed_tags)),
              search.NumberField(name='organization_type', value=service_profile.organizationType)
              ]

    translator = get_translator(service_user, [ServiceTranslation.IDENTITY_TEXT])
    for language in translator.non_default_supported_languages:
        language = convert_web_lang_to_iso_lang(language)
        name = 'qualified_identifier_%s' % language
        value = translator.translate(ServiceTranslation.IDENTITY_TEXT, service_identity.qualifiedIdentifier, language)
        fields.append(search.TextField(name=name, value=value))

        name = 'name_%s' % language
        value = translator.translate(ServiceTranslation.IDENTITY_TEXT, service_identity.name, language)
        fields.append(search.TextField(name=name, value=value.lower()))

        name = 'description_%s' % language
        value = translator.translate(ServiceTranslation.IDENTITY_TEXT, service_identity.description, language)
        fields.append(search.TextField(name=name, value=value))

    tags = set()
    default_app = get_app(service_identity.app_id)
    if default_app.demo:
        tags.add('environment#demo')
    else:
        tags.add('environment#production')

    for app_id in service_identity.appIds:
        if app_id in (App.APP_ID_ROGERTHAT, App.APP_ID_OSA_LOYALTY):
            continue
        if default_app.type == App.APP_TYPE_CITY_APP and app_id.startswith('be-'):
            tags.add('group#cityapps_belgium')
        tags.add('app_id#%s' % app_id)

    service_info = ServiceInfo.create_key(service_user, service_identity.identifier).get()
    if not service_info:
        logging.warn('skipping place_types in get_search_fields for service_user:%s identifier:%s', service_user, service_identity.identifier)
        return service_identity.name.lower(), list(tags), fields

    for place_type in service_info.place_types:
        tags.add('place_type#%s' % place_type)
        place_details = get_place_details(place_type, 'en')
        if not place_details:
            continue
        tags.add('place_type#%s' % place_type)

    return service_identity.name.lower(), list(tags), fields


def get_map_txt_from_fields(fields):
    txt = []
    for field in fields:
        if field.name in ('app_ids', 'action_labels', 'action_tags', 'organization_type',):
            continue
        if not field.value:
            continue
        if field.name in ('service', 'qualified_identifier', 'name', 'description', 'keywords',):
            txt.append(field.value)
        elif field.name.startswith('qualified_identifier_'):
            continue # txt.append(field.value)  # we don't have multi language services
        elif field.name.startswith('name_'):
            continue #  txt.append(field.value) # we don't have multi language services
        elif field.name.startswith('description_'):
            continue #  txt.append(field.value) # we don't have multi language services
        else:
            logging.warn('get_map_txt_from_fields got unknown field:%s', field.name)
    return txt


@returns([search.Document])
@arguments(service_identity_user=users.User)
def re_index(service_identity_user):
    service_user = get_service_user_from_service_identity_user(service_identity_user)
    azzert(not is_trial_service(service_user))

    svc_index = search.Index(name=SERVICE_INDEX)
    loc_index = search.Index(name=SERVICE_LOCATION_INDEX)

    # cleanup any previous index entry
    _cleanup_search_index(service_identity_user.email(), svc_index, loc_index)

    # re-add if necessary
    sc, locs = get_search_config(service_identity_user)
    if not sc.enabled:
        cleanup_map_index(service_identity_user)
        return []

    name, tags, fields = get_search_fields(service_user, service_identity_user, sc)

    svc_doc = search.Document(doc_id=service_identity_user.email(), fields=fields)
    svc_index.put(svc_doc)
    docs = [svc_doc]

    should_cleanup = True
    if locs:
        for loc in locs:
            loc_doc = search.Document(
                fields=fields + [
                    search.GeoField(name='location', value=search.GeoPoint(float(loc.lat) / GEO_POINT_FACTOR,
                                                                           float(loc.lon) / GEO_POINT_FACTOR))
                ])
            loc_index.put(loc_doc)
            docs.append(loc_doc)
        if save_map_service(service_identity_user):
            should_cleanup = False
            add_map_index(service_identity_user, locs, name, tags, get_map_txt_from_fields(fields))
    if should_cleanup:
        cleanup_map_index(service_identity_user)

    return docs


@returns()
@arguments(service_identity_user=users.User)
def re_index_map_only(service_identity_user):
    service_user = get_service_user_from_service_identity_user(service_identity_user)
    azzert(not is_trial_service(service_user))

    # re-add if necessary
    sc, locs = get_search_config(service_identity_user)
    if not sc.enabled:
        cleanup_map_index(service_identity_user)
        return

    should_cleanup = True
    if locs:
        name, tags, fields = get_search_fields(service_user, service_identity_user, sc)
        if save_map_service(service_identity_user):
            should_cleanup = False
            add_map_index(service_identity_user, locs, name, tags, get_map_txt_from_fields(fields))
    if should_cleanup:
        cleanup_map_index(service_identity_user)


@returns(FindServiceResponseTO)
@arguments(app_user=users.User, search_string=unicode, geo_point=GeoPointWithTimestampTO, organization_type=int,
           cursor_string=unicode, avatar_size=int, hashed_tag=unicode)
def find_service(app_user, search_string, geo_point, organization_type, cursor_string=None,
                 avatar_size=50, hashed_tag=None):

    def get_name_sort_options():
        sort_expr = search.SortExpression(expression='name', direction=search.SortExpression.ASCENDING)
        return search.SortOptions(expressions=[sort_expr])

    def get_location_sort_options(lat, lon):
        loc_expr = "distance(location, geopoint(%f, %f))" % (lat, lon)
        sort_expr = search.SortExpression(expression=loc_expr,
                                          direction=search.SortExpression.ASCENDING,
                                          default_value=VERY_FAR)
        return search.SortOptions(expressions=[sort_expr])

    limit = 10  # limit per category (except 'My Services', this one has no limit)
    results = []
    results_cursor = None
    suggestions_nearby = []
    suggestions_nearby_cursor = None

    app_id = get_app_id_from_app_user(app_user)

    my_service_identities = dict()
    if not hashed_tag:
        my_profile_info = get_profile_info(app_user, skip_warning=True)
        if my_profile_info.owningServiceEmails:
            my_owning_service_identity_users = [create_service_identity_user(users.User(owning_service_email)) for
                                                owning_service_email in my_profile_info.owningServiceEmails]
            for si in get_service_identities_by_service_identity_users(my_owning_service_identity_users):
                my_service_identities[si.service_identity_user.email()] = si
        for si in get_service_identities_via_user_roles(app_user, app_id, organization_type):
            my_service_identities[si.service_identity_user.email()] = si

    # cursor_string format:
    #     1/ not used anymore
    #     2(;search_string)/<search-string-without-location cursor>  # ;search_string is optional
    #     3(;lat;lon)/<search-nearby cursor>                         # ;lat;lon is optional

    if geo_point:
        lat, lon = geo_point.latitude_degrees, geo_point.longitude_degrees
    else:
        lat, lon = None, None

    if cursor_string:
        cursor_type, cursor_web_safe_string = cursor_string.split('/', 1)
        if cursor_type.startswith('2;'):  # search_string included in cursor
            cursor_type, search_string = cursor_type.split(';', 1)
            search_string = base64.b64decode(search_string).decode('utf-8')
        elif cursor_type.startswith('3;'):  # lat,lon included in cursor
            cursor_type, lat, lon = cursor_type.split(';', 2)
            lat, lon = float(lat), float(lon)
    else:
        cursor_type = cursor_web_safe_string = None

    if geo_point and (cursor_type in (None, '3')):
        the_index = search.Index(name=SERVICE_LOCATION_INDEX)
        # Query generic (not on search_string) for nearby services
        try:
            query_string = u"app_ids:%s" % app_id
            if organization_type != ServiceProfile.ORGANIZATION_TYPE_UNSPECIFIED:
                query_string += u" organization_type:%s" % organization_type
            if hashed_tag:
                query_string += u" action_tags:%s" % hashed_tag

            query = search.Query(query_string=query_string,
                                 options=search.QueryOptions(returned_fields=['service', 'action_labels', 'location'],
                                                             sort_options=get_location_sort_options(lat, lon),
                                                             limit=limit,
                                                             cursor=search.Cursor(cursor_web_safe_string,
                                                                                  per_result=True)))
            search_result = the_index.search(query)
            if search_result.results:
                suggestions_nearby.extend(search_result.results)
                suggestions_nearby_cursor = '3;%s;%s/%s' % (lat, lon, search_result.results[-1].cursor.web_safe_string)
            else:
                suggestions_nearby_cursor = None
        except:
            logging.error('Search query error', exc_info=True)

    # Search results
    if cursor_type in (None, '2'):
        the_index = search.Index(name=SERVICE_INDEX)
        try:
            query_string = u"%s app_ids:%s" % (normalize_search_string(search_string), app_id)
            if organization_type != ServiceProfile.ORGANIZATION_TYPE_UNSPECIFIED:
                query_string += u" organization_type:%s" % organization_type
            if hashed_tag:
                query_string += u" action_tags:%s" % hashed_tag

            query = search.Query(query_string=query_string,
                                 options=search.QueryOptions(returned_fields=['service', 'action_labels'],
                                                             sort_options=get_name_sort_options(),
                                                             limit=limit - len(results),
                                                             cursor=search.Cursor(cursor_web_safe_string,
                                                                                  per_result=True)))
            search_result = the_index.search(query)
            if search_result.results:
                results.extend(search_result.results)
                results_cursor = '2;%s/%s' % (base64.b64encode(search_string.encode('utf-8')),
                                              search_result.results[-1].cursor.web_safe_string)
            else:
                results_cursor = None
        except:
            logging.error('Search query error for search_string "%s"', search_string, exc_info=True)

    # Make dict of distances of results
    service_identity_closest_distances = dict()
    if geo_point:
        for result in suggestions_nearby + results:
            svc_identity_email = result.fields[0].value
            degrees = list()
            if len(result.fields) < 3:
                # No location found for this result
                if svc_identity_email not in service_identity_closest_distances:
                    for search_location in get_search_locations(users.User(svc_identity_email)):
                        degrees.append((float(search_location.lat) / GEO_POINT_FACTOR,
                                        float(search_location.lon) / GEO_POINT_FACTOR))
            else:
                degrees.append((result.fields[2].value.latitude, result.fields[2].value.longitude))

            for svc_latitude, svc_longitude in degrees:
                distance = haversine(lon, lat, svc_longitude, svc_latitude)
                service_identity_closest_distances[svc_identity_email] = \
                    min(distance, service_identity_closest_distances.get(svc_identity_email, VERY_FAR))

    def get_email_addresses_no_dups(results, service_identity_action_labels):
        # Can have lots of duplicates due to
        # 1. identities with multiple locations
        # 2. identities which are found both in location index and regular index
        service_identity_emails_dups = [result.fields[0].value for result in results]
        service_action_labels = [result.fields[1].value for result in results]
        service_identity_emails_no_dups = []
        for email, action_labels in zip(service_identity_emails_dups, service_action_labels):
            if email not in service_identity_emails_no_dups:
                service_identity_emails_no_dups.append(email)
                service_identity_action_labels[email] = action_labels
        return service_identity_emails_no_dups

    si_action_labels = dict()
    search_result_full_email_addresses = get_email_addresses_no_dups(results, si_action_labels)  # contains /+default+
    suggestions_nearby_full_email_addresses = get_email_addresses_no_dups(suggestions_nearby,
                                                                          si_action_labels)  # contains /+default+

    users_ = list()
    users_.extend(map(users.User, search_result_full_email_addresses))
    users_.extend(map(users.User, suggestions_nearby_full_email_addresses))
    users_.append(app_user)

    profile_infos = get_profile_infos(users_, allow_none_in_results=True)
    user_profile = profile_infos.pop(-1)
    profile_info_dict = {p.user.email(): p for p in profile_infos if p and p.isServiceIdentity}

    def create_FindServiceItemTO(email, show_distance=False):
        profile_info = profile_info_dict.get(email)
        if not profile_info:
            return None

        if show_distance:
            distance = int(service_identity_closest_distances.get(email, -1))
            actions = None
        else:
            distance = -1
            actions = si_action_labels.get(email)

        return FindServiceItemTO.fromServiceIdentity(profile_info, user_profile.language, distance, avatar_size,
                                                     actions)

    result = FindServiceResponseTO()
    result.matches = list()
    result.error_string = None

    if geo_point and cursor_type in (None, '3'):
        if suggestions_nearby_full_email_addresses or cursor_type:
            category_suggestions_nearby = FindServiceCategoryTO()
            category_suggestions_nearby.category = localize(user_profile.language, u"Nearby services")
            category_suggestions_nearby.items = filter(None, [create_FindServiceItemTO(email, True)
                                                              for email in suggestions_nearby_full_email_addresses])
            category_suggestions_nearby.cursor = suggestions_nearby_cursor
            result.matches.append(category_suggestions_nearby)

    # if cursor is not None, then don't add the "No matching services found" category
    if search_result_full_email_addresses or cursor_type in (None, '2'):
        category_search_results = FindServiceCategoryTO()
        category_search_results.cursor = results_cursor
        category_search_results.items = filter(None, map(create_FindServiceItemTO, search_result_full_email_addresses))
        if not category_search_results.items and cursor_type is None:
            if search_string and search_string.strip():
                category_search_results.category = localize(user_profile.language, u"No matching service found")
            else:
                category_search_results.category = localize(user_profile.language, u"No service found")
        elif search_string and search_string.strip():
            category_search_results.category = localize(user_profile.language, u"Search results")
        else:
            category_search_results.category = localize(user_profile.language, u"A-Z")

        if search_string and search_string.strip():
            result.matches.insert(0, category_search_results)
        else:
            result.matches.append(category_search_results)

    if not cursor_string and my_service_identities:
        # show all my services; do not filter away those to which I am already connected
        category_my_services = FindServiceCategoryTO()
        category_my_services.category = localize(user_profile.language, u"My services")
        smi_labels = [item.label for item in ServiceMenuDef.list_with_action(si.service_user)]
        if smi_labels:
            actions = u" - ".join(smi_labels)
        else:
            actions = None
        category_my_services.items = sorted([FindServiceItemTO.fromServiceIdentity(si, user_profile.language,
                                                                                   avatar_size=avatar_size,
                                                                                   actions=actions)
                                             for si in my_service_identities.values()],
                                            key=lambda item: item.name)
        category_my_services.cursor = None
        result.matches.append(category_my_services)

    return result


def _generate_api_key(name, service_user, prefix="ak"):
    key = generate_random_key()
    ak = APIKey(key_name=prefix + key)
    ak.user = service_user
    ak.timestamp = now()
    ak.name = name
    return ak


def _warn_user_menu_outdated(service_identity_user, app_user):
    service_identity, _ = get_profile_infos([service_identity_user, app_user],
                                            expected_types=[ServiceIdentity, UserProfile])

    def trans():
        bump_friend_map_generation = get_service_profile(service_identity.service_user).updatesPending
        friend_map = get_friends_map(app_user)
        to_put = []
        if bump_friend_map_generation:
            friend_map.generation += 1
            to_put.append(friend_map)
        logging.debug('debugging_branding _warn_user_menu_outdated friend_map.gen %s', friend_map.generation)
        helper = FriendHelper.from_data_store(service_identity_user, FRIEND_TYPE_SERVICE)
        to_put.extend(create_update_friend_requests(helper, service_identity_user, friend_map,
                                                    UpdateFriendRequestTO.STATUS_MODIFIED))
        db.put(to_put)

    run_in_transaction(trans, True)


@returns((NoneType, SendApiCallCallbackResultTO))
@arguments(app_user=users.User, service_identity_user=users.User, id_=int, method=unicode, params=unicode,
           hashed_tag=unicode, synchronous=bool)
def send_api_call(app_user, service_identity_user, id_, method, params, hashed_tag, synchronous):
    # type: (users.User, users.User, int, unicode, unicode, unicode, bool) -> Optional[SendApiCallCallbackResultTO]
    if synchronous:
        return _send_api_call(app_user, service_identity_user, id_, method, params, hashed_tag, synchronous)
    else:
        try_or_defer(_send_api_call, app_user, service_identity_user, id_, method, params, hashed_tag, synchronous)


@returns((NoneType, SendApiCallCallbackResultTO))
@arguments(app_user=users.User, service_identity_user=users.User, id_=int, method=unicode, params=unicode,
           hashed_tag=unicode, synchronous=bool)
def _send_api_call(app_user, service_identity_user, id_, method, params, hashed_tag, synchronous):
    from rogerthat.service.api import system
    service_user, identifier = get_service_identity_tuple(service_identity_user)

    def trans():
        # TODO: bundle 2 datastore.get calls into 1 datastore.get call (only when moved to ndb to use cache)
        service_profile = get_service_profile(service_user)
        azzert(service_profile)
        to_get = [FriendServiceIdentityConnection.createKey(app_user, service_identity_user)]
        if hashed_tag:
            to_get.append(ServiceMenuDefTagMap.create_key(hashed_tag, service_user))
        models = db.get(to_get)
        if hashed_tag:
            mapped_tag = models.pop()
            azzert(mapped_tag)
            tag = mapped_tag.tag
        else:
            tag = None
        fsic = models.pop()

        bizz_check(fsic, 'Can not send api call to %s (there\'s no friend-service connection)' % service_identity_user.email())

        context_or_result = system.api_call(send_api_call_response_receiver, logServiceError, service_profile,
                                            email=get_human_user_from_app_user(app_user).email(),
                                            method=method,
                                            params=params,
                                            tag=tag,
                                            service_identity=identifier,
                                            user_details=[UserDetailsTO.fromUserProfile(get_user_profile(app_user))],
                                            PERFORM_CALLBACK_SYNCHRONOUS=synchronous,
                                            DO_NOT_SAVE_RPCCALL_OBJECTS=True)
        if synchronous:
            return context_or_result
        else:
            context = context_or_result
            if context:
                assert isinstance(context, ServiceAPICallback)
                context.human_user = app_user
                context.id = id_
                context.put()
            else:
                _send_api_call_result_request(app_user, id_, None, None)

    xg_on = db.create_transaction_options(xg=True)
    # Since deeper in the stack submit_service_api_callback has a @run_after_transaction decorator,
    # we cannot run this in a transaction here (when synchronous is True) because that decorator
    # makes the function sort off async, which means it will always return None.
    # On the other hand, no transaction means it will run faster so that's nice.
    return trans() if synchronous else db.run_in_transaction_options(xg_on, trans)


@mapping(u'system.api_call.response_handler')
@returns(NoneType)
@arguments(context=ServiceAPICallback, result=SendApiCallCallbackResultTO)
def send_api_call_response_receiver(context, result):
    try_or_defer(received_api_call_result, context.human_user, context.service_identity_user, context.id,
                 result.result if result else None, result.error if result else None)


def _send_api_call_result_request(app_user, id_, result, error):
    request = ReceiveApiCallResultRequestTO()
    request.id = id_
    request.result = result
    request.error = error
    receiveApiCallResult(receive_api_call_result_response_handler, logError, app_user, request=request)


@returns(NoneType)
@arguments(app_user=users.User, service_identity_user=users.User, id_=int, result=unicode, error=unicode)
def received_api_call_result(app_user, service_identity_user, id_, result, error):

    def trans():
        if not get_friend_serviceidentity_connection(app_user, service_identity_user):
            raise FriendNotFoundException()

        _send_api_call_result_request(app_user, id_, result, error)

    xg_on = db.create_transaction_options(xg=True)
    db.run_in_transaction_options(xg_on, trans)


@mapping('com.mobicage.capi.services.receive_api_call_result_response_handler')
@returns(NoneType)
@arguments(context=RpcCAPICall, result=ReceiveApiCallResultResponseTO)
def receive_api_call_result_response_handler(context, result):
    pass


@mapping('com.mobicage.capi.services.update_user_data_response_handler')
@returns(NoneType)
@arguments(context=RpcCAPICall, result=UpdateUserDataResponseTO)
def update_user_data_response_handler(context, result):
    pass


@returns([RpcCAPICall])
@arguments(mobiles=[Mobile], target_user=users.User, helper=FriendHelper)
def create_send_app_data_requests(mobiles, target_user, helper):
    # type: (list[Mobile], users.User, FriendHelper) -> list[RpcCAPICall]
    service_identity = helper.get_profile_info()
    service_profile = helper.get_service_profile()
    service_data = helper.get_service_data()
    if service_data:
        app_data = service_data
    elif service_identity.appData:
        app_data = json.loads(service_identity.appData)
    else:
        app_data = {}
    app_data[BROADCAST_TYPES_SERVICE_DATA_KEY] = service_profile.broadcastTypes or []

    return _send_set_user_data(mobiles, target_user, helper.service_identity_user,
                               UpdateUserDataRequestTO.DATA_TYPE_APP, app_data, app_data.keys())


@returns([RpcCAPICall])
@arguments(mobiles=[Mobile], user_data_model=UserData, fsic=FriendServiceIdentityConnection, target_user=users.User,
           service_identity_user=users.User)
def create_send_user_data_requests(mobiles, user_data_model, fsic, target_user, service_identity_user):
    if user_data_model:
        if user_data_model.userData:
            user_data = user_data_model.userData.to_json_dict()
        else:
            user_data = json.loads(user_data_model.data)
    else:
        user_data = {}
    disabled_broadcast_types = fsic.disabled_broadcast_types if fsic else []
    user_data[DISABLED_BROADCAST_TYPES_USER_DATA_KEY] = disabled_broadcast_types
    return _send_set_user_data(mobiles, target_user, service_identity_user,
                               UpdateUserDataRequestTO.DATA_TYPE_USER, user_data, user_data.keys())


@returns([RpcCAPICall])
@arguments(mobiles=[Mobile], target_user=users.User, service_identity_user=users.User, full_json_dict=dict,
           updated_keys=[unicode])
def get_update_userdata_requests(mobiles, target_user, service_identity_user, full_json_dict, updated_keys):
    # type: (list[Mobile], users.User, users.User, dict, list[unicode], list[unicode]) -> list[RpcCAPICall]
    return _send_set_user_data(mobiles, target_user, service_identity_user, UpdateUserDataRequestTO.DATA_TYPE_USER,
                               full_json_dict, updated_keys)


@returns([RpcCAPICall])
@arguments(mobiles=[Mobile], target_user=users.User, service_identity_user=users.User, type_=unicode,
           full_json_dict=dict, updated_keys=[unicode])
def _send_set_user_data(mobiles, target_user, service_identity_user, type_, full_json_dict, updated_keys):
    # type: (list[Mobile], users.User, users.User, unicode, dict, list[unicode]) -> list[RpcCAPICall]
    updated_json_dict = {k: full_json_dict.get(k) for k in updated_keys}
    capi_calls = []
    for mobile in mobiles:
        service_email = remove_slash_default(service_identity_user).email()
        request = UpdateUserDataRequestTO()
        request.service = service_email if isinstance(service_email, unicode) else service_email.decode('utf-8')
        request.user_data = None
        request.app_data = None
        request.data = None
        request.type = type_
        request.keys = request.values = []
        if mobile_supports_feature(mobile, Features.SPLIT_USER_DATA):
            request.data = json.dumps(updated_json_dict).decode("utf8")
        elif UpdateUserDataRequestTO.DATA_TYPE_USER == type_:
            request.user_data = json.dumps(full_json_dict).decode("utf8")
        else:
            request.app_data = json.dumps(full_json_dict).decode("utf8")

        capi_calls.extend(updateUserData(update_user_data_response_handler, logError, target_user, request=request,
                                         MOBILE_ACCOUNT=mobile, DO_NOT_SAVE_RPCCALL_OBJECTS=True))
    return capi_calls


@returns(NoneType)
@arguments(service_identity_user=users.User, friend_user=users.User, data_string=unicode, replace=bool,
           must_be_friends=bool)
def set_user_data(service_identity_user, friend_user, data_string, replace=False, must_be_friends=True):
    data_dict = _get_json_dict_from_string(data_string)
    if not data_dict:
        return
    set_user_data_object(service_identity_user, friend_user, data_dict, replace, must_be_friends)


@returns(NoneType)
@arguments(service_identity_user=users.User, friend_user=users.User, data_dict=dict, replace=bool,
           must_be_friends=bool)
def set_user_data_object(service_identity_user, friend_user, data_dict, replace=False, must_be_friends=True):
    def trans(updated_json_dict):
        user_data_key = UserData.createKey(friend_user, service_identity_user)
        friend_map, user_data, user_profile = db.get([get_friends_map_key_by_user(friend_user),
                                                      user_data_key,
                                                      get_profile_key(friend_user)])
        current_mobile = users.get_current_mobile()

        if not friend_map:
            if len(updated_json_dict) == 1 and DISABLED_BROADCAST_TYPES_USER_DATA_KEY in updated_json_dict:
                # User is disabling a news item
                friend_map = FriendMap.create(friend_user)
            else:
                raise FriendNotFoundException()

        friend_detail_user = remove_slash_default(service_identity_user)
        friend_exists = friend_detail_user in friend_map.friends
        if must_be_friends:
            if not friend_exists:
                raise FriendNotFoundException()
            friend_detail = friend_map.friendDetails[friend_detail_user.email()]
            if friend_detail.existence != FriendDetail.FRIEND_EXISTENCE_ACTIVE:
                raise FriendNotFoundException()

        full_json_dict = updated_json_dict
        # The mobile that triggered this request should not be updated.
        mobiles_future = db.get_async([get_mobile_key_by_account(m.account) for m in user_profile.mobiles
                                       if not current_mobile or m.account != current_mobile.account])
        if user_data:
            if replace:
                user_data.data = None
                if user_data.userData is None:
                    user_data.userData = KVStore(user_data_key)
                else:
                    user_data.userData.clear()
            elif user_data.userData is None:
                user_data.userData = KVStore(user_data_key)
                if user_data.data:
                    full_json_dict = json.loads(user_data.data)
                    full_json_dict.update(updated_json_dict)
                user_data.data = None
            else:
                full_json_dict = user_data.userData.to_json_dict()
                full_json_dict.update(updated_json_dict)
        else:
            user_data = UserData(key=user_data_key,
                                 data=None,
                                 userData=KVStore(user_data_key))

        puts = []
        if DISABLED_BROADCAST_TYPES_USER_DATA_KEY in full_json_dict:
            service_user = get_service_user_from_service_identity_user(service_identity_user)
            if friend_exists:
                service_profile, fsic = db.get([get_profile_key(service_user),
                                                FriendServiceIdentityConnection.createKey(friend_user,
                                                                                          service_identity_user)])
            else:
                service_profile, si = db.get([get_profile_key(service_user),
                                              ServiceIdentity.keyFromUser(service_identity_user)])
                # Create FSIC and FriendDetail with existence=DELETED
                fsic = FriendServiceIdentityConnection.create(friend_user, user_profile.name, user_profile.avatarId,
                                                              service_identity_user, service_profile.broadcastTypes,
                                                              user_profile.birthdate, user_profile.gender,
                                                              user_profile.app_id, deleted=True)
                friend_map.friendDetails.addNew(friend_detail_user, si.name, service_profile.avatarId,
                                                type_=FriendDetail.TYPE_SERVICE, hasUserData=False,
                                                existence=FriendDetail.FRIEND_EXISTENCE_DELETED)
                friend_map.friends.append(friend_detail_user)

            fsic.disabled_broadcast_types = full_json_dict[DISABLED_BROADCAST_TYPES_USER_DATA_KEY]
            fsic.enabled_broadcast_types = list(
                set(service_profile.broadcastTypes) - set(fsic.disabled_broadcast_types))
            puts.append(fsic)
            full_json_dict.pop(DISABLED_BROADCAST_TYPES_USER_DATA_KEY)

        try:
            user_data.userData.from_json_dict(full_json_dict, remove_none_values=True)
        except InvalidKeyError as e:
            raise InvalidKeyException(key=e.key)

        friend_detail = friend_map.friendDetails[friend_detail_user.email()]
        if len(user_data.userData.keys()) > 0:
            puts.append(user_data)  # create or update UserData
            friend_detail.hasUserData = True
        else:
            db.delete_async(user_data_key)
            friend_detail.hasUserData = False
        friend_detail.relationVersion += 1
        friend_map.generation += 1
        puts.append(friend_map)

        if not friend_exists:
            friend_map.version += 1
            helper = FriendHelper.from_data_store(service_identity_user, FRIEND_TYPE_SERVICE)
            puts.extend(create_update_friend_requests(helper, service_identity_user, friend_map,
                                                      UpdateFriendRequestTO.STATUS_ADD))

        logging.debug("debugging_branding set_user_data_object friend_map.ver %s friend_map.gen %s friend_detail.relv %s",
                      friend_map.version, friend_map.generation, friend_detail.relationVersion)

        # Remove None values from full_json_dict
        full_json_dict = {k: v for k, v in full_json_dict.iteritems() if v is not None}
        mobiles = mobiles_future.get_result()
        puts.extend(get_update_userdata_requests(mobiles, friend_map.user, service_identity_user, full_json_dict,
                                                 updated_json_dict.keys()))
        put_and_invalidate_cache(*puts)

    run_in_xg_transaction(trans, data_dict)


@returns(dict)
@arguments(kv_store=KVStore, keys=[unicode])
def _get_data_from_kv_store(kv_store, keys):
    result = dict()
    for key in keys:
        data = kv_store.get(key)
        if data:
            result[key] = json.load(data) if hasattr(data, 'getvalue') else data
    return result


@returns(dict)
@arguments(json_str=unicode)
def _get_json_dict_from_string(json_str):
    try:
        json_dict = json.loads(json_str)
    except:
        raise InvalidJsonStringException()
    if json_dict is None:
        raise InvalidJsonStringException()
    if not isinstance(json_dict, dict):
        raise InvalidJsonStringException()
    return json_dict


@returns(unicode)
@arguments(service_identity_user=users.User, friend_user=users.User, user_data_keys=[unicode])
def get_user_data(service_identity_user, friend_user, user_data_keys):

    def trans():
        result = {key: None for key in user_data_keys}
        user_data = db.get(UserData.createKey(friend_user, service_identity_user))
        if user_data:
            if user_data.userData:
                result.update(_get_data_from_kv_store(user_data.userData, user_data_keys))
            else:
                data = json.loads(user_data.data)
                for key in user_data_keys:
                    result[key] = data.get(key)
        return result

    return json.dumps(db.run_in_transaction(trans))


@returns(unicode)
@arguments(service_identity_user=users.User, data_string=unicode)
def set_app_data(service_identity_user, data_string):

    def trans(json_dict):
        si = get_service_identity(service_identity_user)
        if not si.serviceData:
            si.serviceData = KVStore(si.key())

        if si.appData:
            old_app_data = json.loads(si.appData)
            old_app_data.update(json_dict)
            json_dict = old_app_data
        si.appData = None
        try:
            si.serviceData.update(json_dict, remove_none_values=True)
        except InvalidKeyError, e:
            raise InvalidKeyException(e.key)
        si.put()
        update_friends(si)

    json_dict = _get_json_dict_from_string(data_string)
    if not json_dict:
        return

    db.run_in_transaction(trans, json_dict)


@returns(unicode)
@arguments(service_identity_user=users.User, keys=[unicode])
def get_app_data(service_identity_user, keys):

    def trans():
        result = {key: None for key in keys}
        si = get_service_identity(service_identity_user)
        if si.serviceData:
            result.update(_get_data_from_kv_store(si.serviceData, keys))
        else:
            data = json.loads(si.appData)
            for key in keys:
                result[key] = data.get(key)
        return result

    return json.dumps(db.run_in_transaction(trans))


@returns()
@arguments(service_user=users.User, app_ids=[unicode])
def validate_app_admin(service_user, app_ids):
    app_keys = list()
    for app_id in app_ids:
        if not app_id:
            raise InvalidAppIdException(app_id=app_id)
        app_keys.append(App.create_key(app_id))

    apps = get_apps_by_keys(app_keys)
    for app_id, app in zip(app_ids, apps):
        if not app:
            from rogerthat.bizz.app import AppDoesNotExistException
            raise AppDoesNotExistException(app_id)
        if service_user.email() not in app.admin_services:
            raise AppOperationDeniedException(app.app_id)


@returns(tuple)
@arguments(email=unicode, name=unicode, password=unicode, languages=[unicode], solution=unicode, category_id=unicode,
           organization_type=int, fail_if_exists=bool, supported_app_ids=[unicode],
           callback_configuration=ServiceCallbackConfigurationTO, owner_user_email=unicode)
def create_service(email, name, password, languages, solution, category_id, organization_type, fail_if_exists=True,
                   supported_app_ids=None, callback_configuration=None, owner_user_email=None):
    service_email = email
    new_service_user = users.User(service_email)

    def update(service_profile, service_identity):
        # runs in transaction started in create_service_profile
        if callback_configuration:
            callbacks = 0
            for function in callback_configuration.functions:
                if function in SERVICE_API_CALLBACK_MAPPING:
                    callbacks |= SERVICE_API_CALLBACK_MAPPING[function]
                else:
                    raise CallbackNotDefinedException(function)
            configure_profile(service_profile, callback_configuration.uri, callbacks)
        else:
            configure_profile_for_mobidick(service_profile)
        service_profile.supportedLanguages = languages
        service_profile.passwordHash = sha256_hex(password)
        service_profile.lastUsedMgmtTimestamp = now()
        service_profile.solution = solution
        service_profile.sik = unicode(generate_random_key())
        service_profile.category_id = category_id
        service_profile.organizationType = organization_type
        service_profile.version = 1

        service_identity.qualifiedIdentifier = owner_user_email
        service_identity.content_branding_hash = None

        sik = SIKKey(key_name=service_profile.sik)
        sik.user = new_service_user
        api_key = _generate_api_key(solution or "mobidick", new_service_user)

        to_put = [sik, api_key]

        if owner_user_email:
            user_profile = get_user_profile(users.User(owner_user_email), cached=False)
            if user_profile:
                logging.info('Coupling user %s to %s', owner_user_email, service_email)
                if service_email not in user_profile.owningServiceEmails:
                    user_profile.owningServiceEmails.append(service_email)
                if not user_profile.passwordHash:
                    user_profile.passwordHash = password_hash
                    user_profile.isCreatedForService = True
                to_put.append(user_profile)
            else:
                logging.info('Coupling new user %s to %s', owner_user_email, service_email)
                user_profile = create_user_profile(users.User(owner_user_email), owner_user_email, languages[0])
                user_profile.isCreatedForService = True
                user_profile.owningServiceEmails = [service_email]
                update_password_hash(user_profile, password_hash, now())

        put_and_invalidate_cache(*to_put)
        # service_profile and service_identity are put in transaction in create_service_profile
        return sik, api_key

    # Check that there are no users with this e-mail address
    profile = get_service_or_user_profile(users.User(service_email), cached=False)
    existing_service_profile = None
    if profile:
        if isinstance(profile, UserProfile):
            raise UserWithThisEmailAddressAlreadyExistsException(service_email)
        elif isinstance(profile, ServiceProfile):
            existing_service_profile = profile

    password_hash = sha256_hex(password)

    if existing_service_profile:
        if fail_if_exists:
            raise ServiceAlreadyExistsException()
        else:
            api_keys = list(get_api_keys(new_service_user))

            def trans():
                service_profile = get_service_profile(new_service_user)
                service_profile.passwordHash = password_hash
                service_profile.put()
                sik = SIKKey(key_name=service_profile.sik)
                if api_keys:
                    logging.info("api_keys set")
                    api_key = api_keys[0]
                else:
                    logging.info("api_keys not set")
                    ak = _generate_api_key("Main", new_service_user)
                    ak.put()
                    api_key = ak.ak
                return sik, api_key

            xg_on = db.create_transaction_options(xg=True)
            return db.run_in_transaction_options(xg_on, trans)

    if category_id and not get_friend_category_by_id(category_id):
        raise CategoryNotFoundException()

    try:
        name = _validate_name(name)
    except ValueError as e:
        logging.debug("Invalid name", exc_info=1)
        raise InvalidNameException(e.message)

    for language in languages:
        if language not in OFFICIALLY_SUPPORTED_LANGUAGES:
            raise UnsupportedLanguageException()

    if supported_app_ids:

        @db.non_transactional
        def validate_supported_apps():
            for app_id, app in zip(supported_app_ids, App.get(map(App.create_key, supported_app_ids))):
                if not app:
                    raise InvalidAppIdException(app_id)

        validate_supported_apps()

    sik, api_key = create_service_profile(new_service_user, name, False, update, supported_app_ids=supported_app_ids)[2]

    return sik, api_key


@returns(NoneType)
@arguments(service_user=users.User, friends=[BaseMemberTO])
def publish_changes(service_user, friends=None):

    # Leave service_profile.autoUpdating as it is, just send updates to the connected users if there are updates
    def trans():
        service_profile = get_service_profile(service_user, False)
        azzert(service_profile)

        if service_profile.updatesPending:
            if friends:
                target_users = [f.app_user for f in friends]
                for app_user in target_users:
                    schedule_update_a_friend_of_service_user(service_profile, app_user, force=True)
            else:
                service_profile.updatesPending = False
                service_profile.put()
                schedule_update_all_friends_of_service_user(service_profile, force=True)

        return service_profile

    service_profile = db.run_in_transaction(trans)
    if not friends:
        channel.send_message(service_user, 'rogerthat.service.updatesPendingChanged',
                             updatesPending=service_profile.updatesPending)


@ndb.non_transactional()
@returns(NoneType)
@arguments(service_user=users.User, broadcast_type=unicode)
def validate_broadcast_type(service_user, broadcast_type):
    service_profile = get_service_profile(service_user, False)
    if broadcast_type not in service_profile.broadcastTypes:
        logging.debug('Unknown broadcast type: %s\nKnown broadcast types are: %s',
                      broadcast_type, service_profile.broadcastTypes)
        raise InvalidBroadcastTypeException(broadcast_type)


@returns(NoneType)
@arguments(service_identity=ServiceIdentity, app_id=unicode)
def validate_app_id_for_service_identity(service_identity, app_id):
    '''Validate that the service identity supports the provided app'''
    validate_is_friend_or_supports_app_id(service_identity, app_id, None)


@returns(NoneType)
@arguments(service_identity=ServiceIdentity, app_id=unicode, app_user=users.User)
def validate_is_friend_or_supports_app_id(service_identity, app_id, app_user):
    '''Validate that the service identity supports the provided app, or is connected to the provided user'''
    if app_id not in service_identity.appIds:
        if app_user is None or not get_friend_serviceidentity_connection(app_user, service_identity.user):
            raise InvalidAppIdException(app_id)


@returns(NoneType)
@arguments(service_identity_user=users.User, app_id=unicode)
def validate_app_id_for_service_identity_user(service_identity_user, app_id):
    validate_app_id_for_service_identity(get_service_identity(service_identity_user), app_id)


@returns(unicode)
@arguments(service_identity=ServiceIdentity, app_id=unicode, friend_email=unicode)
def get_and_validate_app_id_for_service_identity(service_identity, app_id, friend_email=None):
    if not app_id or app_id is MISSING:
        return service_identity.app_id
    app_user = create_app_user_by_email(friend_email, app_id) if friend_email else None
    validate_is_friend_or_supports_app_id(service_identity, app_id, app_user)
    return app_id


@returns(unicode)
@arguments(service_identity_user=users.User, app_id=unicode, friend_email=unicode)
def get_and_validate_app_id_for_service_identity_user(service_identity_user, app_id, friend_email=None):
    return get_and_validate_app_id_for_service_identity(get_service_identity(service_identity_user),
                                                        app_id,
                                                        friend_email)


def add_app_id_to_services(app_id, service_emails):
    for service_email in service_emails:
        service_user = users.User(service_email)
        with users.set_user(service_user):
            service_identity = get_default_service_identity(service_user)
            if not service_identity or service_identity.appIds is None:
                continue
            if app_id not in service_identity.appIds:
                service_identity.appIds.append(app_id)
                service_profile = get_service_profile(service_user)
                to = ServiceIdentityDetailsTO.fromServiceIdentity(service_identity, service_profile)
                update_service_identity(service_user, to)


def schedule_add_app_id_to_services(app_id, service_emails):
    deferred.defer(add_app_id_to_services, app_id, service_emails,
                   _transactional=db.is_in_transaction())


def fake_friend_connection(map_key_or_user, si):
    def _update_friend_map():
        if isinstance(map_key_or_user, users.User):
            friend_map = get_friends_map(map_key_or_user)
        else:
            friend_map = db.get(map_key_or_user)
        friend_map.generation += 1
        friend_map.version += 1
        friend_map.put()
        return friend_map

    friend_map = run_in_transaction(_update_friend_map)

    friend_detail = FriendDetails().addNew(remove_slash_default(si.user),
                                           si.name, si.avatarId, type_=FriendDetail.TYPE_SERVICE)
    friend_detail.relationVersion = -1
    friend_detail.existence = FriendDetail.FRIEND_EXISTENCE_DELETED

    logging.debug("debugging_branding fake_friend_connection friend_map.ver %s friend_map.gen %s friend_detail.relv %s",
                  friend_map.version, friend_map.generation, friend_detail.relationVersion)

    extra_conversion_kwargs = {'existence': FriendTO.FRIEND_EXISTENCE_DELETED, 'includeServiceDetails': False}
    friend_update_status = UpdateFriendRequestTO.STATUS_ADD
    helper = FriendHelper.from_data_store(users.User(friend_detail.email), friend_detail.type)
    friend_to = convert_friend(helper, friend_map.user, friend_detail, friend_update_status, extra_conversion_kwargs)
    do_update_friend_request(friend_map.user, friend_to, friend_update_status, friend_map, helper)
