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

import logging
import time
from types import NoneType

from mcfw.consts import MISSING
from mcfw.rpc import returns, arguments
from rogerthat.bizz import news
from rogerthat.bizz.news import get_news_items_statistics
from rogerthat.bizz.service import get_and_validate_service_identity_user
from rogerthat.rpc import users
from rogerthat.rpc.service import service_api
from rogerthat.settings import get_server_settings
from rogerthat.to.messaging import BaseMemberTO
from rogerthat.to.news import NewsActionButtonTO, NewsItemTO, NewsItemListResultTO, \
    NewsTargetAudienceTO, NewsFeedNameTO, BaseMediaTO, NewsLocationsTO, \
    ServiceNewsGroupTO
from rogerthat.utils import bizz_check


@service_api(function=u'news.get', silent_result=True)
@returns(NewsItemTO)
@arguments(news_id=(int, long), service_identity=unicode, include_statistics=bool)
def get(news_id, service_identity=None, include_statistics=False):
    t = time.time()
    service_user = users.get_current_user()
    service_identity_user = get_and_validate_service_identity_user(service_user, service_identity)
    news_item = news.get_news(service_identity_user, news_id)
    logging.info('Fetching news item took %s', time.time() - t)
    statistics = get_news_items_statistics([news_item], True).get(news_id) if include_statistics else None
    return NewsItemTO.from_model(news_item, get_server_settings().baseUrl, statistics)


@service_api(function=u'news.publish')
@returns(NewsItemTO)
@arguments(sticky=bool, sticky_until=(int, long), title=unicode, message=unicode, image=unicode, news_type=(int, long),
           action_buttons=[NewsActionButtonTO], qr_code_content=unicode,
           qr_code_caption=unicode, scheduled_at=(int, long), flags=int, news_id=(NoneType, int, long),
           app_ids=[unicode], service_identity=unicode, target_audience=NewsTargetAudienceTO, role_ids=[(long, int)],
           tags=[unicode], feed_names=[NewsFeedNameTO], media=BaseMediaTO, locations=NewsLocationsTO, group_type=unicode,
           group_visible_until=(NoneType, int, long), timestamp=(NoneType, int, long))
def publish(sticky=MISSING, sticky_until=MISSING, title=MISSING, message=MISSING, image=MISSING, news_type=MISSING,
            action_buttons=MISSING, qr_code_content=MISSING, qr_code_caption=MISSING,
            scheduled_at=MISSING, flags=MISSING, news_id=None, app_ids=MISSING, service_identity=None,
            target_audience=None, role_ids=None, tags=None, feed_names=None, media=MISSING, locations=None, group_type=MISSING,
            group_visible_until=None, timestamp=None):
    service_user = users.get_current_user()
    service_identity_user = get_and_validate_service_identity_user(service_user, service_identity)
    action_buttons = action_buttons if action_buttons is not MISSING else []
    news_item = news.put_news(service_identity_user, sticky, sticky_until, title, message, image, news_type,
                              action_buttons, qr_code_content, qr_code_caption, app_ids, scheduled_at, flags, news_id,
                              target_audience, role_ids, tags, feed_names, media, locations, group_type, group_visible_until, timestamp,
                              accept_missing=True)
    # Replace hashed tag with real tag
    if action_buttons and news_item.buttons:
        for button in news_item.buttons:
            for btn in action_buttons:
                if button.id == btn.id and button.action.startswith('poke://'):
                    button.action = btn.action
                    break
    return NewsItemTO.from_model(news_item, get_server_settings().baseUrl)


@service_api(function=u'news.disable')
@returns()
@arguments(news_id=(int, long), members=[BaseMemberTO], service_identity=unicode)
def disable_news(news_id, members, service_identity=None):
    service_user = users.get_current_user()
    service_identity_user = get_and_validate_service_identity_user(service_user, service_identity)
    news.disable_news(service_identity_user, news_id, members)


@service_api(function=u'news.list')
@returns(NewsItemListResultTO)
@arguments(cursor=unicode, batch_count=(int, long), service_identity=unicode, updated_since=(int, long),
           tag=unicode)
def list_news(cursor=None, batch_count=10, service_identity=None, updated_since=0, tag=None):
    bizz_check(batch_count <= 100, 'Cannot get more than 100 news items at once.')
    service_user = users.get_current_user()
    service_identity_user = get_and_validate_service_identity_user(service_user, service_identity)
    return news.get_news_by_service(cursor, batch_count, service_identity_user, updated_since, tag)


@service_api(function=u'news.list_groups')
@returns([ServiceNewsGroupTO])
@arguments(language=unicode)
def list_groups(language=None):
    service_user = users.get_current_user()
    return news.groups.get_groups_for_service_user(service_user, language=language)


@service_api(function=u'news.delete')
@returns(bool)
@arguments(news_id=(int, long), service_identity=unicode)
def delete(news_id, service_identity=None):
    service_user = users.get_current_user()
    service_identity_user = get_and_validate_service_identity_user(service_user, service_identity)
    return news.delete(news_id, service_identity_user)