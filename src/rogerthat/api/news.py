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

from mcfw.properties import unicode_property, typed_property
from mcfw.rpc import returns, arguments
from rogerthat.rpc import users
from rogerthat.rpc.rpc import expose
from rogerthat.to import TO
from rogerthat.to.news import GetNewsGroupsResponseTO, GetNewsGroupsRequestTO, GetNewsStreamItemsResponseTO, \
    GetNewsStreamItemsRequestTO, \
    GetNewsGroupServicesResponseTO, GetNewsGroupServicesRequestTO, SaveNewsGroupServicesResponseTO, \
    SaveNewsGroupServicesRequestTO, SaveNewsGroupFiltersResponseTO, SaveNewsGroupFiltersRequestTO, \
    GetNewsGroupResponseTO, GetNewsGroupRequestTO, SaveNewsStatisticsResponseTO, SaveNewsStatisticsRequestTO, \
    GetNewsItemDetailsResponseTO, GetNewsItemDetailsRequestTO


class GetNewsRequestTO(TO):
    pass


class GetNewsResponseTO(TO):
    cursor = unicode_property('1')
    result = typed_property('2', dict, True)


class GetNewsItemsRequestTO(TO):
    pass


class GetNewsItemsResponseTO(TO):
    items = typed_property('1', dict, True)


# Backwards compat - just return an empty list
@expose(('api',))
@returns(GetNewsResponseTO)
@arguments(request=GetNewsRequestTO)
def getNews(request):
    return GetNewsResponseTO(cursor=None, result=[])


# Backwards compat - just return an empty list
@expose(('api',))
@returns(GetNewsItemsResponseTO)
@arguments(request=GetNewsItemsRequestTO)
def getNewsItems(request):
    return GetNewsItemsResponseTO(items=[])


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
    from rogerthat.bizz.news import get_items_for_filter
    app_user = users.get_current_user()
    if request.filter:
        return get_items_for_filter(request.filter, request.news_ids, request.cursor, app_user)

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


# Deprecated but not removed for old client support
@expose(('api',))
@returns(SaveNewsGroupFiltersResponseTO)
@arguments(request=SaveNewsGroupFiltersRequestTO)
def saveNewsGroupFilters(request):
    return SaveNewsGroupFiltersResponseTO()


@expose(('api',))
@returns(GetNewsItemDetailsResponseTO)
@arguments(request=GetNewsItemDetailsRequestTO)
def getNewsItemDetails(request):
    # type: (GetNewsItemDetailsRequestTO) -> GetNewsItemDetailsResponseTO
    from rogerthat.bizz.news import get_news_item_details
    app_user = users.get_current_user()
    return get_news_item_details(app_user, request.id)
