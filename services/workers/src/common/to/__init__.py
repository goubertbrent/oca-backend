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

from typing import Type, TypeVar

from common.mcfw.rpc import serialize_complex_value, parse_complex_value


def convert_to_unicode(v):
    if v is None:
        return None
    if isinstance(v, str):
        return v.decode('utf-8')
    return v


TO_TYPE = TypeVar('TO_TYPE', bound='TO')


class TO(object):
    def __str__(self):
        # Useful when debugging. Can be evaluated to get an object with the same properties back.
        return '%s(%s)' % (self.__class__.__name__, ', '.join('%s=%r' % (k, getattr(self, k))
                                                              for k in self.to_dict()))

    __repr__ = __str__

    def __init__(self, **kwargs):
        if 'type' in kwargs and isinstance(kwargs['type'], basestring):
            # Fix for creating objects with subtype_mapping via constructor
            setattr(self, 'type', convert_to_unicode(kwargs['type']))
        for k, v in kwargs.iteritems():
            if isinstance(v, str):
                v = v.decode('utf-8')
            setattr(self, k, v)

    def to_dict(self, include=None, exclude=None):
        # type: (list[basestring], list[basestring]) -> dict[str, object]
        result = serialize_complex_value(self, type(self), False, skip_missing=True)
        if include:
            if not isinstance(include, list):
                include = [include]
            return {key: result[key] for key in include if key in result}
        if exclude:
            if not isinstance(exclude, list):
                exclude = [exclude]
            return {key: result[key] for key in set(result.keys()) - set(exclude) if key in result}
        return result

    @classmethod
    def from_dict(cls, data):
        # type: (Type[TO_TYPE], dict) -> TO_TYPE
        return parse_complex_value(cls, data, False)

    @classmethod
    def from_list(cls, data):
        # type: (Type[TO_TYPE], list[dict]) -> list[TO_TYPE]
        return parse_complex_value(cls, data, True)

    @classmethod
    def from_model(cls, m):
        return cls.from_dict(m.to_dict())
