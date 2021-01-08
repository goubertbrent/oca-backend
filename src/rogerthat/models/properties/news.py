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

from google.appengine.ext import db, ndb

from mcfw.properties import long_property, unicode_property, azzert
from mcfw.serialization import s_long, ds_long, s_unicode, ds_unicode, get_list_serializer, get_list_deserializer
from mcfw.utils import convert_to_str
from rogerthat.models import UserProfile
from rogerthat.models.properties.messaging import SpecializedList, DuplicateButtonIdException

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class NewsItemStatistics(object):
    AGE_LENGTH = 21
    GENDER_LENGTH = 3

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

    @classmethod
    def get_gender_label(cls, gender_index):
        if gender_index == 1:
            return u'gender-male'
        elif gender_index == 2:
            return u'gender-female'
        else:
            return u'gender-unknown'

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
    def get_gender_labels(cls):
        return [cls.get_gender_label(index) for index in xrange(cls.GENDER_LENGTH)]

    @classmethod
    def get_age_labels(cls):
        return [cls.get_age_label(index) for index in xrange(cls.AGE_LENGTH)]


class NewsButtonTO(object):
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
    b = NewsButtonTO()
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
