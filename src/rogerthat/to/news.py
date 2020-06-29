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

from datetime import datetime
import json
import time

from dateutil.relativedelta import relativedelta
from typing import List

from mcfw.properties import long_list_property, typed_property, bool_property, long_property, unicode_property, \
    unicode_list_property, azzert, float_property
from mcfw.serialization import s_long, ds_long, s_bool, s_unicode, ds_bool, ds_unicode, \
    get_list_serializer, get_list_deserializer
from rogerthat.dal.profile import get_user_profile
from rogerthat.models import UserProfile
from rogerthat.models.news import NewsItem, NewsNotificationStatus, NewsMatchType
from rogerthat.models.properties.news import NewsItemStatistics
from rogerthat.rpc import users
from rogerthat.to import BaseButtonTO, TO
from rogerthat.to import KeyValueLongTO
from rogerthat.utils.app import get_app_user_tuple, get_app_id_from_app_user
from rogerthat.utils.service import remove_slash_default


class NewsSenderTO(object):
    email = unicode_property('1')
    name = unicode_property('2')
    avatar_id = long_property('3')

    def __init__(self, email=None, name=None, avatar_id=None):
        self.email = email
        self.name = name
        self.avatar_id = avatar_id


def _serialize_news_sender(stream, sender):
    s_long(stream, 1)  # version
    s_unicode(stream, sender.email)
    s_unicode(stream, sender.name)
    s_long(stream, sender.avatar_id)


def _deserialize_news_sender(stream):
    _ = ds_long(stream)  # version
    sender = NewsSenderTO()
    sender.email = ds_unicode(stream)
    sender.name = ds_unicode(stream)
    sender.avatar_id = ds_long(stream)
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


class NewsItemStatisticsTimeTO(TO):
    timestamp = long_property('1')
    amount = long_property('2')

    def __init__(self, timestamp, amount):
        self.timestamp = timestamp
        self.amount = amount


class NewsItemStatisticsDetailsTO(TO):
    age = typed_property('1', KeyValueLongTO, True)  # key: age (e.g. 10 - 15), value: amount
    gender = typed_property('2', KeyValueLongTO, True)  # key: gender, value: amount
    time = typed_property('3', NewsItemStatisticsTimeTO, True)
    total = long_property('4')

    def __init__(self, age=None, gender=None, time=None, total=0):
        if age is None:
            age = []
        if gender is None:
            gender = []
        if time is None:
            time = []
        self.age = age
        self.gender = gender
        self.time = time
        self.total = total

    @classmethod
    def from_model(cls, model, news_type, news_item_creation_timestamp):
        """
        Args:
            model (NewsItemStatistics)
            news_type (unicode)
            news_item_creation_timestamp (long)
        """
        age = []
        gender = []
        time_to = []
        for i, _ in enumerate(NewsItemStatistics.default_age_stats()):
            start_age = i * 5
            end_age = start_age + 5
            age_label = u'%s - %s' % (start_age, end_age)
            age_value = getattr(model, '%s_age' % news_type)[i]
            age.append(KeyValueLongTO(age_label, age_value))
        for i, _ in enumerate(NewsItemStatistics.default_gender_stats()):
            gender_label = NewsItemStatistics.gender_translation_key(i)
            gender_value = getattr(model, '%s_gender' % news_type)[i]
            gender.append(KeyValueLongTO(gender_label, gender_value))
        time_values = getattr(model, '%s_time' % news_type, [])
        for hours_from_creation, time_value in enumerate(time_values):
            dt = datetime.utcfromtimestamp(news_item_creation_timestamp) + relativedelta(hours=hours_from_creation)
            timestamp = long(time.mktime(dt.utctimetuple()))
            time_to.append(NewsItemStatisticsTimeTO(timestamp, time_value))
        return cls(age, gender, time_to, getattr(model, '%s_total' % news_type))


class NewsItemAppStatisticsTO(TO):
    app_id = unicode_property('app_id')
    # following dicts could have type NewsItemStatisticsDetailsTO, but are dictionaries for enhanced performance
    reached = typed_property('2', dict, False)  # type: dict
    rogered = typed_property('3', dict, False)  # type: dict
    action = typed_property('4', dict, False)  # type: dict
    followed = typed_property('5', dict, False)  # type: dict

    @classmethod
    def from_model(cls, app_id, statistics, news_item_creation_timestamp):
        """
        Args:
            statistics (rogerthat.models.properties.news.NewsItemStatistics)
            news_item_creation_timestamp (long)
        """
        reached = NewsItemStatisticsDetailsTO.from_model(statistics, u'reached', news_item_creation_timestamp).to_dict()
        rogered = NewsItemStatisticsDetailsTO.from_model(statistics, u'rogered', news_item_creation_timestamp).to_dict()
        action = NewsItemStatisticsDetailsTO.from_model(statistics, u'action', news_item_creation_timestamp).to_dict()
        followed = NewsItemStatisticsDetailsTO.from_model(statistics, u'followed',
                                                          news_item_creation_timestamp).to_dict()
        return cls(app_id=app_id, reached=reached, rogered=rogered, action=action, followed=followed)


class NewsItemStatisticsTO(TO):
    id = long_property('id')
    users_that_rogered = unicode_list_property('users_that_rogered')
    total_reached = long_property('total_reached')
    total_action = long_property('total_action')
    total_followed = long_property('total_followed')
    details = typed_property('details', NewsItemAppStatisticsTO, True)  # type: List[NewsItemAppStatisticsTO]

    def __init__(self, id_=0, total_reached=0, users_that_rogered=None, total_action=0, total_followed=0, details=None):
        super(NewsItemStatisticsTO, self).__init__(
            id=id_,
            users_that_rogered=users_that_rogered or [],
            total_reached=total_reached,
            total_action=total_action,
            total_followed=total_followed,
            details=details or []
        )


class NewsStatisticsResultTO(TO):
    id = long_property('id')
    data = typed_property('data', NewsItemStatisticsTO)


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


class BaseNewsItemTO(object):
    id = long_property('1')
    sender = typed_property('2', NewsSenderTO, False)  # type: NewsSenderTO
    title = unicode_property('3')
    message = unicode_property('4')
    image_url = unicode_property('5', default=None)  # deprecated
    broadcast_type = unicode_property('6')  # deprecated
    buttons = typed_property('9', NewsActionButtonTO, True)
    qr_code_content = unicode_property('10')
    qr_code_caption = unicode_property('11')
    version = long_property('12')
    timestamp = long_property('13')
    flags = long_property('14')
    type = long_property('15')
    media = typed_property('media', MediaTO, False, default=None)  # type: MediaTO

    def __init__(self, news_id=0, sender_email=None, sender_name=None, sender_avatar_id=0, title=None,
                 message=None, image_url=None, buttons=None,
                 qr_code_content=None, qr_code_caption=None, version=0, timestamp=0, flags=0, news_type=1, media=None):
        if buttons is None:
            buttons = []
        self.id = news_id
        if sender_email:
            sender_email = remove_slash_default(users.User(sender_email)).email()
        self.sender = NewsSenderTO(sender_email, sender_name, sender_avatar_id)
        self.title = title
        self.message = message
        self.image_url = image_url
        self.broadcast_type = None
        self.buttons = [NewsActionButtonTO.from_model(button) for button in buttons]
        self.qr_code_content = qr_code_content
        self.qr_code_caption = qr_code_caption
        self.version = version
        self.timestamp = timestamp
        self.flags = flags
        self.type = news_type
        self.media = media

    @classmethod
    def from_model(cls, model, base_url):
        # type: (NewsItem, unicode) -> BaseNewsItemTO
        from rogerthat.dal.service import get_service_identity
        si = get_service_identity(model.sender)
        return cls(model.id, si.service_identity_user.email(), si.name, si.avatarId, model.title, model.message,
                   model.media_url(base_url), model.buttons, model.qr_code_content, model.qr_code_caption,
                   model.version, model.timestamp, model.flags, model.type, model.media)


class NewsItemTO(BaseNewsItemTO):
    TYPE_NORMAL = u'NORMAL'
    TYPE_QR_CODE = u'QR_CODE'

    TYPES = (TYPE_NORMAL, TYPE_QR_CODE)

    sticky = bool_property('101')
    sticky_until = long_property('102')
    app_ids = unicode_list_property('103')
    scheduled_at = long_property('105')
    published = bool_property('106')

    target_audience = typed_property('110', NewsTargetAudienceTO, False)
    role_ids = long_list_property('111', default=[])
    tags = unicode_list_property('112')
    group_type = unicode_property('114', default=None)
    locations = typed_property('locations', NewsLocationsTO)
    group_visible_until = long_property('group_visible_until')

    def __init__(self, news_id=0, sender_email=None, sender_name=None, sender_avatar_id=0, title=None,
                 message=None, image_url=None, buttons=None,
                 qr_code_content=None, qr_code_caption=None, version=0, timestamp=0, flags=0, news_type=1,
                 sticky=False, sticky_until=0, app_ids=None, scheduled_at=0, published=False,
                 target_audience=None, role_ids=None,
                 tags=None, media=None, group_type=None, locations=None, group_visible_until=None):

        if app_ids is None:
            app_ids = []
        if buttons is None:
            buttons = []
        if role_ids is None:
            role_ids = []
        if tags is None:
            tags = []

        super(NewsItemTO, self).__init__(news_id, sender_email, sender_name, sender_avatar_id, title,
                                         message, image_url, buttons,
                                         qr_code_content, qr_code_caption, version, timestamp, flags, news_type, media)

        self.sticky = sticky
        self.sticky_until = sticky_until
        self.app_ids = app_ids
        self.scheduled_at = scheduled_at
        if scheduled_at:
            self.timestamp = scheduled_at
        self.published = published

        self.target_audience = target_audience
        self.role_ids = role_ids
        self.tags = tags
        self.group_type = group_type
        self.locations = locations
        self.group_visible_until = group_visible_until

    def has_roles(self):
        """Check if this news item has any assigned roles."""
        return len(self.role_ids) > 0

    @classmethod
    def from_model(cls, model, base_url):
        # type: (NewsItem, unicode) -> NewsItemTO
        from rogerthat.dal.service import get_service_identity
        si = get_service_identity(model.sender)
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
        sender_name = si.name if si else u""
        sender_avatar_id = si.avatarId if si else -1
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
        return cls(model.id, sender_email, sender_name, sender_avatar_id, model.title, model.message,
                   media and media.content, buttons, model.qr_code_content, model.qr_code_caption, model.version,
                   model.timestamp, model.flags, model.type, model.sticky, model.sticky_until, model.app_ids,
                   model.scheduled_at, model.published, target_audience,
                   model.role_ids, model.tags, media, group_type, locations,
                   model.group_visible_until and long(time.mktime(model.group_visible_until.timetuple())))


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

    def __init__(self, news_items=None, more=True, cursor=None, base_url=None):
        # type: (list[NewsItem], bool, unicode, unicode) -> None
        if news_items is None:
            news_items = []
        self.cursor = cursor
        results = []
        for news_item in news_items:
            results.append(NewsItemTO.from_model(news_item, base_url))
        self.result = results
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
    filters = typed_property('4', NewsGroupFilterInfoTO, True, default=[])


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
    id = long_property('1')
    sender = typed_property('2', NewsSenderTO, False)
    title = unicode_property('3')
    message = unicode_property('4')
    media = typed_property('5', MediaTO, False)
    buttons = typed_property('6', NewsActionButtonTO, True)
    qr_code_content = unicode_property('7')
    qr_code_caption = unicode_property('8')
    flags = long_property('11')
    type = long_property('12')
    timestamp = long_property('13')
    actions = long_property('14')  # flags: NewsActionFlag
    disabled = bool_property('15')
    notifications = long_property('16')  # enum: NewsNotificationStatus
    blocked = bool_property('17')
    match_type = long_property('18')  # flags: NewsMatchType

    @classmethod
    def from_model(cls, app_user, news_match, news_item_to, notifications=NewsNotificationStatus.NOT_SET, blocked=False):
        to = cls()
        to.id = news_item_to.id
        to.sender = NewsSenderTO(news_item_to.sender.email, news_item_to.sender.name, news_item_to.sender.avatar_id)
        to.title = news_item_to.title
        to.message = news_item_to.message
        to.media = news_item_to.media
        to.buttons = news_item_to.buttons
        if news_item_to.qr_code_content:
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
        to.actions = news_match.action_flags if news_match else 0
        to.disabled = news_match.disabled if news_match else False
        to.notifications = notifications
        to.blocked = blocked
        if news_match:
            to.match_type = NewsMatchType.LOCATION if news_match.location_match else NewsMatchType.NORMAL
        else:
            to.match_type = NewsMatchType.NORMAL
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
    def from_news_model(cls, model, statistics=None):
        # type: (NewsItem, NewsItemStatisticsTO) -> NewsReadInfoTO
        if not statistics:
            statistics = NewsItemStatisticsTO(model.id)
        return cls(news_id=model.id,
                   app_ids=model.app_ids or [],
                   read_count=statistics.total_reached,
                   users_that_rogered=statistics.users_that_rogered)


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
