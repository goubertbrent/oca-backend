# -*- coding: utf-8 -*-
# Copyright 2016 Mobicage NV
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
# @@license_version:1.1@@

import logging
from types import NoneType

from mcfw.consts import MISSING
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.rpc import users
from rogerthat.rpc.service import ServiceApiException
from rogerthat.to import ReturnStatusTO
from rogerthat.to.news import NewsItemListResultTO, NewsItemTO, NewsActionButtonTO
from rogerthat.utils.service import create_service_identity_user
from shop.to import NewsTO, OrderItemTO
from solutions.common.bizz.news import get_news, put_news_item, delete_news, get_sponsored_news_count, \
    get_news_statistics
from solutions.common.dal import get_solution_settings
from solutions.common.to.news import SponsoredNewsItemCount
from solutions.common.utils import is_default_service_identity
from solutions.flex.bizz import get_all_news


@rest("/common/news/all", "get", read_only_access=True, silent_result=True)
@returns([NewsTO])
@arguments()
def load_news():
    service_user = users.get_current_user()
    settings = get_solution_settings(service_user)
    return [NewsTO.create(n) for n in get_all_news(settings.main_language)]


@rest('/common/news', 'get', read_only_access=True, silent_result=True)
@returns(NewsItemListResultTO)
@arguments(cursor=unicode)
def rest_get_news(cursor=None):
    service_identity = users.get_current_session().service_identity
    return get_news(cursor, service_identity)


@rest('/common/news/statistics', 'get', read_only_access=True, silent_result=True)
@returns(NewsItemTO)
@arguments(news_id=(int, long))
def rest_get_news_statistics(news_id):
    service_identity = users.get_current_session().service_identity
    return get_news_statistics(news_id, service_identity)


@rest('/common/news', 'post', silent_result=True)
@returns(NewsItemTO)
@arguments(title=unicode, message=unicode, broadcast_type=unicode, image=(unicode, type(MISSING)), sponsored=bool,
           action_button=(NoneType, NewsActionButtonTO), order_items=[OrderItemTO],
           type=(int, long, type(MISSING)), qr_code_caption=(unicode, type(MISSING)), app_ids=[unicode],
           scheduled_at=(int, long), news_id=(int, long, NoneType))
def rest_put_news_item(title, message, broadcast_type, image, sponsored=False, action_button=None, order_items=None,
                       type=MISSING, qr_code_caption=MISSING, app_ids=MISSING, scheduled_at=MISSING, news_id=None):  # @ReservedAssignment
    """
    Args:
        title (unicode)
        message (unicode)
        broadcast_type (unicode)
        sponsored (bool)
        image (unicode)
        action_button (NewsButtonTO)
        order_items (list of OrderItemTO)
        type (int)
        qr_code_caption (unicode)
        app_ids (list of unicode)
        scheduled_at (long)
        news_id (long): id of the news to update. When not specified a new item is created
    """
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    if is_default_service_identity(service_identity):
        service_identity_user = create_service_identity_user(service_user)
    else:
        service_identity_user = create_service_identity_user(service_user, service_identity)

    return put_news_item(service_identity_user, title, message, broadcast_type, sponsored, image, action_button,
                         order_items, type, qr_code_caption, app_ids, scheduled_at, news_id, accept_missing=True)


@rest('/common/news/delete', 'post')
@returns(ReturnStatusTO)
@arguments(news_id=(int, long))
def rest_delete_news(news_id):
    try:
        delete_news(news_id)
        return ReturnStatusTO.create(True, None)
    except ServiceApiException as e:
        logging.exception(e)
        return ReturnStatusTO.create(False, None)


@rest('/common/news/promoted_cost', 'post')
@returns([SponsoredNewsItemCount])
@arguments(app_ids=[unicode])
def rest_get_news_promoted_count(app_ids):
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    if is_default_service_identity(service_identity):
        service_identity_user = create_service_identity_user(service_user)
    else:
        service_identity_user = create_service_identity_user(service_user, service_identity)
    return get_sponsored_news_count(service_identity_user, app_ids)
