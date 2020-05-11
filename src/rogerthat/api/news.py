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

from mcfw.rpc import returns, arguments
from rogerthat.bizz.news.groups import get_group_id_for_type_and_app_id
from rogerthat.rpc import users
from rogerthat.rpc.rpc import expose
from rogerthat.to.news import GetNewsResponseTO, GetNewsRequestTO, GetNewsItemsResponseTO, GetNewsItemsRequestTO, \
    GetNewsGroupsResponseTO, GetNewsGroupsRequestTO, GetNewsStreamItemsResponseTO, GetNewsStreamItemsRequestTO, \
    GetNewsGroupServicesResponseTO, GetNewsGroupServicesRequestTO, SaveNewsGroupServicesResponseTO, \
    SaveNewsGroupServicesRequestTO, SaveNewsGroupFiltersResponseTO, SaveNewsGroupFiltersRequestTO, \
    GetNewsGroupResponseTO, GetNewsGroupRequestTO, SaveNewsStatisticsResponseTO, SaveNewsStatisticsRequestTO
from rogerthat.utils.app import get_app_id_from_app_user


@expose(('api',))
@returns(GetNewsResponseTO)
@arguments(request=GetNewsRequestTO)
def getNews(request):
    from rogerthat.bizz.news import get_news_for_user
    app_user = users.get_current_user()
    mobile = users.get_current_mobile()
    return get_news_for_user(app_user, request.cursor, request.updated_since, mobile)


@expose(('api',))
@returns(GetNewsItemsResponseTO)
@arguments(request=GetNewsItemsRequestTO)
def getNewsItems(request):
    from rogerthat.bizz.news import get_news_items_for_user
    app_user = users.get_current_user()
    return get_news_items_for_user(app_user, request.ids)


@expose(('api',))
@returns(SaveNewsStatisticsResponseTO)
@arguments(request=SaveNewsStatisticsRequestTO)
def saveNewsStatistics(request):
    from rogerthat.bizz.news import news_statistics
    app_user = users.get_current_user()
    news_statistics(app_user, request.type, request.news_ids)
    return SaveNewsStatisticsResponseTO()


@expose(('api',))
@returns(GetNewsGroupsResponseTO)
@arguments(request=GetNewsGroupsRequestTO)
def getNewsGroups(request):
    from rogerthat.bizz.news import get_groups_for_user
    app_user = users.get_current_user()
    return get_groups_for_user(app_user)


@expose(('api',))
@returns(GetNewsGroupResponseTO)
@arguments(request=GetNewsGroupRequestTO)
def getNewsGroup(request):
    # type: (GetNewsGroupRequestTO) -> GetNewsGroupResponseTO
    from rogerthat.bizz.news import get_news_group_response
    app_user = users.get_current_user()
    return get_news_group_response(app_user, request.group_id)


@expose(('api',))
@returns(GetNewsStreamItemsResponseTO)
@arguments(request=GetNewsStreamItemsRequestTO)
def getNewsStreamItems(request):
    # type: (GetNewsStreamItemsRequestTO) -> GetNewsStreamItemsResponseTO
    from rogerthat.bizz.news import get_items_for_user_by_group, get_items_for_user_by_service, \
        get_items_for_user_by_search_string
    app_user = users.get_current_user()
    app_id = get_app_id_from_app_user(app_user)
    if request.filter:
        if request.filter.group_type and not request.filter.group_id:
            request.filter.group_id = get_group_id_for_type_and_app_id(request.filter.group_type, app_id)
        if request.filter.search_string is not None:
            return get_items_for_user_by_search_string(app_user, request.filter.search_string, request.cursor)
        if request.filter.service_identity_email is not None:
            return get_items_for_user_by_service(app_user, request.filter.service_identity_email,
                                                 group_id=request.filter.group_id,
                                                 cursor=request.cursor)
        if request.filter.group_id is not None:
            return get_items_for_user_by_group(app_user, request.filter.group_id, request.cursor, request.news_ids)

    return GetNewsStreamItemsResponseTO(cursor=None, items=[])


@expose(('api',))
@returns(GetNewsGroupServicesResponseTO)
@arguments(request=GetNewsGroupServicesRequestTO)
def getNewsGroupServices(request):
    from rogerthat.bizz.news import get_group_services
    app_user = users.get_current_user()
    return get_group_services(app_user, request.group_id, request.key, request.cursor)


@expose(('api',))
@returns(SaveNewsGroupServicesResponseTO)
@arguments(request=SaveNewsGroupServicesRequestTO)
def saveNewsGroupServices(request):
    from rogerthat.bizz.news import save_group_services
    app_user = users.get_current_user()
    return save_group_services(app_user, request.group_id, request.key, request.action, request.service)


@expose(('api',))
@returns(SaveNewsGroupFiltersResponseTO)
@arguments(request=SaveNewsGroupFiltersRequestTO)
def saveNewsGroupFilters(request):
    from rogerthat.bizz.news import save_group_filters
    app_user = users.get_current_user()
    return save_group_filters(app_user, request.group_id, request.enabled_filters)
