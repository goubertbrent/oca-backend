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
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.bizz.communities.communities import get_community
from rogerthat.bizz.communities.models import CommunityGeoFence
from rogerthat.dal.profile import get_service_profile
from rogerthat.rpc import users


@rest('/common/community/geo-fence', 'get', read_only_access=True, silent_result=True)
@returns(dict)
@arguments()
def rest_get_geo_fence():
    service_profile = get_service_profile(users.get_current_user())
    fence = CommunityGeoFence.create_key(service_profile.community_id).get()
    if not fence:
        community = get_community(service_profile.community_id)
        return {'country': community.country}
    return fence.to_dict()
