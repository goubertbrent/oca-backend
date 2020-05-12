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

from __future__ import unicode_literals

from mcfw.rpc import returns, arguments
from rogerthat.bizz.maps import gipod, reports, services
from rogerthat.rpc import users
from rogerthat.rpc.rpc import expose
from rogerthat.to.maps import GetMapResponseTO, GetMapRequestTO, GetMapItemsResponseTO, GetMapItemsRequestTO, \
    SaveMapNotificationsResponseTO, SaveMapNotificationsRequestTO, GetMapItemDetailsRequestTO, \
    GetMapItemDetailsResponseTO, SaveMapItemVoteResponseTO, SaveMapItemVoteRequestTO, ToggleMapItemResponseTO, \
    ToggleMapItemRequestTO, GetSavedMapItemsResponseTO, GetSavedMapItemsRequestTO, ToggleListSectionItemTO, \
    GetMapSearchSuggestionsResponseTO, GetMapSearchSuggestionsRequestTO


@expose(('api',))
@returns(GetMapResponseTO)
@arguments(request=GetMapRequestTO)
def getMap(request):
    app_user = users.get_current_user()
    if request.tag == gipod.GIPOD_TAG:
        return gipod.get_map(app_user)
    if request.tag == reports.REPORTS_TAG:
        return reports.get_map(app_user)
    if request.tag == services.SERVICES_TAG:
        return services.get_map(app_user)
    raise Exception('incorrect_tag')  # todo maps error message?


@expose(('api',))
@returns(GetMapSearchSuggestionsResponseTO)
@arguments(request=GetMapSearchSuggestionsRequestTO)
def getMapSearchSuggestions(request):
    app_user = users.get_current_user()
    if request.tag == services.SERVICES_TAG:
        return services.get_map_search_suggestions(app_user, request)
    raise Exception('incorrect_tag')  # todo maps error message?


@expose(('api',))
@returns(GetMapItemsResponseTO)
@arguments(request=GetMapItemsRequestTO)
def getMapItems(request):
    app_user = users.get_current_user()
    if request.tag == gipod.GIPOD_TAG:
        return gipod.get_map_items(app_user, request)
    if request.tag == reports.REPORTS_TAG:
        return reports.get_map_items(app_user, request)
    if request.tag == services.SERVICES_TAG:
        return services.get_map_items(app_user, request)
    raise Exception('incorrect_tag')  # todo maps error message?


@expose(('api',))
@returns(GetMapItemDetailsResponseTO)
@arguments(request=GetMapItemDetailsRequestTO)
def getMapItemDetails(request):
    app_user = users.get_current_user()
    if request.tag == gipod.GIPOD_TAG:
        return gipod.get_map_item_details(app_user, request)
    if request.tag == reports.REPORTS_TAG:
        return reports.get_map_item_details(app_user, request)
    if request.tag == services.SERVICES_TAG:
        return services.get_map_item_details(app_user, request)
    raise Exception('incorrect_tag')  # todo maps error message?


@expose(('api',))
@returns(SaveMapNotificationsResponseTO)
@arguments(request=SaveMapNotificationsRequestTO)
def saveMapNotifications(request):
    app_user = users.get_current_user()
    if request.tag == gipod.GIPOD_TAG:
        return gipod.save_map_notifications(app_user, request)
    raise Exception('incorrect_tag')  # todo maps error message?


@expose(('api',))
@returns(ToggleMapItemResponseTO)
@arguments(request=ToggleMapItemRequestTO)
def toggleMapItem(request):
    app_user = users.get_current_user()
    if request.tag == services.SERVICES_TAG:
        if request.toggle_id == ToggleListSectionItemTO.TOGGLE_ID_SAVE:
            return services.save_map_item(app_user, request)
        raise Exception('incorrect_toggle_action')
    raise Exception('incorrect_tag')  # todo maps error message?


@expose(('api',))
@returns(GetSavedMapItemsResponseTO)
@arguments(request=GetSavedMapItemsRequestTO)
def getSavedMapItems(request):
    app_user = users.get_current_user()
    if request.tag == services.SERVICES_TAG:
        return services.get_saved_map_items(app_user, request)
    raise Exception('incorrect_tag')  # todo maps error message?


@expose(('api',))
@returns(SaveMapItemVoteResponseTO)
@arguments(request=SaveMapItemVoteRequestTO)
def saveMapItemVote(request):
    app_user = users.get_current_user()
    if request.tag == reports.REPORTS_TAG:
        return reports.save_map_item_vote(app_user, request)
    raise Exception('incorrect_tag')  # todo maps error message?
