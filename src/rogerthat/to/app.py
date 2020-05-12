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

from mcfw.properties import bool_property, unicode_property, long_property, typed_property, unicode_list_property, \
    long_list_property, float_property
from rogerthat.models.apps import LookAndFeelServiceRoles, AppLookAndFeel, ToolbarSettings, HomescreenSettings, \
    NavigationItem, ColorSettings
from rogerthat.models.properties.app import AutoConnectedService
from rogerthat.models.properties.friend import FriendDetail
from rogerthat.models.properties.oauth import OAuthSettings
from rogerthat.rpc import users
from rogerthat.to import TO
from rogerthat.utils.app import get_human_user_from_app_user
from rogerthat.utils.crypto import sha256_hex
from rogerthat.utils.service import create_service_identity_user


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


class AppTO(object):
    id = unicode_property('0')
    name = unicode_property('1')
    type = long_property('2')
    core_branding_hash = unicode_property('3')
    facebook_app_id = long_property('4')
    facebook_app_secret = unicode_property('5')
    ios_app_id = unicode_property('6')
    android_app_id = unicode_property('7')
    creation_time = long_property('8')
    auto_connected_services = typed_property('9', AutoConnectedService, True)
    is_default = bool_property('10')
    user_regex = unicode_property('11')
    dashboard_email_address = unicode_property('12')
    admin_services = unicode_list_property('13')
    demo = bool_property('17')
    beta = bool_property('18')
    chat_enabled = bool_property('19')
    mdp_client_id = unicode_property('20')
    mdp_client_secret = unicode_property('21')
    contact_email_address = unicode_property('22')
    secure = bool_property('23')
    owncloud_base_uri = unicode_property('24')
    owncloud_admin_username = unicode_property('25')
    owncloud_admin_password = unicode_property('26')
    main_service = unicode_property('27')
    embedded_apps = unicode_list_property('28')

    @classmethod
    def from_model(cls, model):
        """
        Args:
            model (rogerthat.models.App)
        """
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
        if model.auto_connected_services:
            app.auto_connected_services = list(model.auto_connected_services)
        else:
            app.auto_connected_services = []
        app.is_default = model.is_default
        app.user_regex = model.user_regex
        app.dashboard_email_address = model.dashboard_email_address
        app.admin_services = model.admin_services
        app.demo = model.demo
        app.beta = model.beta
        app.secure = model.secure
        app.chat_enabled = model.chat_enabled
        app.mdp_client_id = model.mdp_client_id
        app.mdp_client_secret = model.mdp_client_secret
        app.contact_email_address = model.contact_email_address
        app.owncloud_base_uri = model.owncloud_base_uri
        app.owncloud_admin_username = model.owncloud_admin_username
        app.owncloud_admin_password = model.owncloud_admin_password
        app.embedded_apps = model.embedded_apps if model.embedded_apps else []
        return app


class NewsStreamTO(object):
    type = unicode_property('1')


class CreateAppTO(object):
    app_id = unicode_property('1')
    name = unicode_property('2')
    type = long_property('3')
    dashboard_email_address = unicode_property('4')
    auto_added_services = unicode_list_property('5', default=[])
    news_stream = typed_property('6', NewsStreamTO, False, default=None)
    country = unicode_property('country')


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
            for f in friendMap.friendDetails:
                if f.existence != FriendDetail.FRIEND_EXISTENCE_ACTIVE:
                    continue
                self.relations.append(AppUserRelationTO(f.email, f.name,
                                                        u"human" if f.type == FriendDetail.TYPE_USER else u"application"))


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

    def __init__(self, wifi_only_downloads=None, background_fetch_timestamps=None, oauth=None,
                 birthday_message_enabled=False, birthday_message=None, tos_enabled=True,
                 ios_firebase_project_id=None):
        if background_fetch_timestamps is None:
            background_fetch_timestamps = []
        self.wifi_only_downloads = wifi_only_downloads
        self.background_fetch_timestamps = background_fetch_timestamps
        self.oauth = oauth
        self.birthday_message_enabled = birthday_message_enabled
        self.birthday_message = birthday_message
        self.tos_enabled = tos_enabled
        self.ios_firebase_project_id = ios_firebase_project_id

    @classmethod
    def from_model(cls, model):
        """
        Args:
            model (rogerthat.models.AppSettings)
        """
        return cls(model.wifi_only_downloads, model.background_fetch_timestamps, model.oauth,
                   model.birthday_message_enabled, model.birthday_message, model.tos_enabled,
                   model.ios_firebase_project_id)


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


class NavigationItemTO(object):
    # for these types the 'action' needs to be hashed when sent to the user
    HASHED_ACTION_TYPES = ('action', 'click')

    action_type = unicode_property('1')  # null, action, click, cordova
    # None means opening an activity
    # action means listing all services with that action and opening that action when clicked
    # click means clicking on a service menu item (linked to service_email).
    # If service_email is None -> the main service email is used
    # (action and click should be the hashed tag of the service menu item)
    action = unicode_property('2')  # news, messages, ...
    icon = unicode_property('3')  # font-awesome icon name
    icon_color = unicode_property('4')
    text = unicode_property('5')  # translation key
    # deprecated, should be included in params insteaad
    collapse = bool_property('6', default=False)
    service_email = unicode_property('7')
    # json string, KeyValueTO will only support string values
    params = unicode_property('8', default=None)

    def __init__(self, action_type=None, action=None, icon=None, icon_color=None, text=None, collapse=False,
                 service_email=None, params=None):
        self.action_type = action_type
        self.action = action
        self.icon = icon
        self.icon_color = icon_color
        self.text = text
        self.collapse = collapse
        self.service_email = service_email
        self.params = params

    @classmethod
    def from_model(cls, model):
        """
        Args:
            model (rogerthat.models.apps.NavigationItem)
        """
        collapse = model.collapse or model.params.get('collapse', False) if model.params else False
        return cls(model.action_type, model.action, model.icon, model.icon_color, model.text, collapse,
                   model.service_email, unicode(json.dumps(model.params or {})))

    def to_model(self):
        return NavigationItem(
            action_type=self.action_type,
            action=self.action,
            icon=self.icon,
            icon_color=self.icon_color,
            text=self.text,
            service_email=self.service_email,
            params=json.loads(self.params) if self.params else None
        )


class ColorSettingsTO(object):
    primary_color = unicode_property('1')
    primary_color_dark = unicode_property('2')
    # Unused but released in iOS in some apps so we have to keep this
    secondary_color = unicode_property('3', default=None)
    primary_icon_color = unicode_property('4')
    tint_color = unicode_property('5')

    def __init__(self, primary_color=None, primary_color_dark=None, primary_icon_color=None,
                 tint_color=None):
        self.primary_color = primary_color
        self.primary_color_dark = primary_color_dark
        self.secondary_color = None
        self.primary_icon_color = primary_icon_color
        self.tint_color = tint_color

    @classmethod
    def from_model(cls, model):
        """
        Args:
            model (rogerthat.models.apps.ColorSettings)
        """
        return cls(model.primary_color, model.primary_color_dark, model.primary_icon_color, model.tint_color)

    def to_model(self):
        return ColorSettings(
            primary_color=self.primary_color,
            primary_color_dark=self.primary_color_dark,
            primary_icon_color=self.primary_icon_color,
            tint_color=self.tint_color
        )


class HomeScreenSettingsTO(object):
    STYLE_NEWS = u'news'
    STYLE_MESSAGES = u'messages'

    color = unicode_property('1')
    items = typed_property('2', NavigationItemTO, True)
    style = unicode_property('3')
    header_image_url = unicode_property('4')

    def __init__(self, color=None, items=None, style=None, header_image_url=None):
        self.color = color
        self.items = items if items else []
        self.style = style
        self.header_image_url = header_image_url

    @classmethod
    def from_model(cls, model):
        """
        Args:
            model (rogerthat.models.apps.HomescreenSettings)
        """
        return cls(model.color, [NavigationItemTO.from_model(item) for item in model.items], model.style,
                   model.header_image_url)

    def to_model(self):
        return HomescreenSettings(
            color=self.color,
            items=[item.to_model() for item in self.items],
            style=self.style,
            header_image_url=self.header_image_url
        )


class ToolbarSettingsTO(object):
    items = typed_property('1', NavigationItemTO, True)  # type: list of NavigationItemTO

    def __init__(self, items=None):
        self.items = items if items else []

    @classmethod
    def from_model(cls, model):
        """
        Args:
            model (rogerthat.models.apps.ToolbarSettings)
        """
        return cls([NavigationItemTO.from_model(item) for item in model.items])

    def to_model(self):
        return ToolbarSettings(
            items=[item.to_model() for item in self.items]
        )


class LookAndFeelTO(object):
    colors = typed_property('1', ColorSettingsTO, False)
    homescreen = typed_property('2', HomeScreenSettingsTO, False)
    toolbar = typed_property('3', ToolbarSettingsTO, False)

    def __init__(self, colors=None, homescreen=None, toolbar=None):
        self.colors = colors
        self.homescreen = homescreen
        self.toolbar = toolbar

    @classmethod
    def from_model(cls, model):
        """
        Args:
            model (rogerthat.models.apps.AppLookAndFeel)

        Returns:

        """
        colors = ColorSettingsTO.from_model(model.colors)
        homescreen = HomeScreenSettingsTO.from_model(model.homescreen)
        toolbar = ToolbarSettingsTO.from_model(model.toolbar)

        for ni in homescreen.items + toolbar.items:
            if ni.action_type in NavigationItemTO.HASHED_ACTION_TYPES:
                ni.action = sha256_hex(ni.action).decode('utf8')

        return cls(colors, homescreen, toolbar)


class LookAndFeelServiceRolesTO(object):
    role_ids = long_list_property('1')
    service_email = unicode_property('2')
    service_identity = unicode_property('3')

    def __init__(self, role_ids=None, service_email=None, service_identity=None):
        self.role_ids = role_ids if role_ids else []
        self.service_email = service_email
        self.service_identity = service_identity

    def to_model(self):
        service_identity_user = create_service_identity_user(users.User(self.service_email), self.service_identity)
        return LookAndFeelServiceRoles(
            role_ids=self.role_ids,
            service_email=service_identity_user.email()
        )

    @classmethod
    def from_model(cls, model):
        """
        Args:
            model (LookAndFeelServiceRoles)
        """
        service_user, service_identity, = model.service_identity_tuple
        return cls(model.role_ids, service_user.email(), service_identity)


class AppLookAndFeelTO(LookAndFeelTO):
    id = long_property('50')
    app_id = unicode_property('51')
    roles = typed_property('52', LookAndFeelServiceRolesTO, True)

    def __init__(self, role_id=None, colors=None, homescreen=None, toolbar=None, app_id=None, roles=None):
        self.id = role_id
        self.app_id = app_id
        self.roles = roles if roles else []
        super(AppLookAndFeelTO, self).__init__(colors, homescreen, toolbar)

    @classmethod
    def from_model(cls, model):
        """
        Args:
            model (AppLookAndFeel)
        """
        colors = ColorSettingsTO.from_model(model.colors)
        homescreen = HomeScreenSettingsTO.from_model(model.homescreen)
        toolbar = ToolbarSettingsTO.from_model(model.toolbar)
        app_id = model.app_id
        roles = [LookAndFeelServiceRolesTO.from_model(role) for role in model.roles] if model.roles else []
        return cls(model.id, colors, homescreen, toolbar, app_id, roles)

    def to_model(self):
        return AppLookAndFeel(
            app_id=self.app_id,
            colors=self.colors.to_model(),
            homescreen=self.homescreen.to_model(),
            toolbar=self.toolbar.to_model(),
            roles=[role.to_model() for role in self.roles]
        )


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


class UpdateLookAndFeelResponseTO(object):
    pass


class UpdateLookAndFeelRequestTO(object):
    look_and_feel = typed_property('1', LookAndFeelTO, False)

    def __init__(self, look_and_feel=None):
        self.look_and_feel = look_and_feel


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


class NewsGroupTileTO(TO):
    background_image_url = unicode_property('background_image_url')
    promo_image_url = unicode_property('promo_image_url')
    title = unicode_property('title')
    subtitle = unicode_property('subtitle')
    
    @classmethod
    def from_model(cls, model):
        """
        Args:
            model (rogerthat.models.news.NewsGroupTile)
        """
        if not model:
            return None
        return cls.from_dict(model.to_dict())


class NewsGroupTO(TO):
    group_id = unicode_property('group_id')
    name = unicode_property('name')
    send_notifications = bool_property('send_notifications')
    default_notifications_enabled = bool_property('default_notifications_enabled')
    group_type = unicode_property('group_type')
    tile = typed_property('tile', NewsGroupTileTO, False)

    @classmethod
    def from_model(cls, model):
        """
        Args:
            model (rogerthat.models.news.NewsGroup)
        """
        return cls.from_dict(model.to_dict(extra_properties=['group_id']))


class NewsSettingsTO(object):
    groups = typed_property('1', NewsGroupTO, True)

    def __init__(self, groups=None):
        if groups is None:
            groups = []
        self.groups = groups
