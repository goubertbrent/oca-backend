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
from google.appengine.ext import ndb
from typing import List

from mcfw.utils import Enum
from rogerthat.models import NdbModel
from rogerthat.rpc import users
from rogerthat.utils.service import create_service_identity_user


class CommunityAutoConnectedService(NdbModel):
    service_email = ndb.StringProperty()
    removable = ndb.BooleanProperty(indexed=False, default=True)

    @property
    def service_identity_email(self):
        return create_service_identity_user(self.service_email).email()


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



class Community(NdbModel):
    auto_connected_services = ndb.StructuredProperty(CommunityAutoConnectedService,
                                                     repeated=True)  # type: List[CommunityAutoConnectedService]
    country = ndb.StringProperty()  # 2 letter country code
    create_date = ndb.DateTimeProperty(auto_now_add=True)
    default_app = ndb.StringProperty()
    demo = ndb.BooleanProperty(default=False)
    embedded_apps = ndb.StringProperty(repeated=True)
    main_service = ndb.StringProperty()
    name = ndb.StringProperty()
    signup_enabled = ndb.BooleanProperty(default=True)
    features = ndb.StringProperty(repeated=True, choices=AppFeatures.all())  # type: List[str]

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
        return ndb.Key(cls, community_id)

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
    date = ndb.DateProperty(auto_now_add=True, indexed=False)
    count = ndb.IntegerProperty(indexed=False)


class CommunityUserStatsHistory(NdbModel):
    stats = ndb.StructuredProperty(CountOnDate, repeated=True, indexed=False)  # Should contain one entry per day

    @classmethod
    def create_key(cls, community_id):
        return ndb.Key(cls, community_id)


class CommunityUserStats(NdbModel):
    count = ndb.IntegerProperty()
    updated_on = ndb.DateTimeProperty(auto_now=True)

    @property
    def community_id(self):
        return self.key.integer_id()

    @classmethod
    def create_key(cls, community_id):
        return ndb.Key(cls, community_id)
