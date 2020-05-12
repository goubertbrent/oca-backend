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

from rogerthat.models.properties.messaging import SpecializedList
from google.appengine.ext import db
from mcfw.properties import long_property, unicode_property
from mcfw.serialization import s_long, s_unicode, ds_long, ds_unicode, get_list_serializer, get_list_deserializer


try:
    import cStringIO as StringIO
except ImportError:
    import StringIO


class ProspectComment(object):
    index = long_property('1')
    text = unicode_property('2')
    creator = unicode_property('3')
    timestamp = long_property('4')


def _serialize_prospect_comment(stream, comment):
    s_long(stream, comment.index)
    s_unicode(stream, comment.text)
    s_unicode(stream, comment.creator)
    s_long(stream, comment.timestamp)


def _deserialize_prospect_comment(stream, version):
    comment = ProspectComment()
    comment.index = ds_long(stream)
    comment.text = ds_unicode(stream)
    comment.creator = ds_unicode(stream)
    comment.timestamp = ds_long(stream)
    return comment


_serialize_prospect_comment_list = get_list_serializer(_serialize_prospect_comment)
_deserialize_prospect_comment_list = get_list_deserializer(_deserialize_prospect_comment, True)


class ProspectComments(SpecializedList):

    def add(self, prospect_comment):
        self._table[prospect_comment.index] = prospect_comment
        return prospect_comment


def _serialize_prospect_comments(stream, prospect_comments):
    s_long(stream, 1)  # version
    _serialize_prospect_comment_list(stream, [] if prospect_comments is None else prospect_comments.values())


def _deserialize_prospect_comments(stream):
    version = ds_long(stream)
    prospect_comments = ProspectComments()
    for comment in _deserialize_prospect_comment_list(stream, version):
        prospect_comments.add(comment)
    return prospect_comments


class ProspectCommentsProperty(db.UnindexedProperty):

    # Tell what the user type is.
    data_type = ProspectComments

    # For writing to datastore.
    def get_value_for_datastore(self, model_instance):
        stream = StringIO.StringIO()
        _serialize_prospect_comments(stream, super(ProspectCommentsProperty, self).get_value_for_datastore(model_instance))
        return db.Blob(stream.getvalue())

    # For reading from datastore.
    def make_value_from_datastore(self, value):
        if value is None:
            return None
        return _deserialize_prospect_comments(StringIO.StringIO(value))

    def validate(self, value):
        if value is not None and not isinstance(value, ProspectComments):
            raise ValueError('Property %s must be convertible to a ProspectComments instance (%s)' % (self.name, value))
        return super(ProspectCommentsProperty, self).validate(value)

    def empty(self, value):
        return not value
