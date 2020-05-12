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

from google.appengine.ext import db

from mcfw.properties import unicode_property, get_members
from mcfw.serialization import s_unicode, s_long, ds_long, ds_unicode, CustomProperty

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO


def serialize_oauth_settings(stream, data):
    s_long(stream, 3)  # version
    if data:
        s_unicode(stream, data.url)
        s_unicode(stream, data.authorize_path)
        s_unicode(stream, data.token_path)
        s_unicode(stream, data.identity_path)
        s_unicode(stream, data.scopes)
        s_unicode(stream, data.client_id)
        s_unicode(stream, data.secret)
        s_unicode(stream, data.domain)
        s_unicode(stream, data.service_identity_email)
        s_unicode(stream, data.public_key)
        s_unicode(stream, data.jwt_audience)
        s_unicode(stream, data.jwt_issuer)
    else:
        s_unicode(stream, None)


def deserialize_oauth_settings(stream):
    version = ds_long(stream)
    model = OAuthSettings()
    url_or_none = ds_unicode(stream)
    if url_or_none is None:
        return model
    model.url = url_or_none
    model.authorize_path = ds_unicode(stream)
    model.token_path = ds_unicode(stream)
    model.identity_path = ds_unicode(stream)
    model.scopes = ds_unicode(stream)
    model.client_id = ds_unicode(stream)
    model.secret = ds_unicode(stream)
    model.domain = ds_unicode(stream)
    if version > 1:
        model.service_identity_email = ds_unicode(stream)
    if version > 2:
        model.public_key = ds_unicode(stream)
        model.jwt_audience = ds_unicode(stream)
        model.jwt_issuer = ds_unicode(stream)
    return model


class OAuthSettings(object):
    url = unicode_property('1')  # https://myoauthsite.com
    authorize_path = unicode_property('2')  # /oauth/authorize
    token_path = unicode_property('3')  # /oauth/token
    identity_path = unicode_property('4')  # /me
    scopes = unicode_property('5')  # / read,write
    client_id = unicode_property('6')
    secret = unicode_property('7')
    domain = unicode_property('8')  # myoauthsite.com
    service_identity_email = unicode_property('9')  # service@example.com
    public_key = unicode_property('10')
    jwt_audience = unicode_property('11')
    jwt_issuer = unicode_property('12')

    def __init__(self):
        _, simple_members = get_members(OAuthSettings)
        for prop, _ in simple_members:
            setattr(self, prop, None)

    @property
    def authorize_url(self):
        return u'%s%s' % (self.url, self.authorize_path)

    @property
    def token_url(self):
        return u'%s%s' % (self.url, self.token_path)

    @property
    def identity_url(self):
        return u'%s%s' % (self.url, self.identity_path)


class OAuthSettingsProperty(CustomProperty, db.UnindexedProperty):
    data_type = OAuthSettings

    @staticmethod
    def get_serializer():
        return serialize_oauth_settings

    @staticmethod
    def get_deserializer():
        return deserialize_oauth_settings

    def get_value_for_datastore(self, model_instance):
        value = super(OAuthSettingsProperty, self).get_value_for_datastore(model_instance)
        if value is None:
            return None
        stream = StringIO.StringIO()
        serialize_oauth_settings(stream, value)
        return db.Blob(stream.getvalue())

    def make_value_from_datastore(self, value):
        if value is None:
            return OAuthSettings()
        return deserialize_oauth_settings(StringIO.StringIO(value))
