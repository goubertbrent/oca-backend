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

TS_TYPE_MAPPING = {
    'unicode': 'string',
    'bool': 'boolean',
    'float': 'number',
    'int': 'number',
    'long': 'number',
    'dict': '{[key: string]: any;}',
}


def ts_map_type(field):
    primitive = TS_TYPE_MAPPING.get(field.type)
    if primitive:
        if primitive in ('boolean', 'number'):
            return '%s[]' % primitive if field.collection_type else primitive
        else:
            if field.collection_type:
                return '%s[]' % primitive  # lists are never nullable
            return '%s | null' % primitive
    name = field.type.split('.')[-1]
    if field.collection_type:
        return '%s[]' % name
    return '%s | null' % name


def subtype_enum_value(to):
    for key, value in to.super_class.subtype_enum.values.iteritems():
        mapping = to.super_class.clazz.subtype_mapping
        if value not in mapping:
            continue
        if to.name == mapping[value].__name__:
            return '%s.%s' % (to.super_class.subtype_enum.name, key)
    raise Exception('Could not determine value for %s' % to.name)
