# -*- coding: utf-8 -*-
# Copyright 2017 Mobicage NV
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
# @@license_version:1.2@@

import logging
from types import NoneType

from mcfw.consts import MISSING
from mcfw.properties import azzert
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.rpc import users
from rogerthat.rpc.service import ServiceApiException
from rogerthat.to import ReturnStatusTO, RETURNSTATUS_TO_SUCCESS, WarningReturnStatusTO
from rogerthat.to.news import NewsActionButtonTO, NewsTargetAudienceTO
from rogerthat.utils.service import create_service_identity_user
from shop.exceptions import BusinessException
from shop.to import OrderItemTO
from shop.view import get_current_http_host
from solutions import SOLUTION_COMMON, translate as common_translate
from solutions.common.bizz.news import get_news, put_news_item, delete_news, get_sponsored_news_count, \
    get_news_statistics, get_news_reviews, send_news_review_reply, publish_item_from_review, \
    AllNewsSentToReviewWarning
from solutions.common.dal import get_solution_settings
from solutions.common.dal.cityapp import get_service_user_for_city
from solutions.common.to.news import SponsoredNewsItemCount, NewsBroadcastItemTO, NewsBroadcastItemListTO, \
    NewsStatsTO, NewsReviewTO
from solutions.common.utils import is_default_service_identity


def _translate_exception_msg(sln_settings, msg):
    try:
        return common_translate(sln_settings.main_language, SOLUTION_COMMON, msg)
    except ValueError:
        return msg


@rest('/common/news', 'get', read_only_access=True, silent_result=True)
@returns(NewsBroadcastItemListTO)
@arguments(tag=unicode, cursor=unicode)
def rest_get_news(tag=None, cursor=None):
    service_identity = users.get_current_session().service_identity
    return get_news(cursor, service_identity, tag)


@rest('/common/news/statistics', 'get', read_only_access=True, silent_result=True)
@returns(NewsStatsTO)
@arguments(news_id=(int, long))
def rest_get_news_statistics(news_id):
    service_identity = users.get_current_session().service_identity
    return get_news_statistics(news_id, service_identity)


@rest('/common/news', 'post', silent_result=True)
@returns((NewsBroadcastItemTO, WarningReturnStatusTO))
@arguments(title=unicode, message=unicode, broadcast_type=unicode, image=(unicode, type(MISSING)), sponsored=bool,
           action_button=(NoneType, NewsActionButtonTO), order_items=[OrderItemTO],
           type=(int, long, type(MISSING)), qr_code_caption=(unicode, type(MISSING)),
           app_ids=[unicode], scheduled_at=(int, long), news_id=(int, long, NoneType), broadcast_on_facebook=bool,
           broadcast_on_twitter=bool, facebook_access_token=unicode, target_audience=NewsTargetAudienceTO,
           role_ids=[(int, long)], tag=unicode)
def rest_put_news_item(title, message, broadcast_type, image, sponsored=False, action_button=None, order_items=None,
                       type=MISSING, qr_code_caption=MISSING, app_ids=MISSING,  # @ReservedAssignment
                       scheduled_at=MISSING, news_id=None, broadcast_on_facebook=False, broadcast_on_twitter=False,
                       facebook_access_token=None, target_audience=None, role_ids=None, tag=None):
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
        broadcast_on_facebook (bool)
        broadcast_on_twitter (bool)
        facebook_access_token (unicode): user or page access token
        target_audience (NewsTargetAudienceTO)
        role_ids (list of long)
        tag (unicode)
    """
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    if is_default_service_identity(service_identity):
        service_identity_user = create_service_identity_user(service_user)
    else:
        service_identity_user = create_service_identity_user(service_user, service_identity)

    try:
        host = get_current_http_host()
        return put_news_item(
            service_identity_user, title, message, broadcast_type, sponsored, image, action_button,
            order_items, type, qr_code_caption, app_ids, scheduled_at, news_id, broadcast_on_facebook,
            broadcast_on_twitter, facebook_access_token, target_audience=target_audience, role_ids=role_ids,
            host=host, tag=tag, accept_missing=True)
    except AllNewsSentToReviewWarning as ex:
        return WarningReturnStatusTO.create(True, warningmsg=ex.message)
    except BusinessException as ex:
        sln_settings = get_solution_settings(service_user)
        message = _translate_exception_msg(sln_settings, ex.message)
        return WarningReturnStatusTO.create(False, message)


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


@rest('/common/news/reviews', 'get')
@returns([NewsReviewTO])
@arguments(app_id=unicode)
def rest_get_news_reviews(app_id):
    city_service = get_service_user_for_city(app_id)
    azzert(city_service == users.get_current_user())
    return map(NewsReviewTO.from_model, get_news_reviews(city_service))


@rest('/common/news/review/reply', 'post')
@returns(ReturnStatusTO)
@arguments(review_key=unicode, message=unicode)
def rest_send_news_review_reply(review_key, message):
    try:
        send_news_review_reply(review_key, message)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException:
        return ReturnStatusTO.create(False, None)


@rest('/common/news/review/publish', 'post')
@returns((ReturnStatusTO, NewsBroadcastItemTO))
@arguments(review_key=unicode)
def rest_publish_news_from_review(review_key):
    try:
        return publish_item_from_review(review_key)
    except BusinessException as ex:
        sln_settings = get_solution_settings(users.get_current_user())
        message = _translate_exception_msg(sln_settings, ex.message)
        return ReturnStatusTO.create(False, message)
