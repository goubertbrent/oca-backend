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
from Queue import Queue, Empty
from threading import Thread
from types import NoneType

from google.appengine.ext import db

from mcfw.rpc import returns, arguments
from rogerthat.bizz import app as bizz_app
from rogerthat.bizz.communities.communities import get_community
from rogerthat.bizz.service import validate_app_admin, get_and_validate_app_id_for_service_identity_user
from rogerthat.dal.app import get_app_translations
from rogerthat.dal.friend import get_friends_map_key_by_user
from rogerthat.dal.profile import get_user_profiles_by_app_id, get_service_profile
from rogerthat.dal.registration import list_installations_by_app, get_installation_logs_by_installation, \
    get_mobiles_and_profiles_for_installations
from rogerthat.dal.service import get_default_service_identity
from rogerthat.models import Installation, ServiceProfile
from rogerthat.rpc import users
from rogerthat.rpc.models import ServiceAPICallback
from rogerthat.rpc.rpc import mapping
from rogerthat.rpc.service import service_api, service_api_callback
from rogerthat.to.app import AppInfoTO, AppUserListResultTO, AppUserTO, AppSettingsTO, PutLoyaltyUserResultTO, \
    AppTranslationTO
from rogerthat.to.installation import InstallationListTO, InstallationLogTO, InstallationTO
from rogerthat.utils.app import create_app_user, get_app_user_tuple
from rogerthat.utils.crypto import decrypt, encrypt
from rogerthat.utils.service import add_slash_default


#############################################
# DO NOT DOCUMENT THIS SERVICE API FUNCTION #
@service_api(function=u'app.get_info')
@returns(AppInfoTO)
@arguments(app_id=unicode)
def get_info(app_id):
    app = bizz_app.get_app(app_id)
    return AppInfoTO.fromModel(app) if app else None


@service_api(function=u'app.put_user_regexes')
@returns()
@arguments(app_id=unicode, regexes=[unicode])
def put_user_regexes(app_id, regexes):
    service_user = users.get_current_user()
    validate_app_admin(service_user, [app_id])
    bizz_app.put_user_regexes(service_user, app_id, regexes)


@service_api(function=u'app.del_user_regexes')
@returns()
@arguments(app_id=unicode, regexes=[unicode])
def del_user_regexes(app_id, regexes):
    service_user = users.get_current_user()
    validate_app_admin(service_user, [app_id])
    bizz_app.del_user_regexes(service_user, app_id, regexes)


@service_api(function=u'app.put_profile_data')
@returns(NoneType)
@arguments(email=unicode, profile_data=unicode, app_id=unicode)
def put_profile_data(email, profile_data, app_id):
    from rogerthat.bizz.profile import set_profile_data
    service_user = users.get_current_user()
    validate_app_admin(service_user, [app_id])
    set_profile_data(service_user, create_app_user(users.User(email), app_id), profile_data)


@service_api(function=u'app.del_profile_data')
@returns(NoneType)
@arguments(email=unicode, profile_data_keys=[unicode], app_id=unicode)
def del_profile_data(email, profile_data_keys, app_id):
    from rogerthat.bizz.profile import set_profile_data
    service_user = users.get_current_user()
    validate_app_admin(service_user, [app_id])
    set_profile_data(service_user,
                     create_app_user(users.User(email), app_id),
                     json.dumps(dict(((key, None) for key in profile_data_keys))))


@service_api(function=u'app.list_users')
@returns(AppUserListResultTO)
@arguments(app_id=unicode, cursor=unicode)
def list_users(app_id, cursor):
    service_user = users.get_current_user()
    validate_app_admin(service_user, [app_id])

    if cursor:
        cursor = decrypt(service_user, cursor)

    query = get_user_profiles_by_app_id(app_id)
    query.with_cursor(cursor)
    user_profiles = query.fetch(1000)
    cursor = query.cursor()
    extra_key = query.fetch(1)

    result = AppUserListResultTO()
    result.cursor = unicode(encrypt(service_user, cursor)) if len(extra_key) > 0 else None

    work = Queue()
    results = Queue()
    for items in [user_profiles[x:x + 50] for x in xrange(0, len(user_profiles), 50)]:
        work.put(items)

    def slave():
        while True:
            try:
                user_profiles = work.get_nowait()
            except Empty:
                break  # No more work, goodbye
            try:
                friendMaps = db.get([get_friends_map_key_by_user(user_profile.user) for user_profile in user_profiles])
                for user_profile, friendMap in zip(user_profiles, friendMaps):
                    results.put(AppUserTO(user_profile, friendMap))
            except Exception, e:
                results.put(e)

    threads = list()
    for _ in xrange(10):
        t = Thread(target=slave)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    result.users = list()
    while not results.empty():
        app_user = results.get()
        if isinstance(app_user, AppUserTO):
            result.users.append(app_user)
        else:
            raise app_user

    return result


@service_api(function=u'app.get_settings')
@returns(AppSettingsTO)
@arguments(app_id=unicode)
def get_settings(app_id=None):
    """
    Args:
        app_id (unicode)
    Returns:
        AppSettingsTO
    """
    service_user = users.get_current_user()
    if not app_id:
        app_id = get_community(get_service_profile(service_user).community_id).default_app

    validate_app_admin(service_user, [app_id])
    return AppSettingsTO.from_model(bizz_app.get_app_settings(app_id))


@service_api(function=u'app.put_settings')
@returns(AppSettingsTO)
@arguments(settings=AppSettingsTO, app_id=unicode)
def put_settings(settings, app_id=None):
    """
    Args:
        settings (AppSettingsTO)
        app_id (unicode)
    Returns:
        AppSettingsTO
    """
    service_user = users.get_current_user()
    if not app_id:
        app_id = get_community(get_service_profile(service_user).community_id).default_app

    validate_app_admin(service_user, [app_id])
    return AppSettingsTO.from_model(bizz_app.put_settings(app_id, settings))


@service_api(function=u'app.put_loyalty_user')
@returns(PutLoyaltyUserResultTO)
@arguments(url=unicode, email=unicode)
def put_loyalty_user(url, email):
    from rogerthat.bizz.profile import put_loyalty_user as bizz_put_loyalty_user
    service_user = users.get_current_user()
    result = PutLoyaltyUserResultTO()
    result.url, app_user = bizz_put_loyalty_user(service_user, url, email)
    human_user, result.app_id = get_app_user_tuple(app_user)
    result.email = human_user.email()
    return result


@service_api(function=u'app.get_translations')
@returns([AppTranslationTO])
@arguments(language=unicode, app_id=unicode)
def get_translations(language, app_id=None):
    service_user = users.get_current_user()
    app_id = get_and_validate_app_id_for_service_identity_user(add_slash_default(service_user), app_id)
    translations = get_app_translations(app_id)
    result = []

    if translations and translations.translations_dict:
        for key, value in translations.translations_dict.get(language, {}).iteritems():
            result.append(AppTranslationTO(key, value))

    return result


@service_api(function=u'app.list_installations')
@returns(InstallationListTO)
@arguments(app_id=unicode, cursor=unicode, page_size=(int, long), detailed=bool)
def list_installations(app_id, cursor=None, page_size=50, detailed=False):
    page_size = min(1000, page_size)
    service_user = users.get_current_user()
    validate_app_admin(service_user, [app_id])
    installations, cursor, has_more = list_installations_by_app(app_id, cursor, page_size)
    mobiles = {}
    profiles = {}
    if detailed:
        mobiles, profiles = get_mobiles_and_profiles_for_installations(installations)
    return InstallationListTO.from_query(installations, cursor, has_more, mobiles, profiles)


@service_api(function=u'app.get_installation')
@returns(InstallationTO)
@arguments(installation_id=unicode)
def get_installation(installation_id):
    service_user = users.get_current_user()
    installation = Installation.get_by_key_name(installation_id)
    validate_app_admin(service_user, [installation.app_id])
    return InstallationTO.from_model(installation, installation.mobile, installation.profile)


@service_api(function=u'app.list_installation_logs')
@returns([InstallationLogTO])
@arguments(installation_id=unicode)
def list_installation_logs(installation_id):
    service_user = users.get_current_user()
    installation = Installation.get_by_key_name(installation_id)
    validate_app_admin(service_user, [installation.app_id])
    return [InstallationLogTO.from_model(log) for log in get_installation_logs_by_installation(installation)]


@service_api_callback(function='app.installation_progress', code=ServiceProfile.CALLBACK_APP_INSTALLATION_PROGRESS)
@returns(NoneType)
@arguments(installation=InstallationTO, logs=[InstallationLogTO])
def installation_progress(installation, logs):
    # type: (InstallationTO, list[InstallationLogTO]) -> NoneType
    """
    Notifies the main service of new installation logs. Only the new logs are returned, not all of them.
    """
    pass


@mapping(u'app.installation_progress.response_receiver')
@returns(NoneType)
@arguments(context=ServiceAPICallback, result=NoneType)
def installation_progress_response_receiver(context, result):
    pass
