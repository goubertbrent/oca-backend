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

from google.appengine.ext import ndb
from typing import List

from rogerthat.dal import parent_ndb_key
from rogerthat.models.common import NdbModel, TOProperty
from rogerthat.rpc import users
from rogerthat.to.maps import MapButtonTO, MapListSectionItemTO
from rogerthat.to.news import BaseMediaTO


class MapSettings(NdbModel):
    data = ndb.JsonProperty()

    @property
    def tag(self):
        return self.key.id().decode('utf8')

    @classmethod
    def create_key(cls, tag):
        return ndb.Key(cls, tag)


class MapConfig(NdbModel):
    center = ndb.GeoPtProperty(indexed=False)  # type: ndb.GeoPt
    distance = ndb.IntegerProperty(indexed=False)
    filters = ndb.StringProperty(repeated=True)
    default_filter = ndb.StringProperty()
    buttons = TOProperty(MapButtonTO, repeated=True)  # type: List[MapButtonTO]

    @property
    def tag(self):
        return self.key.id().split('~')[1]

    @classmethod
    def create_key(cls, app_id, map_tag):
        return ndb.Key(cls, '%s~%s' % (app_id, map_tag))


class MapNotifications(NdbModel):
    tag = ndb.StringProperty()
    enabled = ndb.BooleanProperty()

    @property
    def app_user(self):
        return users.User(self.key.parent().id().decode('utf8'))

    @classmethod
    def create_key(cls, tag, app_user):
        return ndb.Key(cls, tag, parent=parent_ndb_key(app_user, namespace=cls.NAMESPACE))

    @classmethod
    def list_by_tag(cls, tag):
        qry = cls.query()
        qry = qry.filter(cls.tag == tag)
        return qry


class MapSavedItem(NdbModel):
    created = ndb.DateTimeProperty(auto_now_add=True)
    item_id = ndb.StringProperty()

    @property
    def id(self):
        return self.key.id()

    @classmethod
    def create_parent_key(cls, tag, app_user):
        return ndb.Key(cls, tag, parent=parent_ndb_key(app_user, namespace=cls.NAMESPACE))

    @classmethod
    def create_key(cls, tag, app_user, item_id):
        return ndb.Key(cls, item_id, parent=cls.create_parent_key(tag, app_user))

    @classmethod
    def list_by_date(cls, tag, app_user):
        qry = cls.query(ancestor=cls.create_parent_key(tag, app_user))
        qry = qry.order(-MapSavedItem.created)
        return qry


class MapServiceMediaItem(NdbModel):
    role_ids = ndb.TextProperty(repeated=True)
    item = TOProperty(BaseMediaTO)  # type: BaseMediaTO

    @classmethod
    def from_to(cls, m):
        return cls(role_ids=m.role_ids,
                   item=m.item)


class MapServiceListItem(NdbModel):
    role_ids = ndb.TextProperty(repeated=True)
    item = TOProperty(MapListSectionItemTO(), repeated=False)  # type: MapListSectionItemTO


# todo multiple languages
class MapService(NdbModel):
    title = ndb.TextProperty()
    main_place_type = ndb.TextProperty()
    place_types = ndb.TextProperty(repeated=True)
    address = ndb.TextProperty()
    geo_location = ndb.GeoPtProperty(indexed=False)  # type: ndb.GeoPt
    # Only used for the sort order of the opening hours
    opening_hours_links = ndb.KeyProperty(repeated=True, indexed=False)  # type: List[ndb.Key]

    media_items = ndb.LocalStructuredProperty(MapServiceMediaItem, repeated=True)  # type: List[MapServiceMediaItem]
    horizontal_items = ndb.LocalStructuredProperty(MapServiceListItem, repeated=True)  # type: List[MapServiceListItem]
    vertical_items = ndb.LocalStructuredProperty(MapServiceListItem, repeated=True)  # type: List[MapServiceListItem]
    has_news = ndb.BooleanProperty(indexed=False)

    @property
    def service_identity_email(self):
        return self.key.id()

    @property
    def service_user(self):
        from rogerthat.utils.service import get_service_user_from_service_identity_user
        return get_service_user_from_service_identity_user(users.User(self.service_identity_email))

    @classmethod
    def create_key(cls, service_identity_email):
        return ndb.Key(cls, service_identity_email)
