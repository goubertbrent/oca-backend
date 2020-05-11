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

from contextlib import closing
import zlib

from google.appengine.ext import db
from mcfw.properties import azzert
from mcfw.serialization import CustomProperty, s_long_list, ds_long_list


try:
    import cStringIO as StringIO
except ImportError:
    import StringIO


class CompressedIntegerList(list):

    def __init__(self, value, model, prop_name):
        azzert(model and prop_name)
        self._model = model
        self._prop_name = prop_name
        self._paused_updates = False
        if isinstance(value, basestring):
            dsc = zlib.decompress(value)
            with closing(StringIO.StringIO(dsc)) as stream:
                super(CompressedIntegerList, self).__init__(ds_long_list(stream))
        else:
            super(CompressedIntegerList, self).__init__(value)

    def ljust(self, delta, value, limit):
        if limit < 0:
            raise ValueError('Illegal limit: %s' % limit)

        self._paused_updates = True
        try:
            self +=delta * [value]
            while len(self) > limit:
                self.pop(0)
        finally:
            self._paused_updates = False
        setattr(self._model, self._prop_name, db.Blob(str(self)))

    def __str__(self):
        with closing(StringIO.StringIO()) as stream:
            s_long_list(stream, self)
            return zlib.compress(stream.getvalue())

#     def __getattr__(self, name):
#         attr = object.__getattr__(self, name)
#         if hasattr(attr, '__call__') and name in ('__add__', '__delitem__', '__delslice__', '__iadd__', '__imul__', '__mul__', '__reduce__', '__reduce_ex__', '__rmul__', '__setitem__', '__setslice__', 'append', 'extend', 'insert', 'pop', 'remove', 'sort'):
#             def newfunc(*args, **kwargs):
#                 result = attr(*args, **kwargs)
#                 if not self._paused_updates:
#                     setattr(self._model, self._prop_name, db.Blob(str(self)))
#                 return result
#             return newfunc
#         else:
#             return attr


for method in ('__add__', '__delitem__', '__delslice__', '__iadd__', '__imul__', '__mul__',
               '__reduce__', '__reduce_ex__', '__rmul__', '__setitem__', '__setslice__',
               'append', 'extend', 'insert', 'pop', 'remove', 'sort'):
    def wrap(method_name):
        def f(self, *args, **kwargs):
            super_f = getattr(super(CompressedIntegerList, self), method_name)
            r = super_f(*args, **kwargs)
            if not self._paused_updates:
                setattr(self._model, self._prop_name, db.Blob(str(self)))
            return r
        return f

    setattr(CompressedIntegerList, method, wrap(method))
