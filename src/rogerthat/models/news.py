# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
# NOTICE: THIS FILE HAS BEEN MODIFIED BY GREEN VALLEY BELGIUM NV IN ACCORDANCE WITH THE APACHE LICENSE VERSION 2.0
# Copyright 2018 GIG Technology NV
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
# @@license_version:1.6@@
from __future__ import unicode_literals

from datetime import date, datetime

from google.appengine.ext import ndb
from google.appengine.ext.ndb.query import QueryOptions

from mcfw.utils import Enum
from rogerthat.dal import parent_ndb_key
from rogerthat.models import UserProfile
from rogerthat.models.common import NdbModel
from rogerthat.models.properties.news import NewsItemStatisticsProperty, NewsButtonsProperty, \
    NewsFeedsProperty
from rogerthat.rpc import users
from rogerthat.utils import now, calculate_age_from_date


class MediaType(Enum):
    IMAGE = 'image'
    VIDEO_YOUTUBE = 'video_youtube'


class NewsMedia(NdbModel):
    type = ndb.StringProperty(choices=MediaType.all(), indexed=False)
    url = ndb.StringProperty(indexed=False)
    content = ndb.IntegerProperty(indexed=False)
    width = ndb.IntegerProperty(indexed=False)
    height = ndb.IntegerProperty(indexed=False)


class NewsItemGeoAddress(NdbModel):
    geo_location = ndb.GeoPtProperty(indexed=False)  # type: ndb.GeoPt
    distance = ndb.IntegerProperty(indexed=False)


class NewsItemAddress(NdbModel):
    LEVEL_STREET = 'STREET'
    level = ndb.StringProperty(indexed=False)

    address_uid = ndb.StringProperty()

    street_name = ndb.StringProperty(indexed=False)
    zip_code = ndb.StringProperty(indexed=False)
    city = ndb.StringProperty(indexed=False)
    country_code = ndb.StringProperty(indexed=False)


class NewsItemLocation(NdbModel):
    geo_addresses = ndb.StructuredProperty(NewsItemGeoAddress, repeated=True)
    addresses = ndb.StructuredProperty(NewsItemAddress, repeated=True)


class NewsItem(NdbModel):
    MAX_TITLE_LENGTH = 80
    MAX_BUTTON_CAPTION_LENGTH = 15
    STATISTICS_TYPE_INFLUX_DB = 'influxdb'

    sticky = ndb.BooleanProperty(indexed=True, required=True)
    sticky_until = ndb.IntegerProperty(indexed=True, default=0)
    sender = ndb.UserProperty(indexed=True, required=True)  # service identity user
    app_ids = ndb.StringProperty(indexed=True, repeated=True)
    timestamp = ndb.IntegerProperty(indexed=True, required=True)  # type: long
    update_timestamp = ndb.IntegerProperty(indexed=True, default=0)
    order_timestamp = ndb.IntegerProperty(indexed=True, default=0)
    scheduled_at = ndb.IntegerProperty(indexed=False, default=0)
    scheduled_task_name = ndb.StringProperty(indexed=False)
    published_timestamp = ndb.IntegerProperty(indexed=True, default=0)
    published = ndb.BooleanProperty(default=False)
    deleted = ndb.BooleanProperty(default=False)
    title = ndb.StringProperty(indexed=False)
    message = ndb.TextProperty()
    type = ndb.IntegerProperty(indexed=False)

    group_types_ordered = ndb.StringProperty(indexed=False, repeated=True)
    group_types = ndb.StringProperty(indexed=True, repeated=True)
    group_ids = ndb.StringProperty(indexed=True, repeated=True)
    group_visible_until = ndb.DateTimeProperty(indexed=False)

    has_locations = ndb.BooleanProperty(default=False)
    location_match_required = ndb.BooleanProperty(default=False)
    locations = ndb.StructuredProperty(NewsItemLocation)  # type: NewsItemLocation

    # --- only used for statistics_type None ---
    reach = ndb.IntegerProperty(indexed=False, default=0)
    rogered = ndb.BooleanProperty(indexed=True, required=True)
    users_that_rogered = ndb.UserProperty(indexed=False, repeated=True)  # type: list[users.User]
    statistics = NewsItemStatisticsProperty(indexed=False)
    follow_count = ndb.IntegerProperty(indexed=False, default=-1)
    action_count = ndb.IntegerProperty(indexed=False, default=-1)
    # --- end only used for statistics_type None ---
    buttons = NewsButtonsProperty(indexed=False)
    statistics_type = ndb.StringProperty(indexed=True, choices=[None, STATISTICS_TYPE_INFLUX_DB])
    qr_code_content = ndb.StringProperty(indexed=False)
    qr_code_caption = ndb.StringProperty(indexed=False)
    version = ndb.IntegerProperty(indexed=False, default=1)
    flags = ndb.IntegerProperty(indexed=False, default=0)
    silent = ndb.BooleanProperty(indexed=False, default=False)

    target_audience_enabled = ndb.BooleanProperty(indexed=False)
    target_audience_min_age = ndb.IntegerProperty(indexed=False, default=0)
    target_audience_max_age = ndb.IntegerProperty(indexed=False, default=200)
    target_audience_gender = ndb.IntegerProperty(indexed=False, default=0)
    connected_users_only = ndb.BooleanProperty(indexed=False)

    role_ids = ndb.IntegerProperty(indexed=False, repeated=True)

    tags = ndb.StringProperty(indexed=True, repeated=True)
    feeds = NewsFeedsProperty(indexed=False)
    media = ndb.StructuredProperty(NewsMedia)  # type: NewsMedia

    TYPE_NORMAL = 1  # application/service to person
    TYPE_QR_CODE = 2
    TYPES = (TYPE_QR_CODE, TYPE_NORMAL)

    FLAG_ACTION_ROGERTHAT = 1
    FLAG_ACTION_FOLLOW = 2
    FLAG_SILENT = 4
    DEFAULT_FLAGS = FLAG_ACTION_FOLLOW | FLAG_ACTION_ROGERTHAT

    MAX_BUTTON_COUNT = 3

    @property
    def id(self):
        return self.key.id()

    @property
    def sort_timestamp(self):
        r = max(self.sticky and self.sticky_until, self.order_timestamp) or 0
        return r

    @property
    def stream_publish_timestamp(self):
        if self.scheduled_at:
            return datetime.utcfromtimestamp(self.scheduled_at)
        return datetime.utcfromtimestamp(self.timestamp)

    @property
    def stream_sort_timestamp(self):
        if self.sticky:
            return datetime.utcfromtimestamp(self.sticky_until)
        return self.stream_publish_timestamp

    def sort_priority(self, connections, profile=None, users_that_rogered=None):

        if self.sticky:
            return 10

        if profile and not self.match_target_audience(profile):
            return 45

        if users_that_rogered and any(user_that_rogered in connections[0] for user_that_rogered in users_that_rogered):
            return 20

        if self.sender in connections[1]:
            return 30

        return 40

    def feed_name(self, app_id):
        feeds = self.feeds.values() if self.feeds else []
        for feed in feeds:
            if feed.app_id == app_id:
                return feed.name
        return None

    @property
    def target_audience(self):
        """Get the target audience as NewsTargetAudienceTO.

        Returns:
            NewsTargetAudienceTO
        """
        from rogerthat.to.news import NewsTargetAudienceTO

        target_audience = None
        if self.target_audience_enabled:
            target_audience = NewsTargetAudienceTO()
            target_audience.min_age = self.target_audience_min_age
            target_audience.max_age = self.target_audience_max_age
            target_audience.gender = self.target_audience_gender
            target_audience.connected_users_only = self.connected_users_only

        return target_audience

    def has_roles(self):
        """Check if a news item has any assinged roles."""
        return len(self.role_ids) > 0

    @staticmethod
    def match_target_audience_of_item(profile, news_item):
        """Check if the target audience of a news item include the user or not.

        Args:
            profile (UserProfile)
            news_item (NewsItem or NewsItemTO)

        Returns:
           bool
        """
        target_audience = news_item.target_audience
        if not target_audience:
            return True

        if profile.birthdate is None or not profile.gender >= 0:
            return False

        news_item_gender = target_audience.gender
        any_gender = (UserProfile.GENDER_MALE_OR_FEMALE, UserProfile.GENDER_CUSTOM)
        if news_item_gender not in any_gender:
            if profile.gender != news_item_gender:
                return False

        min_age = target_audience.min_age
        max_age = target_audience.max_age
        user_birthdate = date.fromtimestamp(profile.birthdate)
        user_age = calculate_age_from_date(user_birthdate)
        if not (min_age <= user_age <= max_age):
            return False

        return True

    def match_target_audience(self, profile):
        if not self.target_audience_enabled:
            return True
        return NewsItem.match_target_audience_of_item(profile, self)

    @classmethod
    def list_by_sender(cls, sender, updated_since=0, tag=None):
        qry = cls.query()
        qry = qry.filter(cls.deleted == False)
        if tag:
            qry = qry.filter(cls.tags == tag)
        qry = qry.filter(cls.sender == sender)
        if updated_since:
            qry = qry.filter(cls.update_timestamp >= updated_since)
            qry = qry.order(-cls.update_timestamp)
        else:
            qry = qry.order(-cls.published_timestamp)
        return qry

    @classmethod
    def list_by_app(cls, app_id, updated_since=0, tag=None):
        qry = cls.query()
        if tag:
            qry = qry.filter(cls.tags == tag)

        qry = qry.filter(cls.app_ids == app_id)
        qry = qry.filter(cls.deleted == False)
        qry = qry.filter(cls.published == True)
        qry = qry.filter(cls.update_timestamp >= updated_since)
        qry = qry.order(-cls.update_timestamp)
        return qry

    @classmethod
    def list_published_by_sender(cls, sender, app_id, keys_only=False):
        qry = cls.query(default_options=QueryOptions(keys_only=keys_only))
        qry = qry.filter(cls.published == True)
        qry = qry.filter(cls.deleted == False)
        qry = qry.filter(cls.sender == sender)
        qry = qry.filter(cls.app_ids == app_id)
        qry = qry.order(-cls.published_timestamp)
        return qry

    @classmethod
    def list_published_by_group_id(cls, group_id):
        qry = cls.query()
        qry = qry.filter(cls.published == True)
        qry = qry.filter(cls.group_ids == group_id)
        return qry

    def media_url(self, base_url):
        if base_url and self.media:
            if self.media.url:
                return self.media.url
            return u'%s/unauthenticated/news/image/%d' % (base_url, self.media.content)
        return None

    @classmethod
    def create_key(cls, news_id):
        return ndb.Key(cls, news_id)

    @classmethod
    def get_expired_sponsored_news_keys(cls):
        """
        Returns:
            keys (list of ndb.Key)
        """
        return cls.query().filter(cls.sticky == True).filter(cls.sticky_until < now())


class NewsItemImage(NdbModel):
    image = ndb.BlobProperty()

    @property
    def id(self):
        return self.key.id()

    @classmethod
    def create_key(cls, image_id):
        return ndb.Key(cls, image_id)


class NewsItemStatisticsExporter(NdbModel):
    exported_until = ndb.DateTimeProperty()

    @classmethod
    def create_key(cls, type_):
        return ndb.Key(cls, type_)


class NewsItemAction(Enum):
    REACHED = 'reached'
    ROGERED = 'rogered'
    UNROGERED = 'unrogered'
    FOLLOWED = 'followed'
    ACTION = 'action'
    PINNED = 'pinned'
    UNPINNED = 'unpinned'


class NewsItemActionStatistics(NdbModel):
    created = ndb.DateTimeProperty(auto_now_add=True)
    news_id = ndb.IntegerProperty()
    action = ndb.StringProperty()
    age = ndb.StringProperty()
    gender = ndb.StringProperty()

    @property
    def app_user(self):
        return users.User(self.key.parent().id().decode('utf8'))

    @classmethod
    def create_key(cls, app_user, uid):
        return ndb.Key(cls, uid, parent=parent_ndb_key(app_user))

    @classmethod
    def list_by_action(cls, news_id, action):
        return NewsItemActionStatistics.query()\
            .filter(NewsItemActionStatistics.news_id == news_id)\
            .filter(NewsItemActionStatistics.action == action)

    @classmethod
    def list_between(cls, start, end):
        return NewsItemActionStatistics.query()\
            .filter(NewsItemActionStatistics.created > start)\
            .filter(NewsItemActionStatistics.created <= end)


class NewsStreamLayout(NdbModel):
    group_types = ndb.StringProperty(indexed=False, repeated=True)


class NewsStream(NdbModel):
    TYPE_CITY = u'city'
    TYPE_COMMUNITY = u'community'

    stream_type = ndb.StringProperty(indexed=False, default=None)
    should_create_groups = ndb.BooleanProperty(indexed=False)
    services_need_setup = ndb.BooleanProperty(indexed=True, default=False)
    layout = ndb.LocalStructuredProperty(NewsStreamLayout, repeated=True)
    custom_layout_id = ndb.StringProperty(indexed=False, default=None)

    @property
    def app_id(self):
        return self.key.id().decode('utf8')

    @classmethod
    def create_key(cls, app_id):
        return ndb.Key(cls, app_id)


class NewsStreamCustomLayout(NdbModel):
    layout = ndb.LocalStructuredProperty(NewsStreamLayout, repeated=True)

    @property
    def app_id(self):
        return self.key.parent().id()

    @classmethod
    def create_key(cls, uid, app_id):
        return ndb.Key(cls, uid, parent=ndb.Key(cls, app_id))


class NewsGroupTile(NdbModel):
    background_image_url = ndb.StringProperty(indexed=False)
    promo_image_url = ndb.StringProperty(indexed=False)
    title = ndb.StringProperty(indexed=False)
    subtitle = ndb.StringProperty(indexed=False)


class NewsGroup(NdbModel):
    TYPE_CITY = 'city'
    TYPE_PROMOTIONS = 'promotions'
    TYPE_EVENTS = 'events'
    TYPE_TRAFFIC = 'traffic'
    TYPE_PRESS = 'press'
    TYPE_POLLS = 'polls'
    TYPE_PUBLIC_SERVICE_ANNOUNCEMENTS = 'public_service_announcements'

    FILTER_PROMOTIONS_FOOD = 'food'
    FILTER_PROMOTIONS_RESTAURANT = 'restaurant'
    FILTER_PROMOTIONS_CLOTHING = 'clothing'
    FILTER_PROMOTIONS_ASSOCIATIONS = 'associations'
    FILTER_PROMOTIONS_OTHER = 'other'
    PROMOTIONS_FILTERS = [
        FILTER_PROMOTIONS_FOOD,
        FILTER_PROMOTIONS_RESTAURANT,
        FILTER_PROMOTIONS_CLOTHING,
        FILTER_PROMOTIONS_ASSOCIATIONS,
        FILTER_PROMOTIONS_OTHER
    ]

    name = ndb.StringProperty(indexed=False)  # not visible to users/customers
    app_id = ndb.StringProperty()
    send_notifications = ndb.BooleanProperty(indexed=False, default=True)
    visible_until = ndb.DateTimeProperty(indexed=True)

    group_type = ndb.StringProperty()
    filters = ndb.StringProperty(repeated=True, indexed=False)
    regional = ndb.BooleanProperty(indexed=False)

    default_order = ndb.IntegerProperty(indexed=False)
    default_notifications_enabled = ndb.BooleanProperty(indexed=False)

    tile = ndb.LocalStructuredProperty(NewsGroupTile, repeated=False)

    service_filter = ndb.BooleanProperty(indexed=False, default=False)
    services = ndb.UserProperty(indexed=False, repeated=True)

    @property
    def group_id(self):
        return self.key.id().decode('utf8')

    @classmethod
    def create_key(cls, uid):
        return ndb.Key(cls, uid)

    @classmethod
    def list_by_app_id(cls, app_id):
        qry = cls.query()
        qry = qry.filter(cls.app_id == app_id)
        return qry

    @classmethod
    def list_by_visibility_date(cls, d):
        qry = cls.query()
        qry = qry.filter(cls.visible_until < d)
        qry = qry.filter(cls.visible_until != None)
        return qry


class NewsSettingsServiceGroup(NdbModel):
    group_type = ndb.StringProperty()
    filter = ndb.StringProperty()


class NewsSettingsService(NdbModel):
    # setup_needed_id
    # 1 to 10 need group_types
    # 11 to 20 need broadcast type mapping
    # 999 skipped

    default_app_id = ndb.StringProperty()
    setup_needed_id = ndb.IntegerProperty()
    groups = ndb.LocalStructuredProperty(NewsSettingsServiceGroup, repeated=True)
    duplicate_in_city_news = ndb.BooleanProperty(indexed=False, default=False)

    @property
    def service_user(self):
        return users.User(self.key.parent().id().decode('utf8'))

    @classmethod
    def create_key(cls, service_user):
        return ndb.Key(cls, service_user.email(), parent=parent_ndb_key(service_user, namespace=cls.NAMESPACE))

    @classmethod
    def list_by_app_id(cls, app_id):
        return cls.query().filter(cls.default_app_id == app_id)

    @classmethod
    def list_setup_needed(cls, app_id, sni):
        return cls.list_by_app_id(app_id).filter(cls.setup_needed_id == sni)

    def get_group(self, group_type):
        for g in self.groups:
            if g.group_type == group_type:
                return g
        return None

    def get_group_types(self):
        return [group.group_type for group in self.groups]


class NewsNotificationStatus(Enum):
    NOT_SET = -1
    DISABLED = 0
    ENABLED = 1


class NewsActionFlag(Enum):
    REACHED = 1 << 1
    ROGERED = 1 << 2
    FOLLOWED = 1 << 3
    ACTION = 1 << 4
    PINNED = 1 << 5


class NewsNotificationFilter(Enum):
    HIDDEN = -1
    NONE = 0
    ALL = 1
    SPECIFIED = 2


class NewsMatchType(Enum):
    NORMAL = 0
    LOCATION = 1


class NewsSettingsUserGroupDetails(NdbModel):
    group_id = ndb.StringProperty()
    order = ndb.IntegerProperty()
    filters = ndb.StringProperty(repeated=True)
    notifications = ndb.IntegerProperty()
    last_load_request = ndb.DateTimeProperty()


class NewsSettingsUserGroup(NdbModel):
    group_type = ndb.StringProperty()
    order = ndb.IntegerProperty()
    details = ndb.LocalStructuredProperty(NewsSettingsUserGroupDetails, repeated=True)  # type: list[NewsSettingsUserGroupDetails]

    def get_details_sorted(self):
        return sorted(self.details, key=lambda k: k.order)


class NewsSettingsUser(NdbModel):
    NOTIFICATION_ENABLED_FOR_NONE = u'none'
    NOTIFICATION_ENABLED_FOR_ALL = u'all'
    NOTIFICATION_ENABLED_FOR_SPECIFIED = u'specified'

    FILTER_MAPPING = {
        NOTIFICATION_ENABLED_FOR_NONE: NewsNotificationFilter.NONE,
        NOTIFICATION_ENABLED_FOR_ALL: NewsNotificationFilter.ALL,
        NOTIFICATION_ENABLED_FOR_SPECIFIED: NewsNotificationFilter.SPECIFIED,
    }

    app_id = ndb.StringProperty()
    last_get_groups_request = ndb.DateTimeProperty()
    group_ids = ndb.StringProperty(repeated=True)
    groups = ndb.LocalStructuredProperty(NewsSettingsUserGroup, repeated=True)

    @property
    def app_user(self):
        return users.User(self.key.parent().id().decode('utf8'))

    @classmethod
    def create_key(cls, app_user):
        return ndb.Key(cls, app_user.email(), parent=parent_ndb_key(app_user, namespace=cls.NAMESPACE))

    @classmethod
    def list_by_app_id(cls, app_id):
        return cls.query().filter(cls.app_id == app_id)

    @classmethod
    def list_by_group_id(cls, group_id):
        return cls.query().filter(cls.group_ids == group_id)

    def get_groups_sorted(self):
        return sorted(self.groups, key=lambda k: k.order)

    def get_group(self, group_id):
        # type: (str) -> NewsSettingsUserGroup
        for g in self.groups:
            for d in g.details:
                if d.group_id == group_id:
                    return g
        return None

    def get_group_details(self, group_id):
        # type: (str) -> NewsSettingsUserGroupDetails
        for g in self.groups:
            for d in g.details:
                if d.group_id == group_id:
                    return d
        return None


class NewsSettingsUserService(NdbModel):
    group_id = ndb.StringProperty()
    notifications = ndb.IntegerProperty()
    blocked = ndb.BooleanProperty()

    @classmethod
    def create_parent_key(cls, app_user, group_id):
        return ndb.Key(cls, group_id, parent=parent_ndb_key(app_user, namespace=cls.NAMESPACE))

    @classmethod
    def create_key(cls, app_user, group_id, service_identity_user):
        return ndb.Key(cls, service_identity_user.email(), parent=cls.create_parent_key(app_user, group_id))

    @classmethod
    def list_by_app_user(cls, app_user):
        return cls.query(ancestor=parent_ndb_key(app_user, namespace=cls.NAMESPACE))

    @classmethod
    def list_by_group_id(cls, app_user, group_id):
        return cls.query(ancestor=cls.create_parent_key(app_user, group_id))

    @classmethod
    def list_by_notification_status(cls, app_user, group_id, status):
        qry = cls.list_by_group_id(app_user, group_id)
        qry = qry.filter(cls.notifications == status)
        return qry

    @classmethod
    def list_blocked(cls, app_user, group_id):
        qry = cls.list_by_group_id(app_user, group_id)
        qry = qry.filter(cls.blocked == True)
        return qry


class NewsItemMatch(NdbModel):
    REASON_BLOCKED = u'blocked'
    REASON_FILTERED = u'filtered'
    REASON_DELETED = u'deleted'
    REASON_SERVICE_INVISIBLE = u'service_invisible'

    ACTION_FLAG_MAPPING = {
        NewsItemAction.REACHED: NewsActionFlag.REACHED,
        NewsItemAction.ROGERED: NewsActionFlag.ROGERED,
        NewsItemAction.FOLLOWED: NewsActionFlag.FOLLOWED,
        NewsItemAction.ACTION: NewsActionFlag.ACTION,
        NewsItemAction.PINNED: NewsActionFlag.PINNED,
    }

    update_time = ndb.DateTimeProperty(auto_now=True)
    update_time_blocked = ndb.DateTimeProperty(indexed=False, default=None)
    publish_time = ndb.DateTimeProperty(default=None)
    sort_time = ndb.DateTimeProperty()

    news_id = ndb.IntegerProperty()
    sender = ndb.UserProperty()  # service identity user
    group_ids = ndb.StringProperty(repeated=True)  # group_id can be None (service news, searching news)
    filter = ndb.StringProperty()
    location_match = ndb.BooleanProperty(indexed=False, default=False)

    actions = ndb.StringProperty(repeated=True)
    disabled = ndb.BooleanProperty(indexed=False)

    visible = ndb.BooleanProperty()
    invisible_reasons = ndb.StringProperty(repeated=True, indexed=False)

    @property
    def app_user(self):
        return users.User(self.key.parent().id().decode('utf8'))

    @property
    def action_flags(self):
        flags = 0
        for k, v in self.ACTION_FLAG_MAPPING.iteritems():
            if k in self.actions:
                flags |= v
        return flags

    @classmethod
    def create_key(cls, app_user, news_id):
        return ndb.Key(cls, news_id, parent=parent_ndb_key(app_user, namespace=cls.NAMESPACE))

    @classmethod
    def create(cls, app_user, news_id, publish_time, sort_time, sender, group_ids=None, filter_=None, location_match=False):
        return cls(key=cls.create_key(app_user, news_id),
                   publish_time=publish_time,
                   sort_time=sort_time,
                   news_id=news_id,
                   sender=sender,
                   group_ids=group_ids or [],
                   filter=filter_,
                   location_match=location_match,
                   actions=[],
                   disabled=False,
                   visible=True,
                   invisible_reasons=[])

    @classmethod
    def list_by_app_user(cls, app_user):
        return cls.query(ancestor=parent_ndb_key(app_user, namespace=cls.NAMESPACE))

    @classmethod
    def count_unread(cls, app_user, group_id, d, max_count=10):
        return cls.query(ancestor=parent_ndb_key(app_user, namespace=cls.NAMESPACE))\
            .filter(cls.group_ids == group_id)\
            .filter(cls.visible == True)\
            .filter(cls.publish_time > d)\
            .count_async(max_count)

    @classmethod
    def list_by_group_id(cls, app_user, group_id):
        return cls.query(ancestor=parent_ndb_key(app_user, namespace=cls.NAMESPACE))\
            .filter(cls.group_ids == group_id)

    @classmethod
    def list_visible_by_group_id(cls, app_user, group_id):
        return cls.list_by_group_id(app_user, group_id)\
            .filter(cls.visible == True)\
            .order(-NewsItemMatch.sort_time)

    @classmethod
    def list_by_sender(cls, app_user, sender, group_id):
        return cls.query(ancestor=parent_ndb_key(app_user, namespace=cls.NAMESPACE))\
            .filter(cls.sender == sender)\
            .filter(cls.group_ids == group_id)

    @classmethod
    def list_visible_by_sender_and_group_id(cls, app_user, sender, group_id):
        return cls.list_by_sender(app_user, sender, group_id)\
            .filter(cls.visible == True)\
            .order(-NewsItemMatch.sort_time)

    @classmethod
    def list_by_filter(cls, app_user, group_id, filter_):
        return cls.query(ancestor=parent_ndb_key(app_user, namespace=cls.NAMESPACE))\
            .filter(cls.group_ids == group_id)\
            .filter(cls.filter == filter_)

    @classmethod
    def list_by_action(cls, app_user, action):
        return cls.query(ancestor=parent_ndb_key(app_user, namespace=cls.NAMESPACE))\
            .filter(cls.actions == action)\
            .filter(cls.visible == True)\
            .order(-NewsItemMatch.update_time)

    @classmethod
    def list_by_news_id(cls, news_id):
        return cls.query().filter(cls.news_id == news_id)

    @classmethod
    def list_by_news_and_group_id(cls, news_id, group_id):
        return cls.query()\
            .filter(cls.news_id == news_id)\
            .filter(cls.group_ids == group_id)
