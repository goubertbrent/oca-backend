# -*- coding: utf-8 -*-
# Copyright 2020 Green Valley NV
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
# @@license_version:1.5@@
from __future__ import unicode_literals

from google.appengine.ext.ndb.model import StructuredProperty, GeoPtProperty, GeoPt, IntegerProperty, TextProperty, \
    BooleanProperty, StringProperty, DateTimeProperty, Key, DateProperty
from typing import List

from mcfw.consts import MISSING
from mcfw.utils import Enum
from rogerthat.models import NdbModel
from rogerthat.models.common import TOProperty
from rogerthat.rpc import users
from rogerthat.to.maps import MapButtonTO
from rogerthat.utils.service import add_slash_default, create_service_identity_user


class CommunityAutoConnectedService(NdbModel):
    service_email = StringProperty()
    removable = BooleanProperty(indexed=False, default=True)

    @property
    def service_identity_email(self):
        return create_service_identity_user(self.service_email).email()

    @property
    def service_identity_email(self):
        return add_slash_default(users.User(self.service_email)).email()


class AppFeatures(Enum):
    # Show events from merchants in the feed from the community
    EVENTS_SHOW_MERCHANTS = 'events_show_merchants'
    # Jobs features
    JOBS = 'jobs'
    # Allows adding a video to a news item
    NEWS_VIDEO = 'news_video'
    # Allows settings the location filter on news items
    NEWS_LOCATION_FILTER = 'news_location_filter'
    # Delays publishing a news item until the city has approved its content
    NEWS_REVIEW = 'news_review'
    # Allows merchants to post in regional news
    NEWS_REGIONAL = 'news_regional'
    # Allows merchants to enable/disable the 'loyalty' feature in their dashboard
    LOYALTY = 'loyalty'


# These are features that are only enabled for a few communities
class CustomizationFeatures(Enum):
    # Store the user his home address in the app data of the main service
    HOME_ADDRESS_IN_USER_DATA = 0


class Community(NdbModel):
    auto_connected_services = StructuredProperty(CommunityAutoConnectedService,
                                                 repeated=True)  # type: List[CommunityAutoConnectedService]
    country = StringProperty()  # 2 letter country code
    create_date = DateTimeProperty(auto_now_add=True)
    default_app = StringProperty()
    demo = BooleanProperty(default=False)
    embedded_apps = StringProperty(repeated=True)
    main_service = StringProperty()
    name = StringProperty()
    signup_enabled = BooleanProperty(default=True)
    features = StringProperty(repeated=True, choices=AppFeatures.all())  # type: List[str]
    customization_features = IntegerProperty(repeated=True, choices=CustomizationFeatures.all())

    @property
    def auto_connected_service_emails(self):
        return [s.service_email for s in self.auto_connected_services]

    @property
    def main_service_user(self):
        if self.main_service:
            return users.User(self.main_service)
        return None

    @property
    def id(self):
        return self.key.id()

    def is_service_removable(self, email):
        for acs in self.auto_connected_services:
            if acs.service_email == email and not acs.removable:
                return False
        return True

    def can_edit_services(self, city_service_user):
        return self.main_service == city_service_user.email()

    @classmethod
    def create_key(cls, community_id):
        return Key(cls, community_id)

    @classmethod
    def list_by_country(cls, country):
        return cls.query().filter(cls.country == country)

    @classmethod
    def list_by_auto_connected(cls, service_email):
        return cls.query().filter(cls.auto_connected_services.service_email == service_email)

    @classmethod
    def list_signup_enabled(cls):
        return cls.query(cls.signup_enabled == True)

    @classmethod
    def list_countries(cls):
        return cls.query(projection=[cls.country], distinct=True)

    @classmethod
    def get_by_default_app(cls, app_id):
        return cls.query().filter(cls.default_app == app_id).get()

    @classmethod
    def list_by_embedded_app(cls, name):
        return cls.query().filter(cls.embedded_apps == name)

    @classmethod
    def list_by_main_service(cls, service_user):
        return cls.query().filter(cls.main_service == service_user.email())


class CountOnDate(NdbModel):
    date = DateProperty(auto_now_add=True, indexed=False)
    count = IntegerProperty(indexed=False)


class CommunityUserStatsHistory(NdbModel):
    stats = StructuredProperty(CountOnDate, repeated=True, indexed=False)  # Should contain one entry per day

    @classmethod
    def create_key(cls, community_id):
        return Key(cls, community_id)


class CommunityUserStats(NdbModel):
    count = IntegerProperty()
    updated_on = DateTimeProperty(auto_now=True)

    @property
    def community_id(self):
        return self.key.integer_id()

    @classmethod
    def create_key(cls, community_id):
        return Key(cls, community_id)


class CommunityLocation(NdbModel):
    locality = StringProperty()
    postal_code = StringProperty()


class GeoFenceGeometry(NdbModel):
    center = GeoPtProperty(required=True)  # type: GeoPt
    max_distance = IntegerProperty()


class CommunityGeoFence(NdbModel):
    country = StringProperty(required=True)
    # Defaults used when creating a new point of interest
    defaults = StructuredProperty(CommunityLocation, indexed=False)
    geometry = StructuredProperty(GeoFenceGeometry, indexed=False)  # type: GeoFenceGeometry

    @classmethod
    def create_key(cls, community_id):
        return Key(cls, community_id)


class MapLayerSettings(NdbModel):
    filters = TextProperty(repeated=True)
    default_filter = TextProperty()
    buttons = TOProperty(MapButtonTO, repeated=True)  # type: List[MapButtonTO]

    @classmethod
    def from_to(cls, to):
        if not to or to is MISSING or not any((to.filters, to.default_filter, to.buttons)):
            return None
        return cls(filters=to.filters, default_filter=to.default_filter, buttons=to.buttons)


class MapLayers(NdbModel):
    gipod = StructuredProperty(MapLayerSettings, indexed=False)  # type: MapLayerSettings
    poi = StructuredProperty(MapLayerSettings, indexed=False)  # type: MapLayerSettings
    reports = StructuredProperty(MapLayerSettings, indexed=False)  # type: MapLayerSettings
    services = StructuredProperty(MapLayerSettings, indexed=False)  # type: MapLayerSettings

    def get_settings_for_tag(self, tag):
        # type: (str) -> MapLayerSettings
        return getattr(self, tag)


class CommunityMapSettings(NdbModel):
    center = GeoPtProperty(indexed=False)  # type: GeoPt
    distance = IntegerProperty(indexed=False)
    layers = StructuredProperty(MapLayers, indexed=False)  # type: MapLayers

    @classmethod
    def get_default(cls, community_id):
        return cls(key=cls.create_key(community_id),
                   center=GeoPt(50.9298839, 3.6246589),
                   distance=3000,
                   layers=MapLayers())

    @classmethod
    def create_key(cls, community_id):
        return Key(cls, community_id)
