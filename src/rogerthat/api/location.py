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

from mcfw.rpc import returns, arguments
from rogerthat.rpc.rpc import expose
from rogerthat.to.location import GetFriendLocationRequestTO, GetFriendLocationResponseTO, \
    GetFriendsLocationResponseTO, GetFriendsLocationRequestTO, GetLocationRequestTO
from rogerthat.utils.app import create_app_user, get_app_id_from_app_user


@expose(('api',))
@returns(GetFriendLocationResponseTO)
@arguments(request=GetFriendLocationRequestTO)
def get_friend_location(request):
    from rogerthat.rpc import users
    from rogerthat.bizz.location import get_friend_location as bizz_get_friend_location
    user = users.get_current_user()
    bizz_get_friend_location(user, create_app_user(users.User(request.friend), get_app_id_from_app_user(user)),
                             target=GetLocationRequestTO.TARGET_MOBILE)
    response = GetFriendLocationResponseTO()
    response.location = None  # for backwards compatibility reasons
    return response


@expose(('api',))
@returns(GetFriendsLocationResponseTO)
@arguments(request=GetFriendsLocationRequestTO)
def get_friend_locations(request):
    from rogerthat.rpc import users
    from rogerthat.bizz.location import get_friend_locations as bizz_get_friend_locations
    user = users.get_current_user()
    response = GetFriendsLocationResponseTO()
    response.locations = bizz_get_friend_locations(user)
    return response
