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

from mcfw.consts import MISSING

JAVA_TYPE_MAPPING = {
    'unicode': 'String',
    'bool': 'boolean',
    'float': 'float',
    'int': 'long',
    'long': 'long'
}

KOTLIN_TYPE_MAPPING = {
    'unicode': 'String',
    'bool': 'Boolean',
    'float': 'Float',
    'int': 'Long',
    'long': 'Long'
}


def java_map_type(value):
    return JAVA_TYPE_MAPPING.get(value, value)


def kotlin_map_type(field, is_array, interface=False):
    value = field.type
    type_ = KOTLIN_TYPE_MAPPING.get(value, value)
    if interface and value not in KOTLIN_TYPE_MAPPING:
        split = type_.split('.')
        split[-1] = 'I' + split[-1]
        type_ = '.'.join(split)
    if is_array:
        return 'List<%s>' % type_
    if type_ == 'String' or value not in KOTLIN_TYPE_MAPPING:
        if field.required:
            return type_
        return type_ + '?'
    return type_


def kotlin_subtype(value):
    if value in ('int', 'long'):
        return 'Int'
    elif value == 'unicode':
        return 'String'
    raise Exception('unsupported subtype ' + value)


def java_parcel_read(field):
    if field.type in JAVA_TYPE_MAPPING:
        if field.type == 'bool':
            return '%s = in.readInt() != 0' % field.name
        t = JAVA_TYPE_MAPPING[field.type]
        upper_name = '%s%s' % (t[0].upper(), t[1:])
        if field.collection_type:
            return '%s = in.create%sArray()' % (field.name, upper_name)
        return '%s = in.read%s()' % (field.name, upper_name)
    if field.collection_type:
        return """ArrayList<%(type)s> %(name)sList = new ArrayList<>();
        in.readList(%(name)sList, %(type)s.class.getClassLoader());
        %(name)s = %(name)sList.toArray(new %(type)s[0])""" % {'name': field.name, 'type': field.type}
    return '%s = in.readParcelable(%s.class.getClassLoader())' % (field.name, field.type)


def java_parcel_write_method(field):
    if field.type in JAVA_TYPE_MAPPING:
        if_array = 'Array' if field.collection_type else ''
        if field.type == 'bool':
            return 'writeInt(%s ? 1 : 0)' % field.name
        t = JAVA_TYPE_MAPPING[field.type]
        upper_name = '%s%s' % (t[0].upper(), t[1:])
        return 'write%s%s(%s)' % (upper_name, if_array, field.name)
    if field.collection_type:
        return 'writeList(Arrays.asList(%s))' % field.name
    return 'writeParcelable(%s, flags)' % field.name


def java_cast(value, var, int_only=False):
    if value == 'float':
        return "(Float) %s" % var
    if value in ('int', 'long'):
        if int_only:
            return '((Long) %s).intValue()' % var
        return "((Long) %s)" % var
    if value == 'bool':
        return "(Boolean) %s" % var
    return "(%s) %s" % (java_map_type(value), var)


def java_has_complex_field(class_def):
    for field in class_def.fields:
        if field.type not in JAVA_TYPE_MAPPING.keys():
            return True
    return False


def java_has_list_field(class_def):
    for field in class_def.fields:
        if field.collection_type:
            return True
    return False


def java_default_value(field):
    if field.default == MISSING:
        raise Exception("There is no default value (field: %s)" % field.name)

    if field.default is None:
        return 'null'
    if field.collection_type:
        return "new %s[0]" % JAVA_TYPE_MAPPING.get(field.type, field.type)

    if field.type not in JAVA_TYPE_MAPPING:
        raise Exception("field.type (%s) not in JAVA_TYPE_MAPPING" % field.type)

    if field.type == 'unicode':
        return '"%s"' % field.default
    if field.type == 'bool':
        return 'true' if field.default else 'false'
    return field.default


def kotlin_default_value(field):
    if field.default is MISSING:
        raise Exception("There is no default value (field: %s)" % field.name)

    if field.default is None:
        return 'null'
    if field.collection_type:
        return "mutableListOf()"

    if field.type not in JAVA_TYPE_MAPPING:
        raise Exception("field.type (%s) not in JAVA_TYPE_MAPPING" % field.type)

    if field.type == 'unicode':
        return '"%s"' % field.default
    if field.type == 'bool':
        return 'true' if field.default else 'false'
    if field.type == 'float':
        return '%sf' % field.default
    return field.default


def needs_arrays_import(to):
    return any(field.collection_type and field.type not in JAVA_TYPE_MAPPING for field in to.fields)


def needs_linked_hashmap_import(to):
    return to.super_class is None


def literal_value(value, quote_value='"'):
    t = type(value)
    if t in (str, unicode):
        return '%s%s%s' % (quote_value, value, quote_value)
    if t in (int, long):
        return value
    raise Exception('unknown literal %s' % value)
