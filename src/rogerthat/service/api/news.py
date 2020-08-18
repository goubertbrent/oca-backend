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

from types import NoneType

from mcfw.consts import MISSING
from mcfw.rpc import returns, arguments
from rogerthat.bizz import news
from rogerthat.bizz.news import get_news_share_base_url, get_news_share_url
from rogerthat.bizz.news.influx import get_news_item_time_statistics, get_basic_news_item_statistics
from rogerthat.bizz.service import get_and_validate_service_identity_user
from rogerthat.dal.profile import get_service_profile
from rogerthat.dal.service import get_service_identity
from rogerthat.models import BaseServiceProfile
from rogerthat.rpc import users
from rogerthat.rpc.service import service_api, service_api_callback
from rogerthat.settings import get_server_settings
from rogerthat.to.messaging import BaseMemberTO
from rogerthat.to.news import NewsActionButtonTO, NewsItemTO, NewsItemListResultTO, \
    NewsTargetAudienceTO, BaseMediaTO, NewsLocationsTO, ServiceNewsGroupTO, NewsItemBasicStatisticsTO, \
    NewsItemTimeStatisticsTO
from rogerthat.utils import bizz_check


@service_api(function=u'news.get', silent_result=True)
@returns(NewsItemTO)
@arguments(news_id=(int, long), service_identity=unicode)
def get(news_id, service_identity=None):
    service_user = users.get_current_user()
    service_identity_user = get_and_validate_service_identity_user(service_user, service_identity)
    news_item = news.get_and_validate_news_item(news_id, service_identity_user)
    service_profile = get_service_profile(service_user)
    si = get_service_identity(service_identity_user)
    server_settings = get_server_settings()
    share_base_url = get_news_share_base_url(server_settings.webClientUrl, si.defaultAppId, news_item.app_ids)
    share_url = get_news_share_url(share_base_url, news_item.id)
    return NewsItemTO.from_model(news_item, server_settings.baseUrl, service_profile, si, share_url=share_url)


@service_api(function=u'news.get_basic_statistics', silent_result=True)
@returns([NewsItemBasicStatisticsTO])
@arguments(ids=[(int, long)], service_identity=unicode)
def get_basic_statistics(ids, service_identity=None):
    service_user = users.get_current_user()
    service_identity_user = get_and_validate_service_identity_user(service_user, service_identity)
    news_items = news.get_and_validate_news_items(ids, service_identity_user)
    return get_basic_news_item_statistics(news_items)


@service_api(function=u'news.get_time_statistics', silent_result=True)
@returns(NewsItemTimeStatisticsTO)
@arguments(news_id=(int, long), service_identity=unicode)
def get_time_statistics(news_id, service_identity=None):
    service_user = users.get_current_user()
    service_identity_user = get_and_validate_service_identity_user(service_user, service_identity)
    news_item = news.get_and_validate_news_item(news_id, service_identity_user)
    return get_news_item_time_statistics(news_item)


@service_api(function=u'news.publish')
@returns(NewsItemTO)
@arguments(sticky=bool, sticky_until=(int, long), title=unicode, message=unicode, image=unicode, news_type=(int, long),
           action_buttons=[NewsActionButtonTO], qr_code_content=unicode,
           qr_code_caption=unicode, scheduled_at=(int, long), flags=int, news_id=(NoneType, int, long),
           app_ids=[unicode], service_identity=unicode, target_audience=NewsTargetAudienceTO, role_ids=[(long, int)],
           tags=[unicode], media=BaseMediaTO, locations=NewsLocationsTO, group_type=unicode,
           group_visible_until=(NoneType, int, long), timestamp=(NoneType, int, long))
def publish(sticky=MISSING, sticky_until=MISSING, title=MISSING, message=MISSING, image=MISSING, news_type=MISSING,
            action_buttons=MISSING, qr_code_content=MISSING, qr_code_caption=MISSING,
            scheduled_at=MISSING, flags=MISSING, news_id=None, app_ids=MISSING, service_identity=None,
            target_audience=None, role_ids=None, tags=None, media=MISSING, locations=None, group_type=MISSING,
            group_visible_until=None, timestamp=None):
    service_user = users.get_current_user()
    service_identity_user = get_and_validate_service_identity_user(service_user, service_identity)
    action_buttons = action_buttons if action_buttons is not MISSING else []
    news_item = news.put_news(service_identity_user, sticky, sticky_until, title, message, image, news_type,
                              action_buttons, qr_code_content, qr_code_caption, app_ids, scheduled_at, flags, news_id,
                              target_audience, role_ids, tags, media, locations, group_type, group_visible_until,
                              timestamp,
                              accept_missing=True)
    # Replace hashed tag with real tag
    if action_buttons and news_item.buttons:
        for button in news_item.buttons:
            for btn in action_buttons:
                if button.id == btn.id and button.action.startswith('poke://'):
                    button.action = btn.action
                    break
    service_profile = get_service_profile(service_user)
    si = get_service_identity(service_identity_user)
    server_settings = get_server_settings()
    share_base_url = get_news_share_base_url(server_settings.webClientUrl, si.defaultAppId, news_item.app_ids)
    share_url = get_news_share_url(share_base_url, news_item.id)
    return NewsItemTO.from_model(news_item, server_settings.baseUrl, service_profile, si, share_url)


@service_api(function=u'news.disable')
@returns()
@arguments(news_id=(int, long), members=[BaseMemberTO], service_identity=unicode)
def disable_news(news_id, members, service_identity=None):
    service_user = users.get_current_user()
    service_identity_user = get_and_validate_service_identity_user(service_user, service_identity)
    news.disable_news(service_identity_user, news_id, members)


@service_api(function=u'news.list')
@returns(NewsItemListResultTO)
@arguments(cursor=unicode, batch_count=(int, long), service_identity=unicode)
def list_news(cursor=None, batch_count=10, service_identity=None):
    bizz_check(batch_count <= 100, 'Cannot get more than 100 news items at once.')
    service_user = users.get_current_user()
    service_identity_user = get_and_validate_service_identity_user(service_user, service_identity)
    return news.get_news_by_service(cursor, batch_count, service_identity_user)


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


@service_api_callback(function=u"news.created", code=BaseServiceProfile.CALLBACK_NEWS_CREATED)
@returns(NoneType)
@arguments(news_item=NewsItemTO, service_identity=unicode)
def news_created(news_item, service_identity):
    pass


@service_api_callback(function=u"news.updated", code=BaseServiceProfile.CALLBACK_NEWS_UPDATED)
@returns(NoneType)
@arguments(news_item=NewsItemTO, service_identity=unicode)
def news_updated(news_item, service_identity):
    pass

@service_api_callback(function=u"news.deleted", code=BaseServiceProfile.CALLBACK_NEWS_DELETED)
@returns(NoneType)
@arguments(news_id=(int, long), service_identity=unicode)
def news_deleted(news_id, service_identity):
    pass

