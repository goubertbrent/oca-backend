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
import re

from google.appengine.api import urlfetch
from google.appengine.ext import db, deferred, ndb
from typing import Tuple, List

from mcfw.cache import invalidate_cache
from mcfw.consts import MISSING
from mcfw.exceptions import HttpBadRequestException, HttpException
from mcfw.properties import get_members
from mcfw.rpc import returns, arguments
from rogerthat.bizz.communities.models import CommunityUserStats
from rogerthat.bizz.gsuite import create_app_group
from rogerthat.bizz.job import run_job
from rogerthat.bizz.service import InvalidAppIdException
from rogerthat.bizz.system import update_settings_response_handler
from rogerthat.bizz.user import delete_account
from rogerthat.capi.system import updateSettings
from rogerthat.dal import put_and_invalidate_cache
from rogerthat.dal.app import get_app_settings, get_default_app
from rogerthat.dal.mobile import get_mobile_settings_cached
from rogerthat.dal.profile import get_user_profiles_by_app_id
from rogerthat.exceptions.app import DuplicateAppIdException
from rogerthat.handlers.proxy import _exec_request
from rogerthat.models import App, AppSettings, UserProfile, ServiceIdentity, AppTranslations, AppNameMapping
from rogerthat.models.apps import EmbeddedApplication
from rogerthat.models.firebase import FirebaseProjectSettings
from rogerthat.models.properties.oauth import OAuthSettings
from rogerthat.rpc import users
from rogerthat.rpc.models import Mobile
from rogerthat.rpc.rpc import logError
from rogerthat.rpc.service import ServiceApiException
from rogerthat.settings import get_server_settings
from rogerthat.to.app import AppSettingsTO, AppTO, CreateAppTO, PatchAppTO
from rogerthat.to.statistics import CommunityUserStatisticsTO
from rogerthat.to.system import UpdateSettingsRequestTO, SettingsTO
from rogerthat.utils import now
from rogerthat.utils.transactions import run_in_xg_transaction, on_trans_committed

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class AppDoesNotExistException(ServiceApiException):

    def __init__(self, app_id):
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_APP + 0,
                                     u"App does not exist", app_id=app_id)


class AppAlreadyExistsException(ServiceApiException):

    def __init__(self, app_id):
        message = u"App %(app_id)s already exists" % dict(app_id=app_id)
        ServiceApiException.__init__(self, ServiceApiException.BASE_CODE_APP + 1, message, app_id=app_id)


@returns(App)
@arguments(app_id=unicode)
def get_app(app_id):
    # type: (unicode) -> App
    def trans():
        app = App.get(App.create_key(app_id))
        if not app:
            raise AppDoesNotExistException(app_id)
        return app

    return trans() if db.is_in_transaction() else db.run_in_transaction(trans)


@returns(bool)
@arguments(service_user=users.User, app_id=unicode, regexes=[unicode])
def put_user_regexes(service_user, app_id, regexes):
    def trans():
        app = get_app(app_id)
        user_regexes = app.user_regex.splitlines()
        updated = False
        for regex in regexes:
            if regex not in user_regexes:
                user_regexes.append(regex)
                updated = True
        if updated:
            app.user_regex = '\n'.join(user_regexes)
            app.put()
        return updated

    return db.run_in_transaction(trans)


@returns(bool)
@arguments(service_user=users.User, app_id=unicode, regexes=[unicode])
def del_user_regexes(service_user, app_id, regexes):
    def trans():
        app = get_app(app_id)
        user_regexes = app.user_regex.splitlines()
        updated = False
        for regex in regexes:
            if regex in user_regexes:
                user_regexes.remove(regex)
                updated = True
        if updated:
            app.user_regex = '\n'.join(user_regexes)
            app.put()
        return updated

    return db.run_in_transaction(trans)


@returns(AppSettings)
@arguments(app_id=unicode, settings=AppSettingsTO)
def put_settings(app_id, settings):
    """
    Args:
        app_id (unicode)
        settings (AppSettingsTO)

    Returns:
        app_settings (AppSettings)
    """

    def trans():
        updated = False
        update_mobiles = False
        app_settings = get_app_settings(app_id)
        if not app_settings:
            app_settings = AppSettings(key=AppSettings.create_key(app_id))
            updated = True

        if settings.wifi_only_downloads not in (MISSING, None) \
                and app_settings.wifi_only_downloads != settings.wifi_only_downloads:
            app_settings.wifi_only_downloads = settings.wifi_only_downloads
            updated = True

        if settings.background_fetch_timestamps not in (MISSING, None) \
                and app_settings.background_fetch_timestamps != settings.background_fetch_timestamps:
            app_settings.background_fetch_timestamps = settings.background_fetch_timestamps
            updated = True
            update_mobiles = True

        if settings.oauth is not MISSING and settings.oauth.url:
            if not app_settings.oauth:
                app_settings.oauth = OAuthSettings()
            _, simple_properties = get_members(OAuthSettings)
            for prop, _ in simple_properties:
                updated_property = getattr(settings.oauth, prop)
                if updated_property is not MISSING and getattr(app_settings.oauth, prop) != updated_property:
                    setattr(app_settings.oauth, prop, updated_property)
                    updated = True
        if settings.birthday_message_enabled is not MISSING:
            app_settings.birthday_message_enabled = settings.birthday_message_enabled
            updated = True
        if settings.birthday_message is not MISSING:
            app_settings.birthday_message = settings.birthday_message
            updated = True

        if settings.tos_enabled is not MISSING:
            app_settings.tos_enabled = settings.tos_enabled
            updated = True

        if updated:
            app_settings.put()
        if update_mobiles:
            deferred.defer(_app_settings_updated, app_id, _transactional=True)

        return app_settings

    return db.run_in_transaction(trans)


def save_firebase_settings_ios(app_id, base64_str):
    import plistlib

    try:
        stream = StringIO()
        stream.write(base64.b64decode(base64_str))
        stream.seek(0)
        pl = plistlib.readPlist(stream)
    except:
        raise HttpBadRequestException('bad_file', data={'message': 'Bad file upload'})

    app_identifier = 'com.mobicage.rogerthat.%s' % app_id
    if pl['BUNDLE_ID'] != app_identifier:
        raise HttpBadRequestException('bad_app_identifier', data={'message': 'Bad app identifier'})

    fps = FirebaseProjectSettings.create_key(pl['PROJECT_ID']).get()
    if not fps:
        raise HttpBadRequestException('firebase_project_not_found',
                                      data={'message': 'Firebase project does not exist yet.'})

    def trans():
        app_settings = get_app_settings(app_id)
        if not app_settings:
            raise HttpBadRequestException('bad_settings', data={'message': 'App settings not found'})

        app_settings.ios_firebase_project_id = fps.project_id
        app_settings.put()

        return app_settings

    return db.run_in_transaction(trans)


@returns()
@arguments(app_id=unicode)
def _app_settings_updated(app_id):
    run_job(get_user_profiles_by_app_id, [app_id],
            push_app_settings_to_user, [app_id])


@returns()
@arguments(user_profile=UserProfile, app_id=unicode)
def push_app_settings_to_user(user_profile, app_id):
    app_settings = get_app_settings(app_id)
    if user_profile.mobiles:
        mobiles = db.get([Mobile.create_key(mobile_detail.account) for mobile_detail in user_profile.mobiles])
        for mobile in mobiles:
            mobile_settings = get_mobile_settings_cached(mobile)
            mobile_settings.version += 1
            mobile_settings.put()

            request = UpdateSettingsRequestTO()
            request.settings = SettingsTO.fromDBSettings(app_settings, user_profile, mobile_settings)
            updateSettings(update_settings_response_handler, logError, mobile.user, request=request)


def validate_user_regex(user_regex):
    all_ok = True
    error_message = "Invalid user regex:\\n\\n"
    regexes = user_regex.splitlines()

    for i, regex in enumerate(regexes):
        try:
            re.match(regex, "")
        except:
            all_ok = False
            error_message += 'line %s: %s\\n' % (i + 1, regex)
    if not all_ok:
        raise HttpBadRequestException('invalid_user_regex', data={})


def get_community_statistics(community_ids):
    # type: (List[long]) -> List[CommunityUserStatisticsTO]
    stats = ndb.get_multi([CommunityUserStats.create_key(community_id) for community_id in community_ids])
    return [
        CommunityUserStatisticsTO.from_model(model) if model else CommunityUserStatisticsTO(community_id=community_id)
        for community_id, model in zip(community_ids, stats)
    ]


def is_valid_app_id(app_id):
    return re.match('^([a-z\-0-9]+)$', app_id) is not None


@returns(App)
@arguments(data=dict)
def create_app(data):
    # type: (dict) -> App
    from solutions.common.bizz.location_data_import import import_location_data
    from solutions.common.bizz.participation.proxy import register_app
    create_app_to = CreateAppTO.from_dict(data)
    if not is_valid_app_id(create_app_to.app_id):
        raise InvalidAppIdException(create_app_to.app_id)

    def trans():
        app_key = App.create_key(create_app_to.app_id)
        if App.get(app_key):
            raise DuplicateAppIdException(create_app_to.app_id)
        embedded_app_ids = [key.id().decode('utf-8')
                            for key in EmbeddedApplication.list_by_app_type(create_app_to.app_type).fetch(keys_only=True)]
        app = App(
            key=app_key,
            type=create_app_to.app_type,
            name=create_app_to.title,
            is_default=False,
            android_app_id=u'com.mobicage.rogerthat.%s' % create_app_to.app_id.replace('-', '.'),
            dashboard_email_address=create_app_to.dashboard_email_address,
            creation_time=now(),
            country=create_app_to.country,
            embedded_apps=embedded_app_ids,
        )
        app_settings = AppSettings(key=AppSettings.create_key(app.app_id),
                                   background_fetch_timestamps=[21600] if app.type == App.APP_TYPE_CITY_APP else [])
        db.put((app, app_settings))

        deferred.defer(register_app, create_app_to.app_id, create_app_to.ios_developer_account, _transactional=True)
        deferred.defer(create_app_group, create_app_to.app_id)
        if create_app_to.official_id:
            deferred.defer(import_location_data, app.app_id, app.country, create_app_to.official_id, _transactional=True)
        appcfg_data = data.copy()
        server_settings = get_server_settings()
        appcfg_data['app_constants'] = {
            'EMAIL_HASH_ENCRYPTION_KEY': server_settings.emailHashEncryptionKey,
            'REGISTRATION_EMAIL_SIGNATURE': base64.b64decode(server_settings.registrationEmailSignature),
            'REGISTRATION_MAIN_SIGNATURE': base64.b64decode(server_settings.registrationMainSignature),
            'REGISTRATION_PIN_SIGNATURE': base64.b64decode(server_settings.registrationPinSignature),
            'GOOGLE_MAPS_KEY': server_settings.googleMapsKey,
        }
        appcfg_data['cloud_constants'] = {
            'HTTPS_BASE_URL': server_settings.baseUrl,
            'HTTPS_PORT': 443,
            'HTTP_BASE_URL': server_settings.baseUrl,  # TODO: probably can/should be removed
            'USE_TRUSTSTORE': False,
            'XMPP_DOMAIN': 'rogerth.at',
        }
        response = _exec_request('/api/apps', urlfetch.POST, {'Content-Type': 'application/json'},
                                 json.dumps(appcfg_data), True)
        if response.status_code != 200:
            logging.debug(response.content)
            raise HttpException.from_urlfetchresult(response)
        return app

    return run_in_xg_transaction(trans)


@returns(App)
@arguments(app_id=unicode, data=AppTO)
def update_app(app_id, data):
    # type: (unicode, AppTO) -> App
    # Validation
    if data.user_regex:
        validate_user_regex(data.user_regex)

    def trans():
        app = get_app(app_id)
        app.admin_services = data.admin_services
        app.name = data.name
        app.type = data.type
        app.main_service = data.main_service
        app.facebook_app_id = data.facebook_app_id
        app.ios_app_id = data.ios_app_id
        app.android_app_id = data.android_app_id
        app.dashboard_email_address = data.dashboard_email_address
        app.contact_email_address = data.contact_email_address
        app.user_regex = data.user_regex
        app.demo = data.demo
        app.beta = data.beta
        app.secure = data.secure
        app.mdp_client_id = data.mdp_client_id
        app.mdp_client_secret = data.mdp_client_secret
        app.owncloud_base_uri = data.owncloud_base_uri
        app.owncloud_admin_username = data.owncloud_admin_username
        app.owncloud_admin_password = data.owncloud_admin_password
        app.country = data.country
        app.community_ids = data.community_ids
        app.service_filter_type = data.service_filter_type

        if data.default_app_name_mapping and data.default_app_name_mapping != app.default_app_name_mapping:
            app.default_app_name_mapping = data.default_app_name_mapping
            deferred.defer(set_app_name_mapping, app_id, app.default_app_name_mapping, _transactional=True)

        app.put()
        return app

    return run_in_xg_transaction(trans)


def set_app_name_mapping(app_id, name):
    AppNameMapping(key=AppNameMapping.create_key(name), app_id=app_id).put()


@arguments(app_id=unicode)
def delete_app(app_id):
    app = get_app(app_id)
    validate_can_delete_app(app)
    to_delete = [
        AppTranslations.create_key(app_id),
        AppSettings.create_key(app_id),
        app.key()
    ]
    for profile_key in UserProfile.all(keys_only=True).filter('app_id', app_id):
        delete_account(users.User(profile_key.parent().name()))
    db.delete(to_delete)


def validate_can_delete_app(app):
    # type: (App) -> None
    service_identities = ServiceIdentity.all().filter('appIds', app.app_id).fetch(None)
    if service_identities:
        raise HttpBadRequestException('app_has_service_identity',
                                      {'service_identities': [{'identifier': a.identifier, 'name': a.name} for a in
                                                              service_identities]})


@returns(tuple)
@arguments(app_id=unicode, data=PatchAppTO)
def patch_app(app_id, data):
    # type: (str, PatchAppTO) -> Tuple[App, dict]
    def f():
        app = get_app(app_id)
        app.name = data.title
        app.type = data.app_type
        app.beta = data.playstore_track != 'production'
        app.main_service = data.main_service
        app.facebook_app_id = data.facebook_app_id
        app.facebook_app_secret = data.facebook_app_secret
        app.secure = data.secure
        app.put()
        path = '/api/apps/%s/partial' % app_id
        body = json.dumps(data.to_dict())
        result = _exec_request(path, 'put', {'Content-Type': 'application/json'}, body, True)
        if result.status_code != 200:
            raise HttpException.from_urlfetchresult(result)
        return app, json.loads(result.content)

    # Can't use the decorator here since we need the on_trans_committed that clears the cache
    return db.run_in_transaction(f)


def set_default_app(app_id):
    old_default_app = get_default_app()

    def trans(old_default_app):
        old_default_app_key = old_default_app and old_default_app.key()
        new_default_app = get_app(app_id)
        if new_default_app.key() == old_default_app_key:
            return new_default_app

        new_default_app.is_default = True

        if old_default_app_key:
            old_default_app.is_default = False
            put_and_invalidate_cache(new_default_app, old_default_app)
            on_trans_committed(logging.info, 'Default app updated from %s (%s) to %s (%s)', old_default_app.app_id,
                               old_default_app.name, new_default_app.app_id, new_default_app.name)
        else:
            put_and_invalidate_cache(new_default_app)
        return new_default_app

    app = run_in_xg_transaction(trans, old_default_app)
    invalidate_cache(get_default_app)
    return app
