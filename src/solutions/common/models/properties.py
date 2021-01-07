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

from contextlib import closing

from google.appengine.ext import db

from mcfw.consts import MISSING
from mcfw.properties import azzert
from mcfw.properties import unicode_property, typed_property, long_property, bool_property
from mcfw.serialization import s_long, s_unicode, ds_long, ds_unicode, get_list_serializer, get_list_deserializer, \
    s_bool, ds_bool
from rogerthat.models import App
from rogerthat.models.properties.messaging import SpecializedList
from rogerthat.to import TO
from rogerthat.to.service import UserDetailsTO
from solutions.common.consts import UNIT_PIECE


try:
    import cStringIO as StringIO
except ImportError:
    import StringIO


def serialize_solution_user(stream, u):
    s_long(stream, 3)  # version
    if u is None:
        s_bool(stream, False)
    else:
        s_bool(stream, True)
        s_unicode(stream, u.name)
        s_unicode(stream, u.email)
        s_unicode(stream, u.avatar_url)
        s_unicode(stream, u.language)
        s_unicode(stream, u.app_id if u.app_id is not MISSING else None)

def deserialize_solution_user(stream):
    version = ds_long(stream)  # version
    if version > 2:
        if not ds_bool(stream):
            return None
    u = SolutionUser()
    u.name = ds_unicode(stream)
    u.email = ds_unicode(stream)
    u.avatar_url = ds_unicode(stream)
    u.language = ds_unicode(stream)
    if version > 1:
        u.app_id = ds_unicode(stream)
    else:
        u.app_id = App.APP_ID_ROGERTHAT
    return u

class SolutionUser(object):
    name = unicode_property('1')
    email = unicode_property('2')
    avatar_url = unicode_property('3')
    language = unicode_property('4')
    app_id = unicode_property('5')

    @staticmethod
    def fromTO(to):
        u = SolutionUser()
        u.name = to.name
        u.email = to.email
        u.avatar_url = to.avatar_url
        u.language = to.language
        u.app_id = to.app_id
        return u

    def to_user_details(self):
        return UserDetailsTO.create(self.email, self.name, self.language, self.avatar_url, self.app_id)


class SolutionUserProperty(db.UnindexedProperty):

    data_type = SolutionUser

    def get_value_for_datastore(self, model_instance):
        stream = StringIO.StringIO()
        serialize_solution_user(stream, super(SolutionUserProperty, self).get_value_for_datastore(model_instance))
        return db.Blob(stream.getvalue())

    def make_value_from_datastore(self, value):
        if value is None:
            return None
        return deserialize_solution_user(StringIO.StringIO(value))


class MenuItemTO(TO):
    VISIBLE_IN_MENU = 1
    VISIBLE_IN_ORDER = 2

    name = unicode_property('1')
    price = long_property('2')
    description = unicode_property('3')
    visible_in = long_property('4')
    # ordering unit and step
    unit = long_property('5')
    step = long_property('6')
    image_id = long_property('7')
    qr_url = unicode_property('8')
    has_price = bool_property('9')
    id = unicode_property('10')
    # custom unit can be used for pricing without linking to (ordering) unit
    custom_unit = long_property('11')


class MenuCategoryTO(TO):
    name = unicode_property('1')
    items = typed_property('2', MenuItemTO, True)
    index = long_property('3')
    predescription = unicode_property('4')
    postdescription = unicode_property('5')
    id = unicode_property('6')


class MenuCategories(SpecializedList):

    def add(self, category):
        if category.id:
            azzert(category.id not in self._table)
            self._table[category.id] = category
        else:
            azzert(category.name not in self._table)
            self._table[category.name] = category


def _serialize_item(stream, item):
    s_unicode(stream, item.name)
    s_long(stream, item.price)
    s_unicode(stream, item.description)
    s_long(stream, item.visible_in)
    s_long(stream, item.unit)
    s_long(stream, item.step)
    s_long(stream, -1 if item.image_id in (None, MISSING) else item.image_id)
    s_unicode(stream, None if item.qr_url is MISSING else item.qr_url)
    s_bool(stream, item.price > 0 if item.has_price is MISSING else item.has_price)
    s_unicode(stream, item.id)
    s_long(stream, item.custom_unit)


def convert_price_to_long(str_price):
    long_price = long(100 * float(str_price.replace(',', '.')))
    return long_price


def _deserialize_item(stream, version):
    item = MenuItemTO()
    item.name = ds_unicode(stream)
    item.price = convert_price_to_long(ds_unicode(stream)) if version < 5 else ds_long(stream)
    item.description = ds_unicode(stream)
    item.visible_in = ds_long(stream) if version > 2 else MenuItemTO.VISIBLE_IN_MENU | MenuItemTO.VISIBLE_IN_ORDER
    item.unit = ds_long(stream) if version > 3 else UNIT_PIECE
    item.step = ds_long(stream) if version > 3 else 1
    if version < 6:
        item.image_id = None
    else:
        item.image_id = ds_long(stream)
        if item.image_id == -1:
            item.image_id = None
    item.qr_url = None if version < 7 else ds_unicode(stream)
    item.has_price = item.price > 0 if version < 8 else ds_bool(stream)
    item.id = ds_unicode(stream) if version > 8 else None
    # defaults to ordering unit
    item.custom_unit = ds_long(stream) if version > 9 else item.unit
    return item

_serialize_item_list = get_list_serializer(_serialize_item)
_deserialize_item_list = get_list_deserializer(_deserialize_item, True)


def _serialize_category(stream, c):
    s_unicode(stream, c.name)
    _serialize_item_list(stream, c.items)
    s_long(stream, c.index)
    s_unicode(stream, c.predescription)
    s_unicode(stream, c.postdescription)
    s_unicode(stream, c.id)


def _deserialize_category(stream, version):
    c = MenuCategoryTO()
    c.name = ds_unicode(stream)
    c.items = _deserialize_item_list(stream, version)
    c.index = ds_long(stream)
    c.predescription = ds_unicode(stream) if version > 1 else None
    c.postdescription = ds_unicode(stream) if version > 1 else None
    c.id = ds_unicode(stream) if version > 8 else None
    return c

_serialize_category_list = get_list_serializer(_serialize_category)
_deserialize_category_list = get_list_deserializer(_deserialize_category, True)


def _serialize_categories(stream, categories):
    s_long(stream, 10)  # version in case we need to adjust the categories structure
    _serialize_category_list(stream, categories.values())


def _deserialize_categories(stream):
    version = ds_long(stream)
    categories = MenuCategories()
    for c in _deserialize_category_list(stream, version):
        categories.add(c)
    return categories

class MenuCategoriesProperty(db.UnindexedProperty):

    # Tell what the user type is.
    data_type = MenuCategories

    # For writing to datastore.
    def get_value_for_datastore(self, model_instance):
        stream = StringIO.StringIO()
        super_value = super(MenuCategoriesProperty, self).get_value_for_datastore(model_instance)
        if not super_value:
            return None
        _serialize_categories(stream, super_value)
        return db.Blob(stream.getvalue())

    # For reading from datastore.
    def make_value_from_datastore(self, value):
        if value is None:
            return None
        return _deserialize_categories(StringIO.StringIO(value))

    def validate(self, value):
        if value is not None and not isinstance(value, MenuCategories):
            raise ValueError('Property %s must be convertible to a MenuCategories instance (%s)' % (self.name, value))
        return super(MenuCategoriesProperty, self).validate(value)

    def empty(self, value):
        return not value


class ActivatedModuleTO(TO):
    name = unicode_property('1', default=None)
    timestamp = long_property('2', default=0)

def _serialize_activated_module(stream, m):
    s_unicode(stream, m.name)
    s_long(stream, m.timestamp)


def _deserialize_activated_module(stream, version):
    m = ActivatedModuleTO()
    m.name = ds_unicode(stream)
    m.timestamp = ds_long(stream)
    return m


def _serialize_activated_modules(stream, modules):
    s_long(stream, 1)  # version
    _serialize_activated_module_list(stream, modules)


def _deserialize_activated_modules(stream):
    version = ds_long(stream)
    modules = ActivatedModules()
    for m in _deserialize_activated_module_list(stream, version) or []:
        modules.add(m)
    return modules


_serialize_activated_module_list = get_list_serializer(_serialize_activated_module)
_deserialize_activated_module_list = get_list_deserializer(_deserialize_activated_module, True)


class ActivatedModules(SpecializedList):

    def add(self, m):
        self._table[m.name] = m

    def remove(self, name):
        if name in self._table:
            del self._table[name]


class ActivatedModulesProperty(db.UnindexedProperty):

    # Tell what the user type is.
    data_type = ActivatedModules

    # For writing to datastore.
    def get_value_for_datastore(self, model_instance):
        super_value = super(ActivatedModulesProperty, self).get_value_for_datastore(model_instance)
        if not super_value:
            return None
        with closing(StringIO.StringIO()) as stream:
            _serialize_activated_modules(stream, super_value)
            return db.Blob(stream.getvalue())

    # For reading from datastore.
    def make_value_from_datastore(self, value):
        if value is None:
            return None
        return _deserialize_activated_modules(StringIO.StringIO(value))

    def validate(self, value):
        if value is not None and not isinstance(value, ActivatedModules):
            raise ValueError('Property %s must be convertible to a ActivatedModules instance (%s)' % (self.name, value))
        return super(ActivatedModulesProperty, self).validate(value)

    def empty(self, value):
        return not value
