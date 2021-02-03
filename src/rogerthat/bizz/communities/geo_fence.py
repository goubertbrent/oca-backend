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
from google.appengine.ext.ndb.model import GeoPt

from rogerthat.bizz.communities.communities import get_community
from rogerthat.bizz.communities.models import CommunityGeoFence, CommunityLocation, GeoFenceGeometry
from rogerthat.bizz.communities.to import CommunityGeoFenceTO


def get_geo_fence(community_id):
    # type: (int) -> CommunityGeoFence
    key = CommunityGeoFence.create_key(community_id)
    fence = key.get()  # type: CommunityGeoFence
    if not fence:
        fence = CommunityGeoFence(key=key)
        fence.country = get_community(community_id).country
    return fence


def update_geo_fence(community_id, data):
    # type: (int, CommunityGeoFenceTO) -> CommunityGeoFence
    fence = get_geo_fence(community_id)
    fence.defaults = None
    if data.defaults:
        fence.defaults = CommunityLocation(locality=data.defaults.locality,
                                           postal_code=data.defaults.postal_code)
    fence.geometry = None
    if data.geometry:
        fence.geometry = GeoFenceGeometry(center=GeoPt(data.geometry.center.lat, data.geometry.center.lon),
                                          max_distance=data.geometry.max_distance)
    fence.put()
    return fence
