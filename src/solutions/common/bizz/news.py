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
from __future__ import unicode_literals

import base64
import datetime
import json
import logging
from types import NoneType

from google.appengine.ext import db, ndb
from google.appengine.ext.deferred import deferred

from babel.dates import format_datetime, get_timezone
from mcfw.consts import MISSING
from mcfw.exceptions import HttpForbiddenException
from mcfw.properties import azzert
from mcfw.rpc import arguments, returns
from rogerthat.bizz.communities.communities import get_community, get_communities_by_id
from rogerthat.bizz.communities.models import AppFeatures
from rogerthat.consts import DEBUG
from rogerthat.dal import parent_ndb_key
from rogerthat.dal.profile import get_service_profile
from rogerthat.models import App, Image
from rogerthat.models.news import NewsItem
from rogerthat.models.settings import ServiceInfo
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from rogerthat.rpc.users import get_current_session
from rogerthat.service.api import app, news
from rogerthat.to.news import NewsActionButtonTO, NewsTargetAudienceTO, BaseMediaTO, NewsLocationsTO, \
    NewsItemListResultTO, NewsItemTO
from rogerthat.utils.service import get_service_identity_tuple
from solutions import translate as common_translate
from solutions.common import SOLUTION_COMMON
from solutions.common.bizz import SolutionModule, OrganizationType
from solutions.common.bizz.service import get_inbox_message_sender_details, new_inbox_message, \
    send_inbox_message_update, send_message_updates
from solutions.common.dal import get_solution_settings
from solutions.common.models import SolutionInboxMessage
from solutions.common.models.budget import Budget
from solutions.common.models.news import NewsCoupon, SolutionNewsItem, NewsSettings, NewsSettingsTags, NewsReview, \
    CityAppLocations
from solutions.common.to.news import NewsStatsTO


class AllNewsSentToReviewWarning(BusinessException):
    pass


@returns(NewsItemListResultTO)
@arguments(cursor=unicode, service_identity=unicode)
def get_news(cursor=None, service_identity=None):
    return news.list_news(cursor, 10, service_identity)


@returns(NewsStatsTO)
@arguments(news_id=(int, long), service_identity=unicode)
def get_news_item(news_id, service_identity=None):
    news_item = news.get(news_id, service_identity)
    statistics = news.get_basic_statistics([news_id], service_identity)
    stats = statistics[0] if statistics else None
    return NewsStatsTO(
        news_item=news_item,
        statistics=stats,
    )


def get_news_statistics(news_id, service_identity=None):
    return news.get_time_statistics(news_id, service_identity)


def _save_coupon_news_id(news_item_id, coupon):
    """
    Args:
        news_item_id (int)
        coupon (NewsCoupon)
    """
    coupon.news_id = news_item_id
    coupon.put()


def _app_uses_custom_organization_types(language):
    """Check if the app has any translated organization type"""
    translations = {
        translation.key: translation.value for translation in app.get_translations(language)
    }

    if translations:
        for translation_key in OrganizationType.get_translation_keys().values():
            if translations.get(translation_key):
                return True

    return False


@ndb.transactional()
def create_regional_news_item(news_item, regional_communities, service_user, service_identity, paid=False):
    # type: (NewsItem, List[long], users.User, unicode, bool) -> SolutionNewsItem
    sln_item_key = SolutionNewsItem.create_key(news_item.id, service_user)
    settings_key = NewsSettings.create_key(service_user, service_identity)
    sln_item, news_settings = ndb.get_multi([sln_item_key, settings_key])  # type: (SolutionNewsItem, NewsSettings)
    if not sln_item:
        sln_item = SolutionNewsItem(key=sln_item_key)

    if news_item.scheduled_at:
        publish_time = news_item.scheduled_at
    else:
        publish_time = news_item.timestamp

    sln_item.publish_time = publish_time
    sln_item.community_ids = regional_communities
    sln_item.service_identity = service_identity
    if paid or news_settings and NewsSettingsTags.FREE_REGIONAL_NEWS in news_settings.tags:
        sln_item.paid = True
    sln_item.put()
    return sln_item


def check_budget(service_user, service_identity):
    keys = [Budget.create_key(service_user), NewsSettings.create_key(service_user, service_identity)]
    budget, news_settings = ndb.get_multi(keys)  # type: (Budget, NewsSettings)
    if not news_settings or NewsSettingsTags.FREE_REGIONAL_NEWS not in news_settings.tags:
        if not budget or budget.balance <= 0:
            raise BusinessException('insufficient_budget')


def publish_item(service_identity_user, default_community_id, is_free_regional_news, coupon, should_save_coupon,
                 **kwargs):
    service_user, identity = get_service_identity_tuple(service_identity_user)
    news_id = kwargs.get('news_id')
    sticky = kwargs.pop('sticky', False)
    if news_id:
        news_type = kwargs.pop('news_type')
    else:
        news_type = kwargs.get('news_type')
    qr_code_caption = kwargs.get('qr_code_caption')

    @ndb.transactional(xg=True)
    def trans():
        news_item = news.publish(accept_missing=True, sticky=sticky, **kwargs)
        if should_save_coupon:
            _save_coupon_news_id(news_item.id, coupon)
        elif news_type == NewsItem.TYPE_QR_CODE and qr_code_caption is not MISSING and qr_code_caption and news_id:
            news_coupon = NewsCoupon.get_by_news_id(service_identity_user, news_id)
            if news_coupon:
                news_coupon.content = qr_code_caption
                news_coupon.put()
            else:
                logging.warn('Not updating qr_code_caption for non-existing coupon for news with id %d',
                             news_id)
        regional_communities = [i for i in news_item.community_ids if i != default_community_id]
        if regional_communities:
            if not news_id and not is_free_regional_news:
                # check for budget on creation only
                check_budget(service_user, identity)
            deferred.defer(create_regional_news_item, news_item, regional_communities, service_user, identity,
                           paid=is_free_regional_news, _transactional=True)
        return news_item

    try:
        return trans()
    except Exception:
        if should_save_coupon:
            db.delete_async(coupon)
        raise


def get_news_review_message(lang, timezone, header=None, **data):
    def trans(term, *args, **kwargs):
        return common_translate(lang, unicode(term), *args, **kwargs)

    message = u'{}\n\n'.format(header or trans('news_review_requested'))
    message += u'{}: {}\n'.format(trans('title'), data['title'])
    message += u'{}: {}\n'.format(trans('message'), data['message'])

    action_buttons = [
        '{}'.format(button.caption) for button in data['action_buttons']
    ]
    message += u'{}: {}\n'.format(trans('action_button'), ','.join(action_buttons))

    scheduled_at = data.get('scheduled_at')
    if scheduled_at:
        d = datetime.datetime.utcfromtimestamp(scheduled_at)
        date_str = format_datetime(d, locale=lang, tzinfo=get_timezone(timezone))
        message += u'{}\n'.format(trans('scheduled_for_datetime', datetime=date_str))
    return message


def store_image(image_data):
    _, content = image_data.split(',')
    image = Image(blob=base64.b64decode(content))
    image.put()
    return image


def send_news_review_message(sln_settings, sender_service, review_key, image_url, **data):
    msg = get_news_review_message(sln_settings.main_language, sln_settings.timezone, **data)
    sender_user_details = get_inbox_message_sender_details(sender_service)
    picture_urls = []
    if image_url:
        picture_urls.append(image_url)

    message = new_inbox_message(
        sln_settings, msg, service_identity=None,
        category=SolutionInboxMessage.CATEGORY_NEWS_REVIEW,
        category_key=review_key,
        user_details=sender_user_details,
        picture_urls=picture_urls)

    send_message_updates(sln_settings, u'solutions.common.news.review.update', message)
    return unicode(message.key())


def send_news_for_review(city_service, service_identity_user, community_id, is_free_regional_news, coupon, **kwargs):
    key = NewsReview.create_key(city_service)
    review = key.get() or NewsReview(key=key)
    review.service_identity_user = service_identity_user
    review.community_id = community_id
    review.is_free_regional_news = is_free_regional_news
    review.coupon_id = coupon and coupon.id
    review.data = kwargs

    image_url = None
    image = kwargs.get('image')
    if image:
        image = store_image(image)
        review.image_id = image.id
        image_url = u'/unauthenticated/image/%d' % review.image_id

    sln_settings = get_solution_settings(city_service)
    sender_service, _ = get_service_identity_tuple(service_identity_user)
    review.inbox_message_key = send_news_review_message(sln_settings, sender_service, unicode(key), image_url, **kwargs)
    review.put()


@returns()
@arguments(review_key=unicode, reason=unicode)
def send_news_review_reply(review_key, reason):
    review = ndb.Key(urlsafe=review_key).get()
    if review:
        service_user, identity = get_service_identity_tuple(review.service_identity_user)
        sln_settings = get_solution_settings(service_user)
        review_msg = get_news_review_message(sln_settings.main_language, sln_settings.timezone, reason, **review.data)
        sender_user_details = get_inbox_message_sender_details(review.parent_service_user)
        message = new_inbox_message(sln_settings, review_msg, service_identity=identity,
                                    user_details=sender_user_details)
        send_inbox_message_update(sln_settings, message, service_identity=identity)


@returns(NewsItemTO)
@arguments(review_key=unicode)
def publish_item_from_review(review_key):
    review = ndb.Key(urlsafe=review_key).get()  # type: NewsReview
    if not review:
        raise BusinessException('review item is not found!')

    coupon = review.coupon_id and NewsCoupon.get_by_id(review.coupon_id)
    should_save_coupon = bool(coupon)

    service_user, _ = get_service_identity_tuple(review.service_identity_user)
    with users.set_user(service_user):
        item = publish_item(review.service_identity_user, review.community_id, review.is_free_regional_news, coupon,
                            should_save_coupon, **review.data)

    inbox_message = SolutionInboxMessage.get(review.inbox_message_key)
    if inbox_message:
        inbox_message.read = True
        inbox_message.trashed = True
        inbox_message.put()
        sln_settings = get_solution_settings(review.parent_service_user)
        send_inbox_message_update(sln_settings, inbox_message)

    if review.image_id:
        Image.get_by_id(review.image_id).key.delete()

    review.key.delete()
    return item


@returns(NewsItemTO)
@arguments(service_identity_user=users.User, title=unicode, message=unicode,
           action_button=(NoneType, NewsActionButtonTO), news_type=(int, long), qr_code_caption=unicode,
           community_ids=[(int, long)], scheduled_at=(int, long), news_id=(NoneType, int, long),
           target_audience=NewsTargetAudienceTO, media=BaseMediaTO,
           group_type=unicode, locations=NewsLocationsTO, group_visible_until=(int, long))
def put_news_item(service_identity_user, title, message, action_button, news_type, qr_code_caption, community_ids,
                  scheduled_at, news_id=None, target_audience=None, media=MISSING,
                  group_type=None, locations=None, group_visible_until=None):
    """
    Args:
        service_identity_user (users.User)
        title (unicode)
        message (unicode)
        action_button (NewsActionButtonTO)
        news_type (int)
        qr_code_caption (unicode)
        community_ids (list[int])
        scheduled_at (long)
        news_id (long): id of the news item to update. When not provided a new news item will be created.
        target_audience (NewsTargetAudienceTO)
        media (rogerthat.to.news.MediaTO)
        group_type (unicode)
        locations (NewsLocationsTO)
        group_visible_until (long)

    Returns:
        NewsItemTO
    """
    service_user, identity = get_service_identity_tuple(service_identity_user)
    sln_settings = get_solution_settings(service_user)
    service_info = ServiceInfo.create_key(service_user, identity).get()
    check_can_send_news(sln_settings, service_info)
    if news_type == NewsItem.TYPE_QR_CODE:
        azzert(SolutionModule.LOYALTY in sln_settings.modules)
        qr_code_caption = MISSING.default(qr_code_caption, title)
    should_save_coupon = news_type == NewsItem.TYPE_QR_CODE and not news_id

    if not news_id and not community_ids:
        raise BusinessException('Please select at least one community to publish this news in')

    service_profile = get_service_profile(service_user)
    service_community = get_community(service_profile.community_id)

    if not is_regional_news_enabled(service_community) or service_community.demo:
        # Demo apps can't send regional news
        community_ids = [service_profile.community_id]
    sticky = False
    sticky_until = None
    kwargs = {
        'sticky': sticky,
        'sticky_until': sticky_until,
        'message': message,
        'service_identity': identity,
        'news_id': news_id,
        'news_type': news_type,
        'scheduled_at': scheduled_at,
        'target_audience': target_audience,
        'media': media,
        'group_type': group_type,
        'locations': locations,
        'group_visible_until': group_visible_until,
    }

    if news_type == NewsItem.TYPE_QR_CODE:
        if should_save_coupon:
            def trans():
                coupon = NewsCoupon(
                    parent=NewsCoupon.create_parent_key(service_identity_user),
                    content=qr_code_caption
                )
                coupon.put()
                return coupon
            coupon = db.run_in_transaction(trans)
            kwargs['qr_code_content'] = u'%s' % json.dumps({'c': coupon.id})
        kwargs['qr_code_caption'] = qr_code_caption
    elif news_type == NewsItem.TYPE_NORMAL:
        kwargs.update({
            'action_buttons': [action_button] if action_button else [],
            'title': title
        })
    else:
        raise BusinessException('Invalid news type')
    for key, value in kwargs.items():
        if value is MISSING:
            del kwargs[key]

    current_session = get_current_session()
    is_free_regional_news = (current_session and current_session.shop) or service_community.demo

    if not should_save_coupon:
        coupon = None

    new_community_ids = list(community_ids)
    service_communities = {community.id: community for community in get_communities_by_id(community_ids)}
    if not news_id:
        # check for city-enabled news review
        for community_id in community_ids:
            community = service_communities[community_id]
            # Skip check if current service == default service
            if community.main_service_user != service_user:
                if AppFeatures.NEWS_REVIEW in community.features:
                    # create a city review for this app
                    city_kwargs = kwargs.copy()
                    city_kwargs['community_ids'] = [community_id]
                    send_news_for_review(community.main_service_user, service_identity_user, community_id,
                                         is_free_regional_news, coupon, **city_kwargs)
                    # remove from current feed
                    new_community_ids.remove(community_id)

        if not DEBUG and new_community_ids == [App.APP_ID_ROGERTHAT] or (
            not new_community_ids and len(community_ids) > 0):
            raise AllNewsSentToReviewWarning(u'news_review_all_sent_to_review')

    # for the rest
    kwargs['community_ids'] = new_community_ids

    with users.set_user(service_user):
        return publish_item(service_identity_user, service_community.id, is_free_regional_news, coupon,
                            should_save_coupon, **kwargs)


def delete_news(news_id, service_identity=None):
    news.delete(news_id, service_identity)


def is_regional_news_enabled(community):
    # type: (Community) -> bool
    return AppFeatures.NEWS_REGIONAL in community.features


def get_news_reviews(service_user):
    parent_key = parent_ndb_key(service_user, SOLUTION_COMMON)
    return NewsReview.query(ancestor=parent_key)


def get_locations(app_id):
    # type: (str) -> CityAppLocations
    return CityAppLocations.create_key(app_id).get()


def check_can_send_news(sln_settings, service_info):
    # type: (SolutionSettings, ServiceInfo) -> None
    if sln_settings.hidden_by_city:
        reason = common_translate(sln_settings.main_language, 'your_service_was_hidden_by_your_city')
        msg = common_translate(sln_settings.main_language, 'cannot_send_news', reason='\n' + reason)
        raise HttpForbiddenException(msg)
    if not service_info.visible:
        reason = common_translate(sln_settings.main_language, 'news_service_invisible_reason')
        msg = common_translate(sln_settings.main_language, 'cannot_send_news', reason='\n' + reason)
        raise HttpForbiddenException(msg)
