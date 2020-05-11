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

from generator.custom.filters import common_namespace

CSHARP_TYPE_MAPPING = {'unicode': 'string',
    'bool':    'bool',
    'int':     'long',
    'long':    'long',
    'float':   'float'
}

CSHARP_CASTABLE_TYPE_MAPPING = {'unicode': 'string',
    'bool':    'bool?',
    'int':     'long?',
    'long':    'long?',
    'float':   'float?'
}

def csharp_delete_dots(value):
    return value.replace('.', '')

def csharp_map_type(value):
    result = CSHARP_TYPE_MAPPING.get(value, None)
    return result if result else common_namespace(value)

def csharp_map_castable_type(value):
    result = CSHARP_CASTABLE_TYPE_MAPPING.get(value, None)
    return result if result else common_namespace(value)

def csharp_has_complex_field(class_def):
    for field in class_def.fields:
        if field.type not in CSHARP_TYPE_MAPPING.keys():
            return True
    return False

def csharp_camel_case(value):
    result = list()
    nextCharInUpperCase = True
    for c in value:
        if c == '_':
            nextCharInUpperCase = True
        else:
            result.append(c.upper() if nextCharInUpperCase else c)
            nextCharInUpperCase = False
    return ''.join(result)
