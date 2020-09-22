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

from __future__ import unicode_literals

from datetime import datetime

from dateutil.relativedelta import relativedelta
from google.appengine.ext import ndb
from google.appengine.ext.ndb.query import QueryOptions
from typing import List

from mcfw.utils import Enum
from rogerthat.dal import parent_ndb_key
from rogerthat.models.common import NdbModel
from rogerthat.models.properties.news import NewsButtonsProperty
from rogerthat.rpc import users
from rogerthat.utils import now
from rogerthat.utils.app import get_app_id_from_app_user
from rogerthat.web_client.models import WebClientSession


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
    STATUS_SCHEDULED = u'scheduled'
    STATUS_PUBLISHED = u'published'
    STATUS_INVISIBLE = u'invisible'
    STATUS_DELETED = u'deleted'

    MAX_TITLE_LENGTH = 80
    MAX_BUTTON_CAPTION_LENGTH = 15

    # todo ruben news item
    # delete properties? -> sticky/sticky_until/tags (already removed) statistics/statistics_type/rogered/reach/action_count/feeds/follow_count/image_id/users_that_rogered/broadcast_type
    # unindex -> has_locations/location_match_required/locations/media

    # add status to qry -> scheduled/published/deleted
    # it needs to be published & not deleted
    # if deleting published should stay as well
    #
    # check needed -> timestamp/update_timestamp/order_timestamp/published_timestamp (unindexed) scheduled_at

    # migrate to ndb propery -> buttons

    # badge count -> just the 10 items of the news group and count those who are later then the last view time
    # but lets do it 1 time globally and then run a job

    # location matched only apply for the main list (not when listing items of 1 service or when searching)

    sticky = ndb.BooleanProperty(indexed=True, required=True)
    sticky_until = ndb.IntegerProperty(indexed=True, default=0)

    sender = ndb.UserProperty(indexed=True, required=True)  # service identity user
    app_ids = ndb.StringProperty(indexed=True, repeated=True)
    community_ids = ndb.IntegerProperty(repeated=True)  # type: List[long] # todo communities
    timestamp = ndb.IntegerProperty(indexed=True, required=True)  # type: long
    update_timestamp = ndb.IntegerProperty(indexed=True, default=0)
    order_timestamp = ndb.IntegerProperty(indexed=True, default=0)
    scheduled_at = ndb.IntegerProperty(indexed=False, default=0)
    scheduled_task_name = ndb.StringProperty(indexed=False)
    published_timestamp = ndb.IntegerProperty(indexed=True, default=0)
    published = ndb.BooleanProperty(default=False)
    deleted = ndb.BooleanProperty(default=False)

    status = ndb.StringProperty(indexed=True)

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

    buttons = NewsButtonsProperty(indexed=False)
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

    @classmethod
    def list_by_sender(cls, sender):
        qry = cls.query()
        qry = qry.filter(cls.deleted == False)
        qry = qry.filter(cls.sender == sender)
        qry = qry.order(-cls.published_timestamp)
        return qry

    @classmethod
    def list_published_by_sender(cls, sender, app_id, keys_only=False):
        qry = cls.query(default_options=QueryOptions(keys_only=keys_only))
        qry = qry.filter(cls.status == cls.STATUS_PUBLISHED)
        qry = qry.filter(cls.sender == sender)
        qry = qry.filter(cls.app_ids == app_id)
        qry = qry.order(-cls.published_timestamp)
        return qry

    @classmethod
    def list_published_by_group_id_sorted(cls, group_id):
        qry = cls.query()
        qry = qry.filter(cls.status == cls.STATUS_PUBLISHED)
        qry = qry.filter(cls.group_ids == group_id)
        qry = qry.order(-cls.published_timestamp)
        return qry

    @classmethod
    def list_published_by_sender_and_group_id_sorted(cls, sender, group_id, keys_only=False):
        qry = cls.query(default_options=QueryOptions(keys_only=keys_only))
        qry = qry.filter(cls.status == cls.STATUS_PUBLISHED)
        qry = qry.filter(cls.sender == sender)
        qry = qry.filter(cls.group_ids == group_id)
        qry = qry.order(-cls.published_timestamp)
        return qry

    @classmethod
    def count_unread(cls, group_id, min_time, max_count=10):
        qry = cls.query()
        qry = qry.filter(cls.status == cls.STATUS_PUBLISHED)
        qry = qry.filter(cls.group_ids == group_id)
        qry = qry.filter(cls.published_timestamp > min_time)
        return qry.count_async(max_count)

    @classmethod
    def get_expired_sponsored_news_keys(cls):
        # type: () -> ndb.Query
        return cls.query().filter(cls.sticky == True).filter(cls.sticky_until < now())

    def media_url(self, base_url):
        if base_url and self.media:
            if self.media.url:
                return self.media.url
            return u'%s/unauthenticated/news/image/%d' % (base_url, self.media.content)
        return None

    @classmethod
    def create_key(cls, news_id):
        return ndb.Key(cls, news_id)


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
    SHARE = 'share'


MAX_ACTION_COUNT_MAP = {
    NewsItemAction.REACHED: 1,
    NewsItemAction.ROGERED: 5,
    NewsItemAction.UNROGERED: 5,
    NewsItemAction.FOLLOWED: 1,
    NewsItemAction.ACTION: 5,
    NewsItemAction.PINNED: 5,
    NewsItemAction.UNPINNED: 5,
}


class NewsItemWebActionHistory(NdbModel):
    action = ndb.StringProperty(indexed=False, choices=NewsItemAction.all())
    date = ndb.DateTimeProperty(auto_now_add=True, indexed=False)


class NewsItemWebActions(NdbModel):
    actions = ndb.StructuredProperty(NewsItemWebActionHistory, indexed=False, repeated=True)  # type: List[NewsItemWebActionHistory]

    @classmethod
    def create_key(cls, session_key, news_id):
        return ndb.Key(cls, news_id, parent=session_key)

    def can_save_action(self, action, date):
        action_count = sum(1 for a in self.actions if a.action == action)
        max_count = MAX_ACTION_COUNT_MAP.get(action, 5)
        # Limit amount of actions to a certain amount to avoid abuse
        can_save = action_count < max_count
        if can_save:
            # Limit same action to once every 5 seconds, also to avoid abuse / double clicks
            acceptable_date = date - relativedelta(seconds=5)
            for a in reversed(self.actions):
                if a.action == action:
                    can_save = a.date < acceptable_date
                    break
        return can_save

    def add_action(self, action, date):
        can_save = self.can_save_action(action, date)
        if can_save:
            self.actions.append(NewsItemWebActionHistory(action=action, date=date))
        return can_save


class NewsItemActionStatistics(NdbModel):
    created = ndb.DateTimeProperty(auto_now_add=True)
    news_id = ndb.IntegerProperty()
    action = ndb.StringProperty()
    age = ndb.StringProperty(indexed=False) # if empty, it's a web user
    gender = ndb.StringProperty(indexed=False) # if empty, it's a web user
    app_id = ndb.StringProperty(indexed=False)  # if empty, parent key is always an app user

    def get_app_id(self):
        return self.app_id if self.app_id else get_app_id_from_app_user(self.app_user)

    @property
    def app_user(self):
        if self.key.parent().kind() == WebClientSession._get_kind():
            return None
        return users.User(self.key.parent().id().decode('utf8'))

    @classmethod
    def create_key(cls, app_user_or_session_key, uid):
        if isinstance(app_user_or_session_key, users.User):
            return ndb.Key(cls, uid, parent=parent_ndb_key(app_user_or_session_key))
        return ndb.Key(cls, uid, parent=app_user_or_session_key)

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

    name = ndb.StringProperty(indexed=False)  # not visible to users/customers
    app_id = ndb.StringProperty()
    community_id = ndb.IntegerProperty() # todo communities
    send_notifications = ndb.BooleanProperty(indexed=False, default=True)
    visible_until = ndb.DateTimeProperty(indexed=True)

    group_type = ndb.StringProperty()
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


class NewsSettingsService(NdbModel):
    # setup_needed_id
    # 1 to 10 need group_types
    # 11 to 20 need broadcast type mapping
    # 999 skipped

    default_app_id = ndb.StringProperty()
    community_id = ndb.IntegerProperty() # todo communities
    setup_needed_id = ndb.IntegerProperty()
    groups = ndb.LocalStructuredProperty(NewsSettingsServiceGroup, repeated=True)  # type: List[NewsSettingsServiceGroup]
    duplicate_in_city_news = ndb.BooleanProperty(indexed=False, default=False)  # type: bool

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
    NO_MATCH = -1
    NORMAL = 0
    LOCATION = 1


class NewsSettingsUserGroupDetails(NdbModel):
    group_id = ndb.StringProperty()
    order = ndb.IntegerProperty()
    notifications = ndb.IntegerProperty()
    last_load_request = ndb.DateTimeProperty()


class NewsSettingsUserGroup(NdbModel):
    group_type = ndb.StringProperty(required=True)
    order = ndb.IntegerProperty(required=True)
    details = ndb.LocalStructuredProperty(NewsSettingsUserGroupDetails,
                                          repeated=True)  # type: List[NewsSettingsUserGroupDetails]

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
    group_ids = ndb.StringProperty(repeated=True)  # type: List[str]
    groups = ndb.LocalStructuredProperty(NewsSettingsUserGroup, repeated=True)  # type: List[NewsSettingsUserGroup]

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


ACTION_FLAG_MAPPING = {
    NewsItemAction.REACHED: NewsActionFlag.REACHED,
    NewsItemAction.ROGERED: NewsActionFlag.ROGERED,
    NewsItemAction.FOLLOWED: NewsActionFlag.FOLLOWED,
    NewsItemAction.ACTION: NewsActionFlag.ACTION,
    NewsItemAction.PINNED: NewsActionFlag.PINNED,
}


class NewsItemActions(NdbModel):
    news_id = ndb.IntegerProperty()

    pinned_time = ndb.DateTimeProperty()

    actions = ndb.StringProperty(repeated=True)
    disabled = ndb.BooleanProperty(indexed=False)

    @property
    def app_user(self):
        return users.User(self.key.parent().id().decode('utf8'))

    @property
    def action_flags(self):
        flags = 0
        for k, v in ACTION_FLAG_MAPPING.iteritems():
            if k in self.actions:
                flags |= v
        return flags

    @classmethod
    def create_key(cls, app_user, news_id):
        return ndb.Key(cls, news_id, parent=parent_ndb_key(app_user, namespace=cls.NAMESPACE))

    @classmethod
    def create(cls, app_user, news_id):
        return cls(key=cls.create_key(app_user, news_id),
                   news_id=news_id,
                   pinned_time=None,
                   actions=[],
                   disabled=False)

    @classmethod
    def list_by_app_user(cls, app_user):
        return cls.query(ancestor=parent_ndb_key(app_user, namespace=cls.NAMESPACE))

    @classmethod
    def list_by_action(cls, app_user, action):
        return cls.query(ancestor=parent_ndb_key(app_user, namespace=cls.NAMESPACE))\
            .filter(cls.actions == action)

    @classmethod
    def list_pinned(cls, app_user):
        return cls.query(ancestor=parent_ndb_key(app_user, namespace=cls.NAMESPACE))\
            .filter(cls.actions == NewsItemAction.PINNED)\
            .order(-NewsItemActions.pinned_time)

    def add_action(self, action, action_time):
        if action not in self.actions:
            self.actions.append(action)
        if action == NewsItemAction.PINNED:
            self.pinned_time = action_time

    def remove_action(self, action):
        if action in self.actions:
            self.actions.remove(action)
        if action == NewsItemAction.PINNED:
            self.pinned_time = None


class NewsItemMatch(NdbModel): # todo ruben nuke this and use NewsItemActions instead
    REASON_BLOCKED = u'blocked'
    REASON_FILTERED = u'filtered'
    REASON_DELETED = u'deleted'
    REASON_SERVICE_INVISIBLE = u'service_invisible'

    update_time = ndb.DateTimeProperty(auto_now=True)
    news_id = ndb.IntegerProperty()
    location_match = ndb.BooleanProperty(indexed=False, default=False)
    actions = ndb.StringProperty(repeated=True)  # type: List[str]
    disabled = ndb.BooleanProperty(indexed=False)

    # delete properties below this

    publish_time = ndb.DateTimeProperty(default=None)
    sort_time = ndb.DateTimeProperty()

    sender = ndb.UserProperty()  # service identity user
    group_ids = ndb.StringProperty(repeated=True)  # group_id can be None (service news, searching news)

    visible = ndb.BooleanProperty()
    invisible_reasons = ndb.StringProperty(repeated=True, indexed=False)

    @property
    def app_user(self):
        return users.User(self.key.parent().id().decode('utf8'))

    @property
    def action_flags(self):
        flags = 0
        for k, v in ACTION_FLAG_MAPPING.iteritems():
            if k in self.actions:
                flags |= v
        return flags

    @classmethod
    def create_key(cls, app_user, news_id):
        return ndb.Key(cls, news_id, parent=parent_ndb_key(app_user, namespace=cls.NAMESPACE))

    @classmethod
    def create(cls, app_user, news_id, publish_time, sort_time, sender, group_ids=None, location_match=False):
        return cls(key=cls.create_key(app_user, news_id),
                   publish_time=publish_time,
                   sort_time=sort_time,
                   news_id=news_id,
                   sender=sender,
                   group_ids=group_ids or [],
                   location_match=location_match,
                   actions=[],
                   disabled=False,
                   visible=True,
                   invisible_reasons=[])

    @classmethod
    def list_by_app_user(cls, app_user):
        return cls.query(ancestor=parent_ndb_key(app_user, namespace=cls.NAMESPACE))

#     @classmethod
#     def count_unread(cls, app_user, group_id, d, max_count=10):
#         return cls.query(ancestor=parent_ndb_key(app_user, namespace=cls.NAMESPACE))\
#             .filter(cls.group_ids == group_id)\
#             .filter(cls.visible == True)\
#             .filter(cls.publish_time > d)\
#             .count_async(max_count)
#
#     @classmethod
#     def list_by_group_id(cls, app_user, group_id):
#         return cls.query(ancestor=parent_ndb_key(app_user, namespace=cls.NAMESPACE))\
#             .filter(cls.group_ids == group_id)
#
#     @classmethod
#     def list_visible_by_group_id(cls, app_user, group_id):
#         return cls.list_by_group_id(app_user, group_id)\
#             .filter(cls.visible == True)\
#             .order(-NewsItemMatch.sort_time)
#
#     @classmethod
#     def list_by_sender(cls, app_user, sender, group_id):
#         return cls.query(ancestor=parent_ndb_key(app_user, namespace=cls.NAMESPACE))\
#             .filter(cls.sender == sender)\
#             .filter(cls.group_ids == group_id)
#
#     @classmethod
#     def list_visible_by_sender_and_group_id(cls, app_user, sender, group_id):
#         return cls.list_by_sender(app_user, sender, group_id)\
#             .filter(cls.visible == True)\
#             .order(-NewsItemMatch.sort_time)

    @classmethod
    def list_by_action(cls, app_user, action):
        return cls.query(ancestor=parent_ndb_key(app_user, namespace=cls.NAMESPACE))\
            .filter(cls.actions == action)\
            .filter(cls.visible == True)\
            .order(-NewsItemMatch.update_time)

#     @classmethod
#     def list_by_news_id(cls, news_id):
#         return cls.query().filter(cls.news_id == news_id)
#
#     @classmethod
#     def list_by_news_and_group_id(cls, news_id, group_id):
#         return cls.query()\
#             .filter(cls.news_id == news_id)\
#             .filter(cls.group_ids == group_id)
