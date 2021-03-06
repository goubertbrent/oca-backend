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

import inspect
import re


class Enum(object):

    @classmethod
    def all(cls):
        return [getattr(cls, a) for a in dir(cls) if not a.startswith('_') and not inspect.ismethod(getattr(cls, a))]


def normalize_search_string(search_string):
    return re.sub(u"[, \" \+ \- : > < = \\\\ \( \) ~]", u" ", search_string)


def chunks(iterable, amount):
    """Yield successive amount-sized chunks from iterable."""
    for i in xrange(0, len(iterable), amount):
        yield iterable[i:i + amount]


def get_readable_key(key):
    # type: (db.Key) -> str
    args = []
    if key.has_id_or_name():
        if isinstance(key.name(), (str, unicode)):
            args.append('name=\'%s\'' % key.name())
        else:
            args.append('id=%d' % key.id())
    if key.parent():
        args.append('parent=' + get_readable_key(key.parent()))
    return '%s(%s)' % (key.kind(), ', '.join(args))


def convert_to_str(data):
    if isinstance(data, unicode):
        return data.encode('utf-8')
    elif isinstance(data, list):
        for i, list_item in enumerate(data):
            data[i] = convert_to_str(list_item)
    elif isinstance(data, dict):
        for key, val in data.iteritems():
            data[key] = convert_to_str(val)
    return data
