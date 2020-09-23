# -*- coding: utf-8 -*-
# Copyright 2020 Green Valley NV
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
from typing import List

from mcfw.rpc import returns, arguments
from rogerthat.bizz.app import get_community_statistics
from rogerthat.bizz.service import get_and_validate_service_identity_user
from rogerthat.rpc import users
from rogerthat.rpc.service import service_api
from rogerthat.to.statistics import CommunityUserStatisticsTO


@service_api(function=u'communities.get_statistics')
@returns([CommunityUserStatisticsTO])
@arguments(community_ids=[(int, long)], service_identity=unicode)
def get_statistics(community_ids, service_identity=None):
    # type: (List[long], unicode) -> List[CommunityUserStatisticsTO]
    service_user = users.get_current_user()
    get_and_validate_service_identity_user(service_user, service_identity)
    return get_community_statistics(community_ids)
