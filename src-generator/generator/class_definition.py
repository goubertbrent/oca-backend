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
import inspect

from mcfw.consts import MISSING
from mcfw.properties import object_factory, azzert


class SubtypeEnum(object):

    def __init__(self, name, values):
        self.name = name
        self.values = values


class ClassDefinition(object):

    def __init__(self, name=None, package=None, super_class=None, fields=None, doc=None, clazz=None):
        self.name = name
        if package.startswith('rogerthat.'):
            package = package.replace('rogerthat.', 'com.mobicage.', 1)
        self.package = package
        self.super_class = super_class
        self.fields = fields or []
        self.doc = doc
        self.clazz = clazz
        self.is_supertype = isinstance(clazz, object_factory)
        if isinstance(clazz, object_factory):
            cls = clazz.subtype_enum
            azzert(cls)
            values = {a: getattr(cls, a) for a in dir(cls)
                      if not a.startswith('_') and not inspect.ismethod(getattr(cls, a))}
            self.subtype_enum = SubtypeEnum(cls.__name__, values)

    @property
    def full_name(self):
        return "%s.%s" % (self.package, self.name)

    def __str__(self):
        return self.full_name

    __repr__ = __str__


def key_type(factory):
    if factory:
        t = type(factory.subtype_mapping.keys()[0])
        if t is str:
            t = unicode
        if t is int:
            t = long
        return t


class AttrDefinition(object):

    def __init__(self, name=None, type_=None, collection_type=None, doc=None, default=MISSING, subtype=None):
        self.name = name
        if type_.startswith('rogerthat.'):
            type_ = type_.replace('rogerthat.', 'com.mobicage.', 1)
        self.type = type_
        self.collection_type = collection_type  # eg. map/set/list/tuple/...
        self.doc = doc
        self.default = default
        self.subtype = subtype

    def __str__(self):
        return "%s %s" % (self.type, self.name)

    __repr__ = __str__


class FunctionDefinition(object):

    def __init__(self, name=None, rtype=None, args=None):
        self.name = name
        self.rtype = rtype
        self.args = args or []


class PackageDefinition(object):

    def __init__(self, name=None, functions=None):
        self.name = name
        self.functions = functions or []


class SubType(object):

    def __init__(self, type_, key_type):
        self.type = type_
        self.key_type = key_type

    def subtype_name(self, key):
        value = self.type.subtype_mapping[key]
        return u'%s.%s' % (value.__module__.replace('rogerthat.', 'com.mobicage.', 1), value.__name__)
