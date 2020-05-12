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

from google.appengine.ext import ndb

from mcfw.cache import CachedModelMixIn, invalidate_cache
from mcfw.serialization import register, s_any, ds_any, List
from mcfw.utils import Enum
from rogerthat.bizz.gcs import get_serving_url
from rogerthat.models.common import NdbModel
from rogerthat.rpc import users
from rogerthat.utils.service import get_service_identity_tuple


class AppAsset(ndb.Model):
    TYPE_CHAT_BACKGROUND_IMAGE = u'ChatBackgroundImage'
    TYPES = (TYPE_CHAT_BACKGROUND_IMAGE,)
    MAX_SIZE = 4096 * 1024
    content_key = ndb.StringProperty(indexed=False)
    app_ids = ndb.StringProperty(repeated=True)
    uploaded_on = ndb.DateTimeProperty(auto_now_add=True)
    modified_on = ndb.DateTimeProperty(auto_now=True)
    content_type = ndb.StringProperty(indexed=False)
    scale_x = ndb.FloatProperty(indexed=False)
    asset_type = ndb.StringProperty()
    serving_url = ndb.StringProperty(indexed=False)

    @property
    def is_default(self):
        return self.key.id() == 'default_%s' % self.asset_type

    @classmethod
    def default_key(cls, asset_type):
        assert (asset_type in cls.TYPES)
        return ndb.Key(cls, 'default_%s' % asset_type)

    @classmethod
    def list_by_type(cls, asset_type):
        return cls.query(cls.asset_type == asset_type)

    @classmethod
    def get_by_app_id(cls, app_id, asset_type):
        return cls.list_by_type(asset_type).filter(cls.app_ids == app_id).get()

    @classmethod
    def get_by_app_ids(cls, app_ids, asset_type):
        return cls.list_by_type(asset_type).filter(cls.app_ids.IN(app_ids))

    @classmethod
    def list_by_app_id(cls, app_id):
        return cls.query(cls.app_ids == app_id)

    @classmethod
    def list_default(cls):
        keys = [cls.default_key(asset_type) for asset_type in cls.TYPES]
        return ndb.get_multi(keys)


class DefaultBranding(ndb.Model):
    TYPE_BIRTHDAY_MESSAGE = u'DefaultBirthdayMessageBranding'
    TYPES = (TYPE_BIRTHDAY_MESSAGE,)

    branding = ndb.StringProperty(indexed=False)
    app_ids = ndb.StringProperty(repeated=True)
    uploaded_on = ndb.DateTimeProperty(auto_now_add=True)
    modified_on = ndb.DateTimeProperty(auto_now=True)
    branding_type = ndb.StringProperty()

    @property
    def is_default(self):
        return self.key.id() == 'default_%s' % self.branding_type

    @classmethod
    def default_key(cls, asset_type):
        assert (asset_type in cls.TYPES)
        return ndb.Key(cls, 'default_%s' % asset_type)

    @classmethod
    def list_by_type(cls, asset_type):
        return cls.query(cls.branding_type == asset_type)

    @classmethod
    def get_by_app_id(cls, app_id, branding_type):
        return cls.list_by_type(branding_type).filter(cls.app_ids == app_id).get()

    @classmethod
    def get_by_app_ids(cls, app_ids, branding_type):
        return cls.list_by_type(branding_type).filter(cls.app_ids.IN(app_ids))

    @classmethod
    def list_by_app_id(cls, app_id):
        return cls.query(cls.app_ids == app_id)

    @classmethod
    def list_default(cls):
        keys = [map(ndb.Key, (cls, branding_type)) for branding_type in cls.TYPES]
        return ndb.get_multi(keys)


class NavigationItem(ndb.Model):
    action_type = ndb.StringProperty()  # null, action, click
    # None means opening an activity with default functionality
    # action means listing all services with that action and opening that action when clicked
    # click means clicking on a service menu item (linked to service_email).
    # If service_email is None -> the main service email is used
    # (action and click should be the hashed tag of the service menu item)
    action = ndb.StringProperty()  # news, messages, ...
    icon = ndb.StringProperty()  # font-awesome icon name
    icon_color = ndb.StringProperty()
    text = ndb.StringProperty()  # translation key
    collapse = ndb.BooleanProperty(default=False)  # deprecated, should be included in params insteaad
    service_email = ndb.StringProperty()
    params = ndb.JsonProperty()


class ColorSettings(ndb.Model):
    primary_color = ndb.StringProperty()
    primary_color_dark = ndb.StringProperty()
    primary_icon_color = ndb.StringProperty()
    tint_color = ndb.StringProperty()  # ios only


class HomescreenSettings(ndb.Model):
    color = ndb.StringProperty()
    items = ndb.LocalStructuredProperty(NavigationItem, repeated=True)
    style = ndb.StringProperty()
    header_image_url = ndb.StringProperty()


class ToolbarSettings(ndb.Model):
    items = ndb.LocalStructuredProperty(NavigationItem, repeated=True)


class LookAndFeelServiceRoles(ndb.Model):
    role_ids = ndb.IntegerProperty(repeated=True)
    service_email = ndb.StringProperty()

    @property
    def service_identity_tuple(self):
        return get_service_identity_tuple(users.User(self.service_email))


class AppLookAndFeel(CachedModelMixIn, ndb.Model):
    app_id = ndb.StringProperty()
    colors = ndb.LocalStructuredProperty(ColorSettings)
    homescreen = ndb.LocalStructuredProperty(HomescreenSettings)
    toolbar = ndb.LocalStructuredProperty(ToolbarSettings)
    roles = ndb.LocalStructuredProperty(LookAndFeelServiceRoles, repeated=True)

    @classmethod
    def create_key(cls, look_and_feel_id):
        return ndb.Key(cls, look_and_feel_id)

    @property
    def id(self):
        return self.key.id()

    def invalidateCache(self):
        from rogerthat.bizz.look_and_feel import get_look_and_feel_by_app_id
        invalidate_cache(get_look_and_feel_by_app_id, self.app_id)

    @classmethod
    def get_by_app_id(cls, app_id):
        return cls.query(cls.app_id == app_id)


register(List(AppLookAndFeel), s_any, ds_any)


class EmbeddedApplicationTag(Enum):
    PAYMENTS = u'payments'


class EmbeddedApplicationType(Enum):
    CHAT_PAYMENT = u'chat-payment'
    WIDGET_PAY = u'widget-pay'


class EmbeddedApplication(NdbModel):
    file_path = ndb.StringProperty(indexed=False)  # /cloudstorage_bucket/path/to/file.extension
    modification_date = ndb.DateTimeProperty(auto_now=True, indexed=False)
    tags = ndb.StringProperty(repeated=True, choices=EmbeddedApplicationTag.all())
    url_regexes = ndb.StringProperty(indexed=False, repeated=True)
    version = ndb.IntegerProperty(indexed=False, default=1)
    title = ndb.StringProperty(indexed=False)
    description = ndb.StringProperty(indexed=False)
    types = ndb.StringProperty(repeated=True, choices=EmbeddedApplicationType.all())
    app_types = ndb.IntegerProperty(repeated=True)

    @property
    def serving_url(self):
        return get_serving_url(self.file_path) if self.file_path else None

    @property
    def name(self):
        return self.key.string_id().decode('utf-8')

    @classmethod
    def create_key(cls, name):
        return ndb.Key(cls, name)

    @classmethod
    def list_by_tag(cls, tag):
        return cls.query().filter(cls.tags == tag)

    @classmethod
    def list_by_type(cls, type_):
        return cls.query().filter(cls.types == type_)

    @classmethod
    def list_by_app_type(cls, app_type):
        return cls.query().filter(cls.app_types == app_type)

    def to_dict(self, extra_properties=None, include=None, exclude=None):
        return super(EmbeddedApplication, self).to_dict(extra_properties=extra_properties or ['serving_url', 'name'],
                                                        include=include,
                                                        exclude=exclude or ['file_path'])
