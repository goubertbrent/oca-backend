# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
# NOTICE: THIS FILE HAS BEEN MODIFIED BY GREEN VALLEY BELGIUM NV IN ACCORDANCE WITH THE APACHE LICENSE VERSION 2.0
# Copyright 2018 GIG Technology NV
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
# @@license_version:1.6@@

from types import NoneType

from mcfw.properties import azzert
from mcfw.restapi import rest
from mcfw.rpc import arguments, returns
from rogerthat.bizz.friend_helper import FriendHelper
from rogerthat.bizz.service import poke_service_by_hashed_tag
from rogerthat.dal.service import get_friend_serviceidentity_connection
from rogerthat.models import ServiceProfile
from rogerthat.models.properties.friend import FriendDetail
from rogerthat.rpc import users
from rogerthat.to.friends import FriendTO, FRIEND_TYPE_SERVICE
from rogerthat.to.service import FindServiceResponseTO
from rogerthat.utils import now
from rogerthat.utils.service import add_slash_default


@rest("/mobi/rest/services/poke_by_hashed_tag", "post")
@returns(NoneType)
@arguments(email=unicode, hashed_tag=unicode, context=unicode)
def poke_by_hashed_tag(email, hashed_tag, context):
    current_user = users.get_current_user()
    poke_service_by_hashed_tag(current_user, add_slash_default(users.User(email)), hashed_tag, context, now())
    return None


@rest("/mobi/rest/services/poke", "post")
@returns(NoneType)
@arguments(email=unicode, sid=unicode)
def poke(email, sid):
    from rogerthat.bizz.service import poke_service
    user = users.get_current_user()
    poke_service(user, add_slash_default(users.User(email)), sid, timestamp=now())


@rest("/mobi/rest/services/get", "get")
@returns([FriendTO])
@arguments()
def get():
    from rogerthat.dal.friend import get_friends_map
    user = users.get_current_user()
    friendMap = get_friends_map(user)
    return [FriendTO.fromDBFriendDetail(FriendHelper.from_data_store(users.User(f.email), f.type), f)
            for f in friendMap.friendDetails
            if f.type == FriendDetail.TYPE_SERVICE and f.existence == FriendDetail.FRIEND_EXISTENCE_ACTIVE]


@rest("/mobi/rest/services/get_full_service", "get")
@returns(FriendTO)
@arguments(service=unicode)
def get_full_service(service):
    from rogerthat.dal.friend import get_friends_map
    user = users.get_current_user()
    service_identity_user = add_slash_default(users.User(service))
    azzert(get_friend_serviceidentity_connection(user, service_identity_user),
           "%s tried to get full service %s, but is not connected to this service identity"
           % (user.email(), service_identity_user.email()))
    helper = FriendHelper.from_data_store(service_identity_user, FRIEND_TYPE_SERVICE)
    return FriendTO.fromDBFriendMap(helper, get_friends_map(user), service_identity_user, includeServiceDetails=True,
                                    targetUser=user)


@rest("/mobi/rest/services/press_menu_item", "post")
@returns(NoneType)
@arguments(service=unicode, coords=[int], generation=int, context=unicode)
def press_menu_item(service, coords, generation, context):
    # generation is service identity menuGeneration
    from rogerthat.bizz.service import press_menu_item as press_menu_item_bizz
    user = users.get_current_user()
    service_identity_user = add_slash_default(users.User(service))
    azzert(get_friend_serviceidentity_connection(user, service_identity_user),
           "%s tried to press menu item of service %s" % (user.email(), service))
    press_menu_item_bizz(user, service_identity_user, coords, context, generation, timestamp=now())


@rest("/mobi/rest/services/find", "post")
@returns(FindServiceResponseTO)
@arguments(search_string=unicode)
def find_service(search_string):
    from rogerthat.bizz.service import find_service as find_service_bizz
    user = users.get_current_user()
    # TODO: retrieve location from javascript (geo browser api) or map ip address
    return find_service_bizz(user, search_string, None, ServiceProfile.ORGANIZATION_TYPE_UNSPECIFIED)
