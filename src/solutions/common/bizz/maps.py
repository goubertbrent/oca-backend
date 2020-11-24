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
from google.appengine.ext.ndb import GeoPt
from typing import List

from rogerthat.bizz.maps.gipod import GIPOD_TAG
from rogerthat.bizz.maps.reports import REPORTS_TAG
from rogerthat.bizz.maps.services import SERVICES_TAG
from rogerthat.models.maps import MapConfig
from rogerthat.to.maps import MapConfigTO


def get_map_settings(app_id, map_tag):
    # type: (str, str) -> MapConfig
    return MapConfig.create_key(app_id, map_tag).get()


@ndb.transactional(xg=True)
def save_map_settings(app_id, map_tag, data):
    # type: (str, str, MapConfigTO) -> MapConfig
    all_tags = [GIPOD_TAG, REPORTS_TAG, SERVICES_TAG]
    models = ndb.get_multi([MapConfig.create_key(app_id, tag) for tag in all_tags])  # type: List[MapConfig]
    to_put = []
    config = None
    # Duplicate the default center / distance to all maps
    for tag, model in zip(all_tags, models):
        if not model:
            model = MapConfig(key=MapConfig.create_key(app_id, tag))
        model.center = GeoPt(data.center.lat, data.center.lon)
        model.distance = data.distance
        if model.tag == map_tag:
            model.buttons = data.buttons
            model.default_filter = data.default_filter
            model.filters = data.filters
            config = model
        to_put.append(model)
    ndb.put_multi(to_put)
    return config
