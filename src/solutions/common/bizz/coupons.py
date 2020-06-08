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

import json
import logging

from mcfw.rpc import arguments, serialize_complex_value
from mcfw.rpc import returns
from rogerthat.bizz.service import get_and_validate_service_identity_user
from rogerthat.rpc import users
from rogerthat.service.api import news
from rogerthat.to.messaging import BaseMemberTO
from rogerthat.to.news import NewsItemTO
from rogerthat.to.service import SendApiCallCallbackResultTO, UserDetailsTO
from rogerthat.utils import now
from rogerthat.utils.app import get_app_user_tuple
from rogerthat.utils.service import get_identity_from_service_identity_user
from rogerthat.utils.transactions import run_in_xg_transaction
from solutions import translate
from solutions.common.dal import get_solution_settings
from solutions.common.exceptions.news import NewsCouponNotFoundException, NewsCouponAlreadyUsedException
from solutions.common.models.news import NewsCoupon, RedeemedBy
from solutions.common.to.coupons import NewsCouponTO

API_METHOD_SOLUTION_COUPON_RESOLVE = 'solutions.coupons.resolve'
API_METHOD_SOLUTION_COUPON_REDEEM = 'solutions.coupons.redeem'


def t(lang, key):
    return translate(lang, key)


@returns(SendApiCallCallbackResultTO)
@arguments(service_user=users.User, email=unicode, method=unicode, params=unicode, tag=unicode,
           service_identity=unicode, user_details=[UserDetailsTO])
def solution_coupon_resolve(service_user, email, method, params, tag, service_identity, user_details):
    data = json.loads(params)
    coupon_id = data.get('coupon_id')
    redeeming_user = users.User(data.get('redeeming_user'))
    response = SendApiCallCallbackResultTO()
    service_identity_user = get_and_validate_service_identity_user(service_user, service_identity)
    try:
        coupon = get_and_validate_news_coupon(coupon_id, service_identity_user, redeeming_user)
        response.result = u'%s' % json.dumps(serialize_complex_value(coupon, NewsCouponTO, False))
    except NewsCouponNotFoundException:
        lang = get_solution_settings(service_user).main_language
        response.error = t(lang, 'coupon_not_found')
    except NewsCouponAlreadyUsedException:
        lang = get_solution_settings(service_user).main_language
        response.error = t(lang, 'you_have_already_used_this_coupon')
        user, app_id = get_app_user_tuple(redeeming_user)
        member = BaseMemberTO(user.email(), app_id)
        disable_news_with_coupon(coupon_id, service_identity_user, member)
    except Exception as exception:
        logging.exception(exception)
        lang = get_solution_settings(service_user).main_language
        response.error = t(lang, 'error-occured-unknown')
    return response


@returns(SendApiCallCallbackResultTO)
@arguments(service_user=users.User, email=unicode, method=unicode, params=unicode, tag=unicode,
           service_identity=unicode, user_details=[UserDetailsTO])
def solution_coupon_redeem(service_user, email, method, params, tag, service_identity, user_details):
    data = json.loads(params)
    coupon_id = data.get('coupon_id')
    redeeming_user = users.User(data.get('redeeming_user'))
    response = SendApiCallCallbackResultTO()
    lang = get_solution_settings(service_user).main_language
    service_identity_user = get_and_validate_service_identity_user(service_user, service_identity)

    try:
        coupon = redeem_news_coupon(coupon_id, service_identity_user, redeeming_user)
        with users.set_user(service_user):
            news_item = news.get(coupon.news_id, service_identity)
            response.result = u'%s' % json.dumps(serialize_complex_value(news_item, NewsItemTO, False))
    except NewsCouponNotFoundException:
        response.error = t(lang, 'coupon_not_found')
    except NewsCouponAlreadyUsedException:
        response.error = t(lang, 'you_have_already_used_this_coupon')
        user, app_id = get_app_user_tuple(redeeming_user)
        member = BaseMemberTO(user.email(), app_id)
        disable_news_with_coupon(coupon_id, service_identity_user, member)
    except Exception as exception:
        logging.error(exception)
        response.error = t(lang, 'error-occured-unknown')
    return response


@returns(NewsCoupon)
@arguments(coupon_id=(int, long), service_identity_user=users.User, redeeming_user=users.User)
def get_and_validate_news_coupon(coupon_id, service_identity_user, redeeming_user):
    # type: (long, users.User, users.User) -> NewsCoupon
    coupon = NewsCoupon.create_key(coupon_id, service_identity_user).get()
    if not coupon:
        raise NewsCouponNotFoundException()
    if coupon.redeemed_by:
        redeeming_email = redeeming_user.email()
        redeemed_user = [value for value in coupon.redeemed_by if value.user == redeeming_email]
        if redeemed_user:
            raise NewsCouponAlreadyUsedException()
    return coupon


@returns(NewsCoupon)
@arguments(coupon_id=(int, long), service_identity_user=users.User, redeeming_user=users.User)
def redeem_news_coupon(coupon_id, service_identity_user, redeeming_user):
    """
    Args:
        coupon_id (int): id of the coupon
        service_identity_user (users.User): service user for which the coupon is valid
        redeeming_user (users.User): user that used/wants to use the coupon

    Raises:
        NewsCouponNotFoundException
        NewsCouponAlreadyUsedException: When the news coupon has already been used by redeeming_user
    """

    def trans():
        coupon = get_and_validate_news_coupon(coupon_id, service_identity_user, redeeming_user)
        redeemed_object = RedeemedBy(
            user=redeeming_user.email(),
            redeemed_on=now()
        )
        coupon.redeemed_by.append(redeemed_object)
        coupon.put()
        user, app_id = get_app_user_tuple(redeeming_user)
        member = BaseMemberTO(user.email(), app_id)
        news.disable_news(coupon.news_id, [member], get_identity_from_service_identity_user(service_identity_user))
        return coupon

    return run_in_xg_transaction(trans)


@returns()
@arguments(coupon_id=(int, long), service_identity_user=users.User, member=BaseMemberTO)
def disable_news_with_coupon(coupon_id, service_identity_user, member):
    coupon = NewsCoupon.create_key(coupon_id, service_identity_user).get()
    news.disable_news(coupon.news_id, [member], get_identity_from_service_identity_user(service_identity_user))
