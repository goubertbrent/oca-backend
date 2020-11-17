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

from __future__ import unicode_literals

from datetime import datetime

from google.appengine.ext import ndb
from typing import Optional, Tuple

from mcfw.exceptions import HttpNotFoundException
from mcfw.restapi import rest, GenericRESTRequestHandler
from mcfw.rpc import returns, arguments
from rogerthat.bizz.communities.communities import get_community
from rogerthat.bizz.news import get_news_share_base_url, get_news_share_url, save_web_news_item_action_statistic
from rogerthat.dal.profile import get_service_profile
from rogerthat.dal.service import get_service_identity
from rogerthat.models import AppNameMapping
from rogerthat.models.news import NewsItem
from rogerthat.settings import get_server_settings
from rogerthat.templates import get_language_from_request
from rogerthat.to.news import NewsItemTO
from rogerthat.utils import try_or_defer
from rogerthat.utils.service import get_service_user_from_service_identity_user
from rogerthat.web_client.pages.web_client import handle_web_request
from solutions import translate


@returns(tuple)
@arguments(app_name=unicode, news_id=(int, long), language=unicode)
def get_news_item_details(app_name, news_id, language=None):
    # type: (unicode, long, unicode) -> Tuple[NewsItem, Optional[AppNameMapping], NewsItemTO]
    news_item, app_name_mapping = ndb.get_multi([
        NewsItem.create_key(news_id),
        AppNameMapping.create_key(app_name)
    ])  # type: NewsItem, AppNameMapping
    if not news_item:
        if not language:
            language = get_language_from_request(GenericRESTRequestHandler.getCurrentRequest())
        msg = translate(language, 'news_item_not_found')
        raise HttpNotFoundException('web.translated-error', {'message': msg})
    server_settings = get_server_settings()
    si_user = news_item.sender
    service_profile = get_service_profile(get_service_user_from_service_identity_user(si_user))
    service_identity = get_service_identity(si_user)
    app_id = app_name_mapping.app_id if app_name_mapping else get_community(service_profile.community_id).default_app
    share_base_url = get_news_share_base_url(server_settings.webClientUrl, app_id=app_id)
    share_url = get_news_share_url(share_base_url, news_item.id)
    return news_item, app_name_mapping, NewsItemTO.from_model(news_item, server_settings.baseUrl, service_profile,
                                                              service_identity, share_url=share_url)


@rest('/api/web/<app_name:[^/]+>/news/id/<news_id:\d+>', 'get')
@returns(NewsItemTO)
@arguments(app_name=unicode, news_id=(int, long), language=unicode)
def rest_get_news_item(app_name, news_id, language=None):
    return get_news_item_details(app_name, news_id, language=language)[2]


@rest('/api/web/<app_name:[^/]+>/news/id/<news_id:\d+>/action/<action:[^/]+>', 'post')
@returns()
@arguments(app_name=unicode, news_id=(int, long), action=unicode)
def rest_save_news_action(app_name, news_id, action):
    app_name_mapping = AppNameMapping.create_key(app_name).get()  # type: AppNameMapping
    if not app_name_mapping:
        raise HttpNotFoundException('No app found for name "%s"' % app_name)
    session = handle_web_request(GenericRESTRequestHandler.getCurrentRequest(),
                                 GenericRESTRequestHandler.getCurrentResponse())
    try_or_defer(save_web_news_item_action_statistic, session, app_name_mapping.app_id, news_id, action, datetime.now())
    return None
