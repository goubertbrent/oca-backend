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
from mcfw.consts import REST_TYPE_TO
from mcfw.restapi import rest, GenericRESTRequestHandler
from mcfw.rpc import returns, arguments
from rogerthat.bizz.communities.communities import create_community, get_community, get_communities_by_country, \
    update_community, get_all_community_countries, delete_community
from rogerthat.bizz.communities.homescreen.homescreen import get_temporary_home_screen, save_temporary_home_screen, \
    publish_home_screen, get_home_screen_translations, test_home_screen
from rogerthat.bizz.communities.homescreen.to import TestHomeScreenTO
from rogerthat.bizz.communities.news import get_news_settings, upload_news_background_image, update_news_stream
from rogerthat.bizz.communities.to import CommunityTO, BaseCommunityTO
from rogerthat.to.news import NewsSettingsTO, NewsGroupConfigTO, NewsSettingsWithGroupsTO


@rest('/console-api/communities/countries', 'get')
@returns([dict])
@arguments()
def rest_get_community_countries():
    return get_all_community_countries()


@rest('/console-api/communities', 'get')
@returns([CommunityTO])
@arguments(country=unicode)
def rest_get_communities(country=None):
    return [CommunityTO.from_model(c) for c in get_communities_by_country(country, live_only=False)]


@rest('/console-api/communities', 'post', type=REST_TYPE_TO)
@returns(CommunityTO)
@arguments(data=BaseCommunityTO)
def rest_create_community(data):
    return CommunityTO.from_model(create_community(data))


@rest('/console-api/communities/<community_id:\d+>', 'get', type=REST_TYPE_TO)
@returns(CommunityTO)
@arguments(community_id=(int, long))
def rest_get_community(community_id):
    return CommunityTO.from_model(get_community(community_id))


@rest('/console-api/communities/<community_id:\d+>', 'put', type=REST_TYPE_TO)
@returns(CommunityTO)
@arguments(community_id=(int, long), data=BaseCommunityTO)
def rest_update_community(community_id, data):
    return CommunityTO.from_model(update_community(community_id, data))


@rest('/console-api/communities/<community_id:\d+>', 'delete')
@returns()
@arguments(community_id=(int, long))
def rest_delete_community(community_id):
    delete_community(community_id, True)


@rest('/console-api/communities/<community_id:\d+>/news-settings', 'get')
@returns(NewsSettingsWithGroupsTO)
@arguments(community_id=(int, long))
def api_get_news_settings(community_id):
    return get_news_settings(community_id)


@rest('/console-api/communities/<community_id:\d+>/news-settings', 'put')
@returns(NewsSettingsTO)
@arguments(community_id=(int, long), data=NewsSettingsTO)
def api_save_news_stream(community_id, data):
    # type: (long, NewsSettingsTO) -> NewsSettingsTO
    return update_news_stream(community_id, data.stream_type)


@rest('/console-api/communities/<community_id:\d+>/news-settings/<group_id:[^/]+>/background-image', 'put')
@returns(NewsGroupConfigTO)
@arguments(community_id=(int, long), group_id=unicode)
def api_upload_news_background_image(community_id, group_id):
    request = GenericRESTRequestHandler.getCurrentRequest()
    uploaded_file = request.POST.get('file')
    return upload_news_background_image(community_id, group_id, uploaded_file)


@rest('/console-api/communities/<community_id:\d+>/home-screen/<home_screen_id:[^/]+>', 'get')
@returns(dict)
@arguments(community_id=(int, long), home_screen_id=unicode)
def api_get_home_screen(community_id, home_screen_id):
    return get_temporary_home_screen(community_id, home_screen_id)


@rest('/console-api/communities/<community_id:\d+>/home-screen/<home_screen_id:[^/]+>', 'put')
@returns(dict)
@arguments(community_id=(int, long), home_screen_id=unicode, data=dict)
def api_save_home_screen(community_id, home_screen_id, data):
    return save_temporary_home_screen(community_id, home_screen_id, data)


@rest('/console-api/communities/<community_id:\d+>/home-screen/<home_screen_id:[^/]+>/publish', 'put')
@returns()
@arguments(community_id=(int, long), home_screen_id=unicode)
def api_publish_home_screen(community_id, home_screen_id):
    return publish_home_screen(community_id, home_screen_id)


@rest('/console-api/communities/<community_id:\d+>/home-screen/<home_screen_id:[^/]+>/test', 'post', type=REST_TYPE_TO)
@returns()
@arguments(community_id=(int, long), home_screen_id=unicode, data=TestHomeScreenTO)
def api_test_home_screen(community_id, home_screen_id, data):
    # type: (int, unicode, TestHomeScreenTO) -> None
    test_home_screen(community_id, home_screen_id, data.test_user)


@rest('/console-api/home-screen-translations', 'get')
@returns([dict])
@arguments()
def api_get_home_screen_translations():
    return get_home_screen_translations()
