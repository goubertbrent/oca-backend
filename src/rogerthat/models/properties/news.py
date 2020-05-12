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

from collections import defaultdict
from contextlib import closing
import logging

from google.appengine.ext import db, ndb
from mcfw.properties import long_list_property, long_property, unicode_property, azzert
from mcfw.serialization import s_long, ds_long_list, s_long_list, ds_long, s_unicode, ds_unicode, get_list_serializer, \
    get_list_deserializer
from mcfw.utils import convert_to_str
from rogerthat.models import UserProfile
from rogerthat.models.properties.messaging import SpecializedList, DuplicateButtonIdException, \
    DuplicateAppIdException


try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class NewsStatisticPerApp(object):

    def set_data(self, stream):
        self._stream = stream

    def _setup(self):
        if self._initialized:
            return

        if not self._stream:
            raise Exception("NewsStatisticPerApp not ready, but setup was called.")

        self._data = defaultdict(NewsItemStatistics)
        ds_long(self._stream)  # version
        for _ in xrange(ds_long(self._stream)):
            app_id = ds_unicode(self._stream)
            self._data[app_id] = _deserialize_news_item_statistics(self._stream)

        self._initialized = True

    def __init__(self):
        self._initialized = False
        self._stream = None
        self._data = None

    def get(self, key, default=None):
        if not (self._initialized or self._stream):
            return default
        self._setup()
        return self._data.get(key, default)

    def __getitem__(self, key):
        if not (self._initialized or self._stream):
            return None
        self._setup()
        return self._data.get(key)

    def __setitem__(self, key, value):
        if not (self._initialized or self._stream):
            self._data = defaultdict(NewsItemStatistics)
            self._initialized = True
        self._setup()
        self._data[key] = value

    def iterkeys(self):
        self._setup()
        return self._data.iterkeys()

    def iteritems(self):
        self._setup()
        return self._data.iteritems()

    def __iter__(self):
        self._setup()
        for val in self._data.values():
            yield val

    def keys(self):
        self._setup()
        return self._data.keys()

    def has_key(self, key):
        self._setup()
        return key in self._data.keys()

    def __contains__(self, key):
        self._setup()
        return key in self._data.keys()

    def __len__(self):
        self._setup()
        return len(self._data)


def _serialize_news_statistic_per_app(stream, value):
    s_long(stream, 1)  # version
    s_long(stream, len(value))
    for app_id, stats in value.iteritems():
        s_unicode(stream, app_id)
        _serialize_news_item_statistics(stream, stats)


def _deserialize_news_item_statistic_per_app(stream):
    news_stats_per_app = NewsStatisticPerApp()
    news_stats_per_app.set_data(stream)
    return news_stats_per_app


class NewsItemStatistics(object):
    _default_stats = {
        'age': {},
        'gender': {},
    }
    AGE_LENGTH = 21
    GENDER_LENGTH = 3

    @staticmethod
    def default_age_stats():
        return [0] * NewsItemStatistics.AGE_LENGTH

    @staticmethod
    def default_gender_stats():
        return [0] * NewsItemStatistics.GENDER_LENGTH

    @staticmethod
    def default_time_stats():
        return [0]

    @property
    def reached_total(self):
        total = sum(self.reached_gender)
        # for validating if stats work properly
        if sum(self.reached_age) != total:
            logging.error('Expected sum of reached_gender (%d) and reached_age (%d) to be the same', total,
                          sum(self.reached_age))
        if sum(self.reached_time) != total:
            logging.error('Expected sum of reached_gender (%d) and reached_time (%d) to be the same', total,
                          sum(self.reached_time))
        return total

    @property
    def rogered_total(self):
        return sum(self.rogered_gender)

    @property
    def action_total(self):
        return sum(self.action_gender)

    @property
    def followed_total(self):
        return sum(self.followed_gender)

    reached_age = long_list_property('reached_age')  # 0-5, 5-10, 5-15, ..., 95-100+
    reached_gender = long_list_property('reached_gender')  # male, female, other
    reached_time = long_list_property('reached_time')  # reach on first hour, reach on second hour, ... (max 30d)
    rogered_age = long_list_property('rogered_age')
    rogered_gender = long_list_property('rogered_gender')
    rogered_time = long_list_property('rogered_time')
    action_age = long_list_property('action_age')
    action_gender = long_list_property('action_gender')
    action_time = long_list_property('action_time')
    followed_age = long_list_property('followed_age')
    followed_gender = long_list_property('followed_gender')
    followed_time = long_list_property('followed_time')

    @classmethod
    def default_statistics(cls):
        stats = cls()
        for prop in ('reached', 'rogered', 'action', 'followed'):
            for statistic in ('age', 'gender', 'time'):
                default_statistics = getattr(cls, 'default_%s_stats' % statistic)()
                setattr(stats, '%s_%s' % (prop, statistic), default_statistics)
        return stats

    @staticmethod
    def get_age_index(age):
        i = int(age / 5) if age and age >= 0 else 0
        if i > 20:
            return 20
        return i

    @staticmethod
    def get_gender_index(gender):
        if gender == UserProfile.GENDER_MALE:
            return 1
        if gender == UserProfile.GENDER_FEMALE:
            return 2
        return 0

    @staticmethod
    def get_time_index(news_item_created_datetime, action_datetime):
        # type: (datetime, datetime) -> int
        diff = action_datetime - news_item_created_datetime
        return int(diff.total_seconds() / 3600)

    @staticmethod
    def gender_translation_key(gender_index):
        if gender_index == 1:
            return u'gender-male'
        elif gender_index == 2:
            return u'gender-female'
        else:
            return u'unknown'

    @classmethod
    def get_age_label(cls, age_index):
        azzert(age_index >= 0, 'Expected age_index to be positive, got %s' % age_index)
        start_age = age_index * 5
        end_age = start_age + 5
        return u'%s - %s' % (start_age, end_age)

    @classmethod
    def default_age_dict(cls):
        stats = cls._default_stats['age']
        if not stats:
            for index in xrange(cls.AGE_LENGTH):
                stats[cls.get_age_label(index)] = 0
        return stats.copy()

    @classmethod
    def default_gender_dict(cls):
        stats = cls._default_stats['gender']
        if not stats:
            for index in xrange(cls.GENDER_LENGTH):
                stats[cls.gender_translation_key(index)] = 0
        return stats.copy()


def _serialize_news_item_statistics(stream, stats):
    """
    Args:
        stream (StringIO)
        stats (NewsItemStatistics)
    """
    s_long(stream, 1)  # version
    s_long_list(stream, stats.reached_age)
    s_long_list(stream, stats.reached_gender)
    s_long_list(stream, stats.reached_time)
    s_long_list(stream, stats.rogered_age)
    s_long_list(stream, stats.rogered_gender)
    s_long_list(stream, stats.rogered_time)
    s_long_list(stream, stats.action_age)
    s_long_list(stream, stats.action_gender)
    s_long_list(stream, stats.action_time)
    s_long_list(stream, stats.followed_age)
    s_long_list(stream, stats.followed_gender)
    s_long_list(stream, stats.followed_time)


def _deserialize_news_item_statistics(stream):
    ds_long(stream)  # version
    stats = NewsItemStatistics()
    stats.reached_age = ds_long_list(stream)
    stats.reached_gender = ds_long_list(stream)
    stats.reached_time = ds_long_list(stream)
    stats.rogered_age = ds_long_list(stream)
    stats.rogered_gender = ds_long_list(stream)
    stats.rogered_time = ds_long_list(stream)
    stats.action_age = ds_long_list(stream)
    stats.action_gender = ds_long_list(stream)
    stats.action_time = ds_long_list(stream)
    stats.followed_age = ds_long_list(stream)
    stats.followed_gender = ds_long_list(stream)
    stats.followed_time = ds_long_list(stream)
    return stats


class NewsItemStatisticsProperty(ndb.GenericProperty):

    data_type = NewsStatisticPerApp

    # For writing to datastore.
    def _to_base_type(self, value):
        stream = StringIO()
        _serialize_news_statistic_per_app(stream, value)
        return db.Blob(stream.getvalue())

    # For reading from datastore.
    def _from_base_type(self, value):
        if value is None:
            return None
        return _deserialize_news_item_statistic_per_app(StringIO(convert_to_str(value)))

    def _validate(self, value):
        if value is not None and not isinstance(value, self.data_type):
            raise ValueError(
                'Property %s must be convertible to a %s instance (%s)' % (self._name, self.data_type.__name__, value))
        return value


class NewsButton(object):
    id = unicode_property('1')
    caption = unicode_property('2')
    action = unicode_property('3')
    flow_params = unicode_property('4')
    index = long_property('5')

    def __init__(self, btn_id=None, caption=None, action=None, flow_params=None, index=0):
        self.id = btn_id
        self.caption = caption
        self.action = action
        self.flow_params = flow_params
        self.index = index


def _serialize_news_button(stream, b):
    s_unicode(stream, b.id)
    s_unicode(stream, b.caption)
    s_unicode(stream, b.action)
    s_unicode(stream, b.flow_params)
    s_long(stream, b.index)


def _deserialize_news_button(stream, version):
    b = NewsButton()
    b.id = ds_unicode(stream)
    b.caption = ds_unicode(stream)
    b.action = ds_unicode(stream)
    b.flow_params = ds_unicode(stream) if version >= 2 else None
    b.index = ds_long(stream) if version >= 3 else 0
    return b


def _serialize_news_buttons(stream, buttons):
    s_long(stream, 3)  # version
    _serialize_news_button_list(stream, buttons)


def _deserialize_news_buttons(stream):
    version = ds_long(stream)
    buttons = NewsButtons()
    for b in _deserialize_news_button_list(stream, version):
        buttons.add(b)
    return buttons


_serialize_news_button_list = get_list_serializer(_serialize_news_button)
_deserialize_news_button_list = get_list_deserializer(_deserialize_news_button, True)


class NewsButtons(SpecializedList):

    def add(self, button):
        if button.id in self._table:
            raise DuplicateButtonIdException()
        self._table[button.id] = button

    def __iter__(self):
        for b in sorted(self._table.itervalues(), key=lambda x: x.index):
            yield b

    def values(self):
        return list(self)


class NewsButtonsProperty(ndb.GenericProperty):

    @staticmethod
    def get_serializer():
        return _serialize_news_buttons

    @staticmethod
    def get_deserializer():
        return _deserialize_news_buttons

    def _to_base_type(self, value):
        stream = StringIO()
        _serialize_news_buttons(stream, value)
        return db.Blob(stream.getvalue())

    def _from_base_type(self, value):
        if value is None:
            return None
        return _deserialize_news_buttons(StringIO(convert_to_str(value)))

    # Tell what the user type is.
    data_type = NewsButtons

    def _validate(self, value):
        if value is not None and not isinstance(value, NewsButtons):
            raise ValueError('Property %s must be convertible to a NewsButtons instance (%s)' % (self._name, value))
        return super(NewsButtonsProperty, self)._validate(value)


class NewsFeed(object):
    app_id = unicode_property('1')
    name = unicode_property('2')

    def __init__(self, app_id=None, name=None):
        self.app_id = app_id
        self.name = name


def _serialize_news_feed(stream, f):
    s_unicode(stream, f.app_id)
    s_unicode(stream, f.name)


def _deserialize_news_feed(stream, version):
    f = NewsFeed()
    f.app_id = ds_unicode(stream)
    f.name = ds_unicode(stream)
    return f


def _serialize_news_feeds(stream, feeds):
    s_long(stream, 1)  # version
    _serialize_news_feed_list(stream, feeds)


def _deserialize_news_feeds(stream):
    version = ds_long(stream)
    feeds = NewsFeeds()
    for f in _deserialize_news_feed_list(stream, version) or []:
        feeds.add(f)
    return feeds


_serialize_news_feed_list = get_list_serializer(_serialize_news_feed)
_deserialize_news_feed_list = get_list_deserializer(_deserialize_news_feed, True)


class NewsFeeds(SpecializedList):

    def add(self, feed):
        if feed.app_id in self._table:
            raise DuplicateAppIdException()
        self._table[feed.app_id] = feed


class NewsFeedsProperty(ndb.GenericProperty):

    # Tell what the user type is.
    data_type = NewsFeeds

    # For writing to datastore.
    def _to_base_type(self, value):
        with closing(StringIO()) as stream:
            _serialize_news_feeds(stream, value)
            return db.Blob(stream.getvalue())

    # For reading from datastore.
    def _from_base_type(self, value):
        if value is None:
            return None
        return _deserialize_news_feeds(StringIO(convert_to_str(value)))

    def validate(self, value):
        if value is not None and not isinstance(value, NewsFeeds):
            raise ValueError('Property %s must be convertible to a NewsFeeds instance (%s)' % (self._name, value))
        return super(NewsFeedsProperty, self)._validate(value)
