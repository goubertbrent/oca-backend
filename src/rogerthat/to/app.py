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

from mcfw.properties import bool_property, unicode_property, long_property, typed_property, unicode_list_property, \
    long_list_property, float_property
from rogerthat.models.properties.friend import FriendDetailTO
from rogerthat.models.properties.oauth import OAuthSettings
from rogerthat.to import TO
from rogerthat.utils.app import get_human_user_from_app_user


class AppInfoTO(object):
    id = unicode_property('0')
    name = unicode_property('1')
    ios_appstore_url = unicode_property('2')
    android_playstore_url = unicode_property('3')

    @staticmethod
    def fromModel(model):
        app = AppInfoTO()
        app.id = model.app_id
        app.name = model.name
        app.ios_appstore_url = model.ios_appstore_web_uri
        app.android_playstore_url = model.android_market_android_uri
        return app


class AppQRTemplateTO(object):
    key_name = unicode_property('1')
    is_default = bool_property('2')
    description = unicode_property('3')
    body_color = unicode_property('4')

    def __init__(self, key_name=None, is_default=False, description=None, body_color=None):
        self.key_name = key_name
        self.is_default = is_default
        self.description = description
        self.body_color = body_color

    @classmethod
    def from_model(cls, model, is_default=False):
        """
        Args:
            model (rogerthat.models.QRTemplate)
            is_default (bool)
        """
        rgb = u''.join([('%X' % c).rjust(2, '0') for c in model.body_color])
        return cls(model.key().name(), is_default, model.description, rgb)


class CreateAppQRTemplateTO(AppQRTemplateTO):
    file = unicode_property('5')


class PatchAppTO(TO):
    title = unicode_property('title')
    app_type = long_property('app_type')
    playstore_track = unicode_property('playstore_track')
    main_service = unicode_property('main_service')
    secure = bool_property('secure')
    facebook_registration = bool_property('facebook_registration')
    facebook_app_id = long_property('facebook_app_id')
    facebook_app_secret = unicode_property('facebook_app_secret')
    chat_payments_enabled = bool_property('chat_payments_enabled')


class AppTO(TO):
    id = unicode_property('id')
    name = unicode_property('name')
    type = long_property('type')
    core_branding_hash = unicode_property('core_branding_hash')
    facebook_app_id = long_property('facebook_app_id')
    facebook_app_secret = unicode_property('facebook_app_secret')
    ios_app_id = unicode_property('ios_app_id')
    android_app_id = unicode_property('android_app_id')
    creation_time = long_property('creation_time')
    is_default = bool_property('is_default')
    user_regex = unicode_property('user_regex')
    dashboard_email_address = unicode_property('dashboard_email_address')
    admin_services = unicode_list_property('admin_services')
    demo = bool_property('demo')
    beta = bool_property('beta')
    mdp_client_id = unicode_property('mdp_client_id')
    mdp_client_secret = unicode_property('mdp_client_secret')
    contact_email_address = unicode_property('contact_email_address')
    secure = bool_property('secure')
    owncloud_base_uri = unicode_property('owncloud_base_uri')
    owncloud_admin_username = unicode_property('owncloud_admin_username')
    owncloud_admin_password = unicode_property('owncloud_admin_password')
    main_service = unicode_property('main_service')
    default_app_name_mapping = unicode_property('default_app_name_mapping')
    country = unicode_property('country')
    community_ids = long_list_property('community_ids')
    service_filter_type = long_property('service_filter_type')

    @classmethod
    def from_model(cls, model):
        # type: (rogerthat.models.App) -> AppTO
        app = cls()
        app.id = model.app_id
        app.name = model.name
        app.type = model.type
        app.main_service = model.main_service
        app.core_branding_hash = model.core_branding_hash
        app.facebook_app_id = model.facebook_app_id
        app.facebook_app_secret = model.facebook_app_secret
        app.ios_app_id = model.ios_app_id
        app.android_app_id = model.android_app_id
        app.creation_time = model.creation_time
        app.is_default = model.is_default
        app.user_regex = model.user_regex
        app.dashboard_email_address = model.dashboard_email_address
        app.admin_services = model.admin_services
        app.demo = model.demo
        app.beta = model.beta
        app.secure = model.secure
        app.mdp_client_id = model.mdp_client_id
        app.mdp_client_secret = model.mdp_client_secret
        app.contact_email_address = model.contact_email_address
        app.owncloud_base_uri = model.owncloud_base_uri
        app.owncloud_admin_username = model.owncloud_admin_username
        app.owncloud_admin_password = model.owncloud_admin_password
        app.default_app_name_mapping = model.default_app_name_mapping
        app.country = model.country
        app.community_ids = model.community_ids
        app.service_filter_type = model.service_filter_type
        return app


class CreateAppTO(TO):
    app_id = unicode_property('1')
    title = unicode_property('title')
    app_type = long_property('app_type')
    dashboard_email_address = unicode_property('4')
    main_language = unicode_property('main_language')
    country = unicode_property('country')
    official_id = long_property('official_id')
    ios_developer_account = long_property('ios_developer_account')
    review_notes = long_property('review_notes')


class AppUserRelationTO(object):
    email = unicode_property('1')
    name = unicode_property('2')
    type = unicode_property('3')  # human / application

    def __init__(self, email, name, type_):
        self.email = email
        self.name = name
        self.type = type_


class AppUserTO(object):
    email = unicode_property('1')
    name = unicode_property('2')
    relations = typed_property('3', AppUserRelationTO, True)

    def __init__(self, user_profile, friendMap):
        self.email = get_human_user_from_app_user(user_profile.user).email()
        self.name = user_profile.name
        self.relations = list()
        if friendMap:
            for f in friendMap.get_friend_details().values():
                if f.existence != FriendDetailTO.FRIEND_EXISTENCE_ACTIVE:
                    continue
                self.relations.append(AppUserRelationTO(f.email, f.name,
                                                        u"human" if f.type == FriendDetailTO.TYPE_USER else u"application"))


class AppUserListResultTO(object):
    cursor = unicode_property('1')
    users = typed_property('2', AppUserTO, True)


class AppSettingsTO(object):
    wifi_only_downloads = bool_property('1')
    background_fetch_timestamps = long_list_property('2')
    oauth = typed_property('3', OAuthSettings, False)
    birthday_message_enabled = bool_property('4')
    birthday_message = unicode_property('5')
    tos_enabled = bool_property('6')
    ios_firebase_project_id = unicode_property('7')
    ios_apns_key_id = unicode_property('ios_apns_key_id')

    def __init__(self, wifi_only_downloads=None, background_fetch_timestamps=None, oauth=None,
                 birthday_message_enabled=False, birthday_message=None, tos_enabled=True,
                 ios_firebase_project_id=None, ios_apns_key_id=None):
        if background_fetch_timestamps is None:
            background_fetch_timestamps = []
        self.wifi_only_downloads = wifi_only_downloads
        self.background_fetch_timestamps = background_fetch_timestamps
        self.oauth = oauth
        self.birthday_message_enabled = birthday_message_enabled
        self.birthday_message = birthday_message
        self.tos_enabled = tos_enabled
        self.ios_firebase_project_id = ios_firebase_project_id
        self.ios_apns_key_id = ios_apns_key_id

    @classmethod
    def from_model(cls, model, ios_apns_key_id=None):
        """
        Args:
            model (rogerthat.models.AppSettings)
        """
        return cls(model.wifi_only_downloads, model.background_fetch_timestamps, model.oauth,
                   model.birthday_message_enabled, model.birthday_message, model.tos_enabled,
                   model.ios_firebase_project_id, ios_apns_key_id)


# This object is sent to the phones
class AppAssetTO(object):
    kind = unicode_property('1')
    url = unicode_property('2')
    scale_x = float_property('3')

    def __init__(self, kind=None, url=None, scale_x=0.0):
        self.kind = kind
        self.url = url
        self.scale_x = scale_x


# This object is used for managing app assets
class AppAssetFullTO(AppAssetTO):
    id = unicode_property('9')
    app_ids = unicode_list_property('10')
    content_type = unicode_property('11')
    is_default = bool_property('12')

    def __init__(self, key=None, kind=None, url=None, scale_x=None, app_ids=None, uploaded_on=None, modified_on=None,
                 content_type=None, is_default=False):
        super(AppAssetFullTO, self).__init__(kind, url, scale_x)
        self.id = unicode(key)
        self.app_ids = app_ids
        self.uploaded_on = uploaded_on
        self.modified_on = modified_on
        self.content_type = content_type
        self.is_default = is_default

    @classmethod
    def from_model(cls, asset):
        """
        Args:
            asset (rogerthat.models.apps.AppAsset)
        """
        return cls(asset.key.id(), asset.asset_type, asset.serving_url, asset.scale_x, asset.app_ids, asset.uploaded_on,
                   asset.modified_on, asset.content_type, asset.is_default)


class DefaultBrandingTO(object):
    id = unicode_property('1')
    branding = unicode_property('2')
    app_ids = unicode_list_property('3')
    branding_type = unicode_property('4')
    is_default = bool_property('5')

    def __init__(self, key=None, branding=None, app_ids=None, branding_type=None, is_default=False):
        self.id = unicode(key)
        self.branding = branding
        self.app_ids = app_ids
        self.branding_type = branding_type
        self.is_default = is_default

    @classmethod
    def from_model(cls, model):
        """
        Args:
            model (rogerthat.models.apps.DefaultBranding)
        """
        return cls(model.key.id(), model.branding, model.app_ids, model.branding_type, model.is_default)


class PutLoyaltyUserResultTO(object):
    url = unicode_property('1')
    email = unicode_property('2')
    app_id = unicode_property('3')


class GetAppAssetRequestTO(object):
    kind = unicode_property('1')


class GetAppAssetResponseTO(AppAssetTO):
    pass


class UpdateAppAssetRequestTO(AppAssetTO):
    pass


class UpdateAppAssetResponseTO(object):
    pass


class AppTranslationTO(object):
    key = unicode_property('key')
    value = unicode_property('value')

    def __init__(self, key, value):
        self.key = key
        self.value = value


class CreateEmbeddedApplicationTO(TO):
    name = unicode_property('name')
    file = unicode_property('file')
    tags = unicode_list_property('tags')
    url_regexes = unicode_list_property('url_regexes', default=[])
    title = unicode_property('title')
    description = unicode_property('description')
    types = unicode_list_property('types')
    app_types = long_list_property('app_types', default=[])


class UpdateEmbeddedApplicationTO(CreateEmbeddedApplicationTO):
    pass


# For requests to the app
class EmbeddedAppTO(TO):
    name = unicode_property('name')
    title = unicode_property('title')
    description = unicode_property('description')
    types = unicode_list_property('types', default=[])
    serving_url = unicode_property('serving_url')
    version = long_property('version')
    url_regexes = unicode_list_property('url_regexes', default=[])

    @classmethod
    def from_model(cls, model):
        return cls.from_dict(model.to_dict())


class GetEmbeddedAppsResponseTO(TO):
    embedded_apps = typed_property('embedded_apps', EmbeddedAppTO, True)


class GetEmbeddedAppsRequestTO(TO):
    type = unicode_property('type', default=None)  # optional


class GetEmbeddedAppResponseTO(EmbeddedAppTO):
    pass


class GetEmbeddedAppRequestTO(TO):
    name = unicode_property('name')


class UpdateEmbeddedAppRequestTO(EmbeddedAppTO):
    pass


class UpdateEmbeddedAppResponseTO(TO):
    pass


class UpdateEmbeddedAppsRequestTO(GetEmbeddedAppsResponseTO):
    pass


class UpdateEmbeddedAppsResponseTO(TO):
    pass
