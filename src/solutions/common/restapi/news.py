# -*- coding: utf-8 -*-
# Copyright 2018 Mobicage NV
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
# @@license_version:1.3@@

from types import NoneType

from mcfw.consts import MISSING, REST_TYPE_TO
from mcfw.exceptions import HttpBadRequestException
from mcfw.properties import azzert
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.rpc import users
from rogerthat.rpc.service import ServiceApiException
from rogerthat.to import ReturnStatusTO, RETURNSTATUS_TO_SUCCESS, WarningReturnStatusTO
from rogerthat.utils.service import create_service_identity_user
from shop.exceptions import BusinessException
from shop.view import get_current_http_host
from solutions import SOLUTION_COMMON, translate as common_translate
from solutions.common.bizz.news import get_news, put_news_item, delete_news, get_sponsored_news_count, \
    get_news_statistics, get_news_reviews, send_news_review_reply, publish_item_from_review, \
    AllNewsSentToReviewWarning
from solutions.common.dal import get_solution_settings
from solutions.common.dal.cityapp import get_service_user_for_city
from solutions.common.to.news import SponsoredNewsItemCount, NewsBroadcastItemTO, NewsBroadcastItemListTO, \
    NewsStatsTO, NewsReviewTO, CreateNewsItemTO
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


@rest('/common/news/<news_id:\d+>', 'get', read_only_access=True, silent_result=True)
@returns(NewsStatsTO)
@arguments(news_id=(int, long))
def rest_get_news_statistics(news_id):
    service_identity = users.get_current_session().service_identity
    return get_news_statistics(news_id, service_identity)


@rest('/common/news/<news_id:\d+>', 'put', silent_result=True, type=REST_TYPE_TO)
@returns(NewsBroadcastItemTO)
@arguments(news_id=(int, long, NoneType), data=CreateNewsItemTO)
def rest_put_news_item(news_id, data):
    # type: (int, CreateNewsItemTO) -> NewsBroadcastItemTO
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
            service_identity_user, data.title, data.message, data.broadcast_type, False, MISSING,
            MISSING.default(data.action_button, None), [], data.type, data.qr_code_caption, data.app_ids,
            data.scheduled_at, news_id, data.broadcast_on_facebook, data.broadcast_on_twitter,
            data.facebook_access_token, target_audience=data.target_audience, role_ids=data.role_ids, host=host,
            tag=data.tag, media=data.media, accept_missing=True)
    # TODO http 400 instead of this
    except AllNewsSentToReviewWarning as ex:
        return WarningReturnStatusTO.create(True, warningmsg=ex.message)
    except BusinessException as ex:
        sln_settings = get_solution_settings(service_user)
        message = _translate_exception_msg(sln_settings, ex.message)
        return WarningReturnStatusTO.create(False, message)


@rest('/common/news', 'post', silent_result=True, type=REST_TYPE_TO)
@returns(NewsBroadcastItemTO)
@arguments(data=CreateNewsItemTO)
def rest_create_news_item(data):
    return rest_put_news_item(None, data)


@rest('/common/news/<news_id:\d+>', 'delete')
@returns()
@arguments(news_id=(int, long))
def rest_delete_news(news_id):
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    try:
        delete_news(news_id, service_identity)
    except ServiceApiException as e:
        raise HttpBadRequestException(e.message)


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
