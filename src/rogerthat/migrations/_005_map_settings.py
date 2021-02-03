# -*- coding: utf-8 -*-
# Copyright 2021 Green Valley NV
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
# @@license_version:1.5@@
from google.appengine.ext.ndb.model import GeoPtProperty, IntegerProperty, TextProperty, GeoPt, Key, put_multi
from typing import List, Dict

from rogerthat.bizz.communities.models import CommunityMapSettings, MapLayers
from rogerthat.models import NdbModel, App
from rogerthat.models.common import TOProperty
from rogerthat.to.maps import MapButtonTO


class MapConfig(NdbModel):
    center = GeoPtProperty(indexed=False)  # type: GeoPt
    distance = IntegerProperty(indexed=False)
    filters = TextProperty(repeated=True)
    default_filter = TextProperty()
    buttons = TOProperty(MapButtonTO, repeated=True)  # type: List[MapButtonTO]

    @property
    def app_id(self):
        return self.key.id().split('~')[0]

    @classmethod
    def create_key(cls, app_id, map_tag):
        return Key(cls, '%s~%s' % (app_id, map_tag))


def migrate():
    map_configs = {m.app_id: m for m in MapConfig.query()}  # type: Dict[str, MapConfig]
    to_put = []
    for app in App.all():  # type: App
        if app.app_id in map_configs:
            for community_id in app.community_ids:
                map_config = map_configs[app.app_id]
                to_put.append(CommunityMapSettings(key=CommunityMapSettings.create_key(community_id),
                                                   center=map_config.center,
                                                   distance=map_config.distance,
                                                   layers=MapLayers()))
    return put_multi(to_put)
