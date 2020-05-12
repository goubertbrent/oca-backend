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

from mcfw.properties import object_factory

SIMPLE_TYPES = ['str', 'unicode', 'bool', 'int', 'float', 'long']


def common_is_object_factory(field):
    return field.type == object_factory.__module__ + '.' + object_factory.__name__  # @UndefinedVariable


def common_is_simple_type(value):
    return value in SIMPLE_TYPES


def common_replace_dots(value):
    return value.replace('.', '/')


def common_camelcase(value, cap_first="false"):
    splitted = value.split('.')
    if len(splitted) == 1:
        return splitted[0].upper()
    i = 0
    result = list()
    if cap_first.lower() == "false":
        i = 1
        result.append(splitted[0][0].lower() + splitted[0][1:])
    while i < len(splitted):
        result.append(splitted[i][0].upper() + splitted[i][1:])
        i += 1
    return ''.join(result)


def common_namespace(value, cap_first="true"):
    splitted = value.split('.')
    if len(splitted) == 1:
        return splitted[0].upper()
    i = 0
    result = list()
    if cap_first.lower() == "false":
        i = 1
        result.append(splitted[0][0].lower() + splitted[0][1:])
    while i < len(splitted):
        result.append(splitted[i][0].upper() + splitted[i][1:])
        i += 1
    return '.'.join(result)


def common_cap_first(value):
    return value[0].upper() + value[1:]
