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
import time

from typing import List, Union

from mcfw.properties import long_list_property, typed_property, bool_property, long_property, unicode_property, \
    unicode_list_property, azzert, float_property
from mcfw.serialization import s_long, ds_long, s_bool, s_unicode, ds_bool, ds_unicode, \
    get_list_serializer, get_list_deserializer
from mcfw.utils import Enum
from rogerthat.models import UserProfile, ServiceIdentity, NdbServiceProfile, ServiceProfile
from rogerthat.models.news import NewsItem, NewsNotificationStatus, NewsMatchType, NewsGroup
from rogerthat.models.properties.news import NewsItemStatistics
from rogerthat.rpc import users
from rogerthat.to import BaseButtonTO, TO, KeyValueLongTO
from rogerthat.utils.service import remove_slash_default


class NewsStatisticAction(Enum):
    STATISTIC_REACH = 'news.reached'
    STATISTIC_ROGERED = 'news.rogered'
    STATISTIC_UNROGERED = 'news.unrogered'
    STATISTIC_FOLLOWED = 'news.followed'
    STATISTIC_ACTION = 'news.action'
    STATISTIC_PINNED = 'news.pinned'
    STATISTIC_UNPINNED = 'news.unpinned'
    STATISTIC_SHARE = 'news.share'


class NewsSenderTO(object):
    email = unicode_property('1')
    name = unicode_property('2')
    avatar_id = long_property('3')
    avatar_url = unicode_property('avatar_url', default=None)

    def __init__(self, email=None, name=None, avatar_id=None, avatar_url=None):
        self.email = email
        self.name = name
        self.avatar_id = avatar_id
        self.avatar_url = avatar_url

    @classmethod
    def from_service_models(cls, base_url, service_profile, si):
        # type: (str, NdbServiceProfile, ServiceIdentity) -> NewsSenderTO
        return cls(email=remove_slash_default(si.service_identity_user).email(),
                   name=si.name,
                   avatar_id=service_profile.avatarId,
                   avatar_url=service_profile.get_avatar_url(base_url))


def _serialize_news_sender(stream, sender):
    s_long(stream, 2)  # version
    s_unicode(stream, sender.email)
    s_unicode(stream, sender.name)
    s_long(stream, sender.avatar_id)
    s_unicode(stream, sender.avatar_url)


def _deserialize_news_sender(stream):
    version = ds_long(stream)  # version
    sender = NewsSenderTO()
    sender.email = ds_unicode(stream)
    sender.name = ds_unicode(stream)
    sender.avatar_id = ds_long(stream)
    if version > 1:
        sender.avatar_url = ds_unicode(stream)
    return sender


class NewsActionButtonTO(BaseButtonTO):
    flow_params = unicode_property('101')

    def __init__(self, id_=None, caption=None, action=None, flow_params=None):
        super(NewsActionButtonTO, self).__init__(id_, caption, action)
        self.flow_params = flow_params

    @classmethod
    def from_model(cls, model):
        return cls(model.id, model.caption, model.action, model.flow_params)


def _serialize_news_button(stream, b):
    s_unicode(stream, b.id)
    s_unicode(stream, b.caption)
    s_unicode(stream, b.action)
    s_unicode(stream, b.flow_params)


def _deserialize_news_button(stream, version):
    b = NewsActionButtonTO()
    b.id = ds_unicode(stream)
    b.caption = ds_unicode(stream)
    b.action = ds_unicode(stream)
    b.flow_params = ds_unicode(stream) if version > 1 else None
    return b

_serialize_news_button_list = get_list_serializer(_serialize_news_button)
_deserialize_news_button_list = get_list_deserializer(_deserialize_news_button, True)


def _serialize_news_buttons(stream, buttons):
    s_long(stream, 2)  # version
    _serialize_news_button_list(stream, buttons)


def _deserialize_news_buttons(stream):
    version = ds_long(stream)
    return _deserialize_news_button_list(stream, version)


class NewsItemBasicStatisticTO(TO):
    total = long_property('total')
    gender = typed_property('gender', KeyValueLongTO, True)  # type: List[KeyValueLongTO]
    age = typed_property('age', KeyValueLongTO, True)  # type: List[KeyValueLongTO]

    @classmethod
    def from_point(cls, stats, total_only=False):
        from rogerthat.bizz.news.influx import get_age_field_key
        gender_stats = []
        age_stats = []
        if not stats:
            total = 0
        else:
            total = stats['total']
            if not total_only:
                for label in NewsItemStatistics.get_gender_labels():
                    value = stats.get(label) or 0
                    gender_stats.append(KeyValueLongTO(key=label.replace('gender-', ''), value=value))
                for label in NewsItemStatistics.get_age_labels():
                    value = stats.get(get_age_field_key(label)) or 0
                    age_stats.append(KeyValueLongTO(key=label.replace('age-', ''), value=value))
        result = cls(total=total)
        if not total_only:
            result.gender = gender_stats
            result.age = age_stats
        return result


class NewsItemBasicStatisticsTO(TO):
    id = long_property('id')
    reached = typed_property('reached', NewsItemBasicStatisticTO)  # type: NewsItemBasicStatisticTO
    action = typed_property('action', NewsItemBasicStatisticTO)  # type: NewsItemBasicStatisticTO


class NewsItemStatisticApp(TO):
    app_id = unicode_property('app_id')
    stats = typed_property('stats', NewsItemBasicStatisticsTO)  # type: NewsItemBasicStatisticsTO


class NewsItemStatisticsPerApp(TO):
    id = long_property('id')
    results = typed_property('stats', NewsItemStatisticApp, True, default=[])  # type: List[NewsItemStatisticApp]


class NewsItemTimeValueTO(TO):
    time = unicode_property('time')
    value = long_property('value')


class NewsItemTimeStatisticsTO(TO):
    id = long_property('id')
    reached = typed_property('reached', NewsItemTimeValueTO, True)  # type: List[NewsItemTimeStatisticsTO]
    action = typed_property('action', NewsItemTimeValueTO, True)  # type: List[NewsItemTimeStatisticsTO]


class NewsTargetAudienceTO(object):
    min_age = long_property('1', default=0)
    max_age = long_property('2', default=200)
    gender = long_property('3', default=UserProfile.GENDER_MALE_OR_FEMALE)
    connected_users_only = bool_property('4', default=False)


class BaseMediaTO(TO):
    type = unicode_property('type')
    content = unicode_property('content')


class SizeTO(TO):
    width = long_property('width')
    height = long_property('height')


class MediaTO(BaseMediaTO, SizeTO):
    pass


class NewsGeoAddressTO(TO):
    distance = long_property('1')
    latitude = float_property('2')
    longitude = float_property('3')

    @classmethod
    def from_model(cls, model):
        return cls(distance=model.distance,
                   latitude=model.geo_location.lat,
                   longitude=model.geo_location.lon)


class NewsAddressTO(TO):
    level = unicode_property('2')
    country_code = unicode_property('3')
    city = unicode_property('4')
    zip_code = unicode_property('5')
    street_name = unicode_property('6')

    @classmethod
    def from_model(cls, address):
        return cls(level=address.level,
                   country_code=address.country_code,
                   city=address.city,
                   zip_code=address.zip_code,
                   street_name=address.street_name)


class NewsLocationsTO(TO):
    match_required = bool_property('1')
    geo_addresses = typed_property('2', NewsGeoAddressTO, True)  # type: list[NewsGeoAddressTO]
    addresses = typed_property('3', NewsAddressTO, True)  # type: list[NewsAddressTO]


class NewsItemTO(TO):
    TYPE_NORMAL = u'NORMAL'
    TYPE_QR_CODE = u'QR_CODE'

    TYPES = (TYPE_NORMAL, TYPE_QR_CODE)

    id = long_property('1')
    sender = typed_property('2', NewsSenderTO, False)  # type: NewsSenderTO
    title = unicode_property('3')
    message = unicode_property('4')
    image_url = unicode_property('5', default=None)  # deprecated
    buttons = typed_property('9', NewsActionButtonTO, True)
    qr_code_content = unicode_property('10')
    qr_code_caption = unicode_property('11')
    version = long_property('12')
    timestamp = long_property('13')
    flags = long_property('14')
    type = long_property('15')
    media = typed_property('media', MediaTO, False, default=None)  # type: MediaTO

    sticky = bool_property('101')
    sticky_until = long_property('102')
    community_ids = long_list_property('103')
    scheduled_at = long_property('105')
    published = bool_property('106')

    target_audience = typed_property('110', NewsTargetAudienceTO, False)
    group_type = unicode_property('114', default=None)
    locations = typed_property('locations', NewsLocationsTO)
    group_visible_until = long_property('group_visible_until')
    share_url = unicode_property('share_url', default=None)

    def __init__(self, news_id=0, sender_email=None, sender_name=None, sender_avatar_id=0, sender_avatar_url=None,
                 title=None, message=None, image_url=None, buttons=None,
                 qr_code_content=None, qr_code_caption=None, version=0, timestamp=0, flags=0, news_type=1,
                 sticky=False, sticky_until=0, community_ids=None, scheduled_at=0, published=False,
                 target_audience=None, media=None, group_type=None, locations=None, group_visible_until=None,
                 share_url=None):

        if community_ids is None:
            community_ids = []
        if buttons is None:
            buttons = []

        if buttons is None:
            buttons = []
        self.id = news_id
        if sender_email:
            sender_email = remove_slash_default(users.User(sender_email)).email()
        self.sender = NewsSenderTO(sender_email, sender_name, sender_avatar_id, sender_avatar_url)
        self.title = title
        self.message = message
        self.image_url = image_url
        self.buttons = [NewsActionButtonTO.from_model(button) for button in buttons]
        self.qr_code_content = qr_code_content
        self.qr_code_caption = qr_code_caption
        self.version = version
        self.timestamp = timestamp
        self.flags = flags
        self.type = news_type
        self.media = media
        self.sticky = sticky
        self.sticky_until = sticky_until
        self.community_ids = community_ids
        self.scheduled_at = scheduled_at
        if scheduled_at:
            self.timestamp = scheduled_at
        self.published = published

        self.target_audience = target_audience
        self.group_type = group_type
        self.locations = locations
        self.group_visible_until = group_visible_until
        self.share_url = share_url

    @classmethod
    def from_model(cls, model, base_url, service_profile, service_identity, share_url):
        # type: (NewsItem, unicode, Union[ServiceProfile, NdbServiceProfile], ServiceIdentity, unicode) -> NewsItemTO
        buttons = model.buttons.values() if model.buttons else []

        # set the target audience
        if model.target_audience_enabled:
            target_audience = NewsTargetAudienceTO()
            target_audience.min_age = model.target_audience_min_age
            target_audience.max_age = model.target_audience_max_age
            target_audience.gender = model.target_audience_gender
            target_audience.connected_users_only = model.connected_users_only
        else:
            target_audience = None
        sender_email = model.sender.email()
        sender_name = service_identity.name
        sender_avatar_id = service_profile.avatarId
        sender_avatar_url = service_profile.get_avatar_url(base_url)
        if model.media:
            media = MediaTO(type=model.media.type, width=model.media.width, height=model.media.height,
                            content=model.media_url(base_url))
        else:
            media = None
        group_type = None
        if model.group_types:
            for gt in model.group_types:
                group_type = gt
                break
        if model.locations:
            locations = NewsLocationsTO(match_required=model.location_match_required,
                                        addresses=[NewsAddressTO.from_model(address)
                                                   for address in model.locations.addresses],
                                        geo_addresses=[NewsGeoAddressTO.from_model(geo_address)
                                                       for geo_address in model.locations.geo_addresses])
        else:
            locations = None
        return cls(model.id, sender_email, sender_name, sender_avatar_id, sender_avatar_url, model.title, model.message,
                   media and media.content, buttons, model.qr_code_content, model.qr_code_caption, model.version,
                   model.timestamp, model.flags, model.type, model.sticky, model.sticky_until, model.community_ids,
                   model.scheduled_at, model.published, target_audience, media, group_type, locations,
                   model.group_visible_until and long(time.mktime(model.group_visible_until.timetuple())),
                   share_url)


def _serialize_news_target_audience(stream, target_audience, version):
    if target_audience:
        s_bool(stream, True)
        s_long(stream, target_audience.min_age)
        s_long(stream, target_audience.max_age)
        s_long(stream, target_audience.gender)
        if version >= 6:
            s_bool(stream, target_audience.connected_users_only)
    else:
        s_bool(stream, False)


def _deserialize_news_target_audience(stream, version):
    target_audience = None

    if ds_bool(stream):  # target audience enabled
        target_audience = NewsTargetAudienceTO()
        target_audience.min_age = ds_long(stream)
        target_audience.max_age = ds_long(stream)
        target_audience.gender = ds_long(stream)
        if version >= 6:
            target_audience.connected_users_only = ds_bool(stream)
    return target_audience


class NewsItemListResultTO(object):
    result = typed_property('1', NewsItemTO, True)
    cursor = unicode_property('2')
    more = bool_property('more')

    def __init__(self, news_items=None, more=True, cursor=None, base_url=None, service_profile=None,
                 service_identity=None, share_base_url=None):
        # type: (list[NewsItem], bool, unicode, unicode, NdbServiceProfile, ServiceIdentity) -> None
        from rogerthat.bizz.news import get_news_share_url
        if news_items is None:
            news_items = []
        self.cursor = cursor

        self.result = []
        for news_item in news_items:
            share_url = get_news_share_url(share_base_url, news_item.id)
            self.result.append(NewsItemTO.from_model(news_item, base_url, service_profile, service_identity, share_url=share_url))
        self.more = more


class DisableNewsRequestTO(object):
    news_id = long_property('1')

    def __init__(self, news_id=None):
        self.news_id = news_id


class DisableNewsResponseTO(object):
    pass


class SaveNewsStatisticsRequestTO(object):
    news_ids = long_list_property('1')
    type = unicode_property('2')


class SaveNewsStatisticsResponseTO(object):
    pass


class IfEmtpyScreenTO(TO):
    title = unicode_property('1')
    message = unicode_property('2')


class NewsGroupFilterInfoTO(TO):
    key = unicode_property('1')
    name = unicode_property('2')
    enabled = bool_property('3')


class NewsGroupTabInfoTO(TO):
    key = unicode_property('1')
    name = unicode_property('2')
    notifications = long_property('3')  # enum: NewsNotificationFilter


class NewsGroupLayoutTO(TO):
    badge_count = long_property('1', default=0)
    background_image_url = unicode_property('2', default=None)
    promo_image_url = unicode_property('3', default=None)
    title = unicode_property('4', default=None)
    subtitle = unicode_property('5', default=None)


class NewsGroupTO(TO):
    key = unicode_property('1')
    name = unicode_property('2')
    if_empty = typed_property('3', IfEmtpyScreenTO, False)
    tabs = typed_property('4', NewsGroupTabInfoTO, True, default=[])
    layout = typed_property('5', NewsGroupLayoutTO, False)
    services = typed_property('6', NewsSenderTO, True, default=[])


class NewsGroupRowTO(TO):
    items = typed_property('1', NewsGroupTO, True)


class GetNewsGroupsRequestTO(TO):
    pass


class GetNewsGroupRequestTO(TO):
    group_id = unicode_property('group_id', default=None)


class GetNewsGroupResponseTO(TO):
    group = typed_property('group', NewsGroupTO, default=None)


class GetNewsGroupsResponseTO(TO):
    rows = typed_property('1', NewsGroupRowTO, True)
    if_empty = typed_property('2', IfEmtpyScreenTO, False)
    has_locations = bool_property('3', default=False)


class GetNewsStreamFilterTO(TO):
    group_id = unicode_property('group_id', default=None)
    group_type = unicode_property('group_type', default=None)
    service_identity_email = unicode_property('service_identity_email', default=None)
    search_string = unicode_property('search_string', default=None)


class NewsStreamItemTO(TO):
    id = long_property('id')
    sender = typed_property('sender', NewsSenderTO, False)
    title = unicode_property('title')
    message = unicode_property('message')
    media = typed_property('media', MediaTO, False)
    buttons = typed_property('buttons', NewsActionButtonTO, True)
    qr_code_content = unicode_property('qr_code_content')
    qr_code_caption = unicode_property('qr_code_caption')
    flags = long_property('flags')
    type = long_property('type')
    timestamp = long_property('timestamp')
    actions = long_property('actions')  # flags: NewsActionFlag
    disabled = bool_property('disabled')
    notifications = long_property('notifications')  # enum: NewsNotificationStatus
    # unused, but can't be removed because old clients still expect this property
    blocked = bool_property('blocked', default=False)
    match_type = long_property('match_type')  # flags: NewsMatchType
    share_url = unicode_property('share_url', default=None)

    @classmethod
    def from_model(cls, app_user, news_item_actions, news_item_to, notifications=NewsNotificationStatus.NOT_SET, match_type=NewsMatchType.NORMAL):
        to = cls()
        to.id = news_item_to.id
        to.sender = news_item_to.sender
        to.title = news_item_to.title
        to.message = news_item_to.message
        to.media = news_item_to.media
        to.buttons = news_item_to.buttons
        if news_item_to.qr_code_content and app_user:
            try:
                content = json.loads(news_item_to.qr_code_content)
                content['u'] = app_user.email()
                to.qr_code_content = u'%s' % json.dumps(content)
            except:
                to.qr_code_content = news_item_to.qr_code_content
        else:
            to.qr_code_content = news_item_to.qr_code_content
        to.qr_code_caption = news_item_to.qr_code_caption
        to.flags = news_item_to.flags
        to.type = news_item_to.type
        to.timestamp = news_item_to.timestamp
        to.actions = news_item_actions.action_flags if news_item_actions else 0
        to.disabled = news_item_actions.disabled if news_item_actions else False
        to.notifications = notifications
        to.blocked = False
        to.match_type = match_type
        to.share_url = news_item_to.share_url
        return to


class GetNewsStreamItemsRequestTO(TO):
    filter = typed_property('1', GetNewsStreamFilterTO, False)
    cursor = unicode_property('2', default=None)
    news_ids = long_list_property('3', default=[])


class GetNewsStreamItemsResponseTO(TO):
    group_id = unicode_property('group_id', default=None)
    cursor = unicode_property('cursor')
    items = typed_property('items', NewsStreamItemTO, True)


class GetNewsGroupServicesRequestTO(TO):
    group_id = unicode_property('1')
    key = unicode_property('2')
    cursor = unicode_property('3', default=None)


class GetNewsGroupServicesResponseTO(TO):
    cursor = unicode_property('1')
    services = typed_property('2', NewsSenderTO, True)


class SaveNewsGroupServicesRequestTO(TO):
    group_id = unicode_property('1')
    key = unicode_property('2')
    action = unicode_property('3')
    service = unicode_property('4')


class SaveNewsGroupServicesResponseTO(TO):
    pass


class SaveNewsGroupFiltersRequestTO(TO):
    group_id = unicode_property('1')
    enabled_filters = unicode_list_property('2')


class SaveNewsGroupFiltersResponseTO(TO):
    pass


class GetNewsItemDetailsRequestTO(TO):
    id = long_property('id')


class GetNewsItemDetailsResponseTO(TO):
    item = typed_property('item', NewsStreamItemTO)  # type: NewsStreamItemTO


class CreateNotificationGroupTO(TO):
    id = unicode_property('1', default=None)
    name = unicode_property('2', default=None)


class CreateNotificationRequestTO(TO):
    pass


class CreateNotificationResponseTO(TO):
    pass


class UpdateBadgeCountRequestTO(TO):
    group_id = unicode_property('1')
    group_type = unicode_property('2')
    badge_count = long_property('3')


class UpdateBadgeCountResponseTO(TO):
    pass


class NewsReadInfoTO(TO):
    news_id = long_property('1')
    app_ids = unicode_list_property('2')
    read_count = long_property('3')
    users_that_rogered = unicode_list_property('4')

    @classmethod
    def from_news_model(cls, model):
        # type: (NewsItem) -> NewsReadInfoTO
        return cls(news_id=model.id,
                   app_ids=model.app_ids or [],
                   read_count=0,
                   users_that_rogered=[])


class NewsMobileConfigTO(object):
    ip = unicode_property('1')
    port = long_property('2')

    @classmethod
    def from_string(cls, settings_string):
        to = cls()
        parts = settings_string.split(":")
        part_ip = [int(p) for p in parts[0].split('.')]
        azzert(len(part_ip) == 4)
        to.ip = parts[0].decode('unicode-escape')
        to.port = int(parts[1])
        return to


class ServiceNewsGroupTO(TO):
    group_type = unicode_property('1')
    name = unicode_property('2')


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


class NewsGroupConfigTO(TO):
    group_id = unicode_property('group_id')
    name = unicode_property('name')
    send_notifications = bool_property('send_notifications')
    default_notifications_enabled = bool_property('default_notifications_enabled')
    group_type = unicode_property('group_type')
    tile = typed_property('tile', NewsGroupTileTO, False)

    @classmethod
    def from_model(cls, model):
        # type: (NewsGroup) -> NewsGroupConfigTO
        return cls.from_dict(model.to_dict(extra_properties=['group_id']))


class NewsSettingsTO(TO):
    stream_type = unicode_property('stream_type')


class NewsSettingsWithGroupsTO(NewsSettingsTO):
    groups = typed_property('1', NewsGroupConfigTO, True)
