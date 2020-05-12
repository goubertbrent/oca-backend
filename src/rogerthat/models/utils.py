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

import sys

import yaml

from google.appengine.ext import db, ndb
from mcfw.consts import MISSING
from mcfw.properties import azzert
from mcfw.rpc import returns, arguments
from rogerthat.utils import bizz_check

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


@returns(db.Property)
def add_meta(prop, **kwargs):
    azzert(isinstance(prop, db.Property))
    for k, v in kwargs.iteritems():
        setattr(prop, '_%s' % k, v)
    return prop


@returns(object)
@arguments(prop=db.Property, meta=unicode, default=object)
def get_meta(prop, meta, default=MISSING):
    if default is MISSING:
        return getattr(prop, '_%s' % meta)
    else:
        return getattr(prop, '_%s' % meta, default)


def allocate_id(model_class, parent=None):
    return allocate_ids(model_class, 1, parent)[0]


@db.non_transactional
def allocate_ids(model_class, count, parent=None):
    id_range = db.allocate_ids(db.Key.from_path(model_class.kind(), 1, parent=parent), count)  # (start, end)
    return range(id_range[0], id_range[1] + 1)


@ndb.non_transactional()
def ndb_allocate_id(model_class, parent=None):
    return ndb_allocate_ids(model_class, 1, parent)[0]


@ndb.non_transactional()
def ndb_allocate_ids(model_class, count, parent=None):
    return model_class.allocate_ids(count, parent=parent)


@returns(dict)
@arguments(old_model=db.Model)
def copy_model_properties(old_model):
    kwargs = dict()
    for propname, propvalue in old_model.properties().iteritems():
        if propname == "_class":
            continue
        if isinstance(propvalue, db.ReferenceProperty):
            value = getattr(old_model.__class__, propname).get_value_for_datastore(old_model)  # the key
        else:
            value = getattr(old_model, propname)
        kwargs[propname] = value

    if isinstance(old_model, db.Expando):
        for dynamic_propname in old_model.dynamic_properties():
            kwargs[dynamic_propname] = getattr(old_model, dynamic_propname)

    return kwargs


@returns(unicode)
@arguments(model=db.Model)
def model_to_yaml(model):
    def _write_value(stream, value):
        if value is None:
            value = 'null'
        elif isinstance(value, basestring):
            if value == '' or value.isdigit() or '%' in value:
                # put empty or numeric strings between single quotes
                value = "'%s'" % value
            elif value.find('\n') != -1:
                value = "|\n  %s" % ("\n  ".join(value.splitlines()))
        stream.write(str(value))

    # TODO: rm if decided which type of docstring
    def _write_doc(stream, propobject, indent=0):
        doc = get_meta(propobject, 'doc', None)
        if doc:
            for i, l in enumerate(doc.splitlines()):
                if i:
                    stream.write('\n%s' % (indent * ' ',))
                stream.write("  # %s" % l)

    stream = StringIO()
    prev_prefix = None

    def sort_prop(item):
        propname, propobject = item
        return get_meta(propobject, 'order', default=sys.maxint), propname

    for propname, propobject in sorted(model.properties().items(), key=sort_prop):
        if propname == "_class":
            continue

        # Grouping settings with the same prefix
        if prev_prefix and not propname.startswith(prev_prefix):
            stream.write('\n')
        prev_prefix = ''
        for c in propname:
            if c.islower():
                prev_prefix += c
            else:
                break

        # Write doc strings
        doc = getattr(propobject, '_doc', None)
        if doc:
            for l in doc.splitlines():
                stream.write("# %s\n" % l)

        # Write property name and value
        stream.write(propname)
        stream.write(":")
        if isinstance(propobject, db.ListProperty):
            l = getattr(model, propname)
            if l:
                for value in l:
                    stream.write("\n- ")
                    _write_value(stream, value)
            else:
                stream.write(" []")
        else:
            stream.write(" ")
            _write_value(stream, getattr(model, propname))

        stream.write("\n")

    return stream.getvalue()


@returns(db.Model)
@arguments(model=db.Model, stream=unicode)
def populate_model_by_yaml(model, stream):
    d = yaml.load(stream)
    bizz_check(d, "Empty yaml")
    missing_properties = [propname for propname in model.properties() if propname not in d]
    if missing_properties:
        from rogerthat.rpc.service import BusinessException
        raise BusinessException("Missing properties: %s" % ", ".join(missing_properties))

    for propname, propobject in model.properties().iteritems():
        value = d[propname]
        if value is not None and isinstance(propobject, db.StringProperty):
            value = str(value)
        setattr(model, propname, value)
    return model


@returns(db.Key)
@arguments(key=db.Key, from_name=unicode, to_name=unicode)
def replace_name_in_key(key, from_name, to_name):
    old_parent_key = key.parent()
    if old_parent_key:
        new_parent_key = replace_name_in_key(old_parent_key, from_name, to_name)
    else:
        new_parent_key = None

    key_name = key.name()
    if key_name:
        if key_name == from_name:
            new_key_id_or_name = to_name
        elif key_name.startswith(from_name + '/'):
            new_key_id_or_name = to_name + key_name[len(from_name):]
        else:
            new_key_id_or_name = key_name
    else:
        new_key_id_or_name = key.id_or_name()

    return db.Key.from_path(key.kind(), new_key_id_or_name, parent=new_parent_key)
