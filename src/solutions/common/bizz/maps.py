# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley NV
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
from google.appengine.ext import ndb
from google.appengine.ext.ndb import GeoPt

from rogerthat.bizz.maps.gipod import GIPOD_TAG
from rogerthat.bizz.maps.reports import REPORTS_TAG
from rogerthat.models.maps import MapConfig
from solutions.common.to.reports import MapConfigTO


def get_map_settings(app_id, map_tag):
    # type: (str, str) -> MapConfig
    return MapConfig.create_key(app_id, map_tag).get()


@ndb.transactional(xg=True)
def save_map_settings(app_id, map_tag, data, is_shop_user):
    # type: (str, str, MapConfigTO, bool) -> MapConfig
    all_tags = [GIPOD_TAG, REPORTS_TAG]
    models = ndb.get_multi([MapConfig.create_key(app_id, tag) for tag in all_tags])  # type: list[MapConfig]
    to_put = []
    config = None
    for tag, model in zip(all_tags, models):
        if not model:
            model = MapConfig(key=MapConfig.create_key(app_id, tag))
        model.center = GeoPt(data.center.lat, data.center.lon)
        model.distance = data.distance
        if model.tag == map_tag:
            if is_shop_user:
                model.buttons = data.buttons
            model.default_filter = data.default_filter
            model.filters = data.filters
            config = model
        to_put.append(model)
    ndb.put_multi(to_put)
    return config
