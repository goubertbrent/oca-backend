# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
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

import base64
import datetime
import json
import logging
from types import NoneType

from google.appengine.ext import db, ndb
from google.appengine.ext.deferred import deferred

from babel.dates import format_datetime, get_timezone
from typing import List

from mcfw.consts import MISSING
from mcfw.properties import azzert
from mcfw.rpc import arguments, returns
from rogerthat.bizz.app import get_app
from rogerthat.consts import DEBUG
from rogerthat.dal import parent_ndb_key
from rogerthat.dal.app import get_apps_by_id
from rogerthat.dal.service import get_service_identity
from rogerthat.models import App, Image
from rogerthat.models.news import NewsItem
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from rogerthat.rpc.users import get_current_session
from rogerthat.service.api import app, news
from rogerthat.to.news import NewsActionButtonTO, NewsTargetAudienceTO, NewsFeedNameTO, BaseMediaTO, NewsLocationsTO, \
    NewsItemListResultTO, NewsItemTO
from rogerthat.utils import now
from rogerthat.utils.service import get_service_identity_tuple
from shop.dal import get_customer
from solutions import translate as common_translate
from solutions.common import SOLUTION_COMMON
from solutions.common.bizz import SolutionModule, OrganizationType
from solutions.common.bizz.cityapp import get_apps_in_country_count
from solutions.common.bizz.service import get_inbox_message_sender_details, new_inbox_message, \
    send_inbox_message_update, send_message_updates
from solutions.common.dal import get_solution_settings
from solutions.common.dal.cityapp import get_cityapp_profile, get_service_user_for_city
from solutions.common.models import SolutionInboxMessage
from solutions.common.models.budget import Budget
from solutions.common.models.news import NewsCoupon, SolutionNewsItem, NewsSettings, NewsSettingsTags, NewsReview, \
    CityAppLocations
from solutions.common.to.news import NewsStatsTO, NewsAppTO


class AllNewsSentToReviewWarning(BusinessException):
    pass


@returns(NewsItemListResultTO)
@arguments(cursor=unicode, service_identity=unicode, tag=unicode)
def get_news(cursor=None, service_identity=None, tag=None):
    if not tag or tag is MISSING:
        tag = u'news'
    return news.list_news(cursor, 10, service_identity, tag=tag)


@returns(NewsStatsTO)
@arguments(news_id=(int, long), service_identity=unicode)
def get_news_statistics(news_id, service_identity=None):
    news_item = news.get(news_id, service_identity, True)
    apps = get_apps_by_id([s.app_id for s in news_item.statistics])
    return NewsStatsTO(
        news_item=news_item,
        apps=[NewsAppTO.from_model(app) for app in apps],
    )


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


def get_regional_apps_of_item(news_item, default_app_id):
    """Returns a list of regional apps of a news item if found"""
    regional_apps = []
    for app_id in news_item.app_ids:
        if app_id in (App.APP_ID_OSA_LOYALTY, App.APP_ID_ROGERTHAT, default_app_id):
            continue
        regional_apps.append(app_id)
    return regional_apps


@ndb.transactional()
def create_regional_news_item(news_item, regional_apps, service_user, service_identity, paid=False):
    # type: (NewsItem, List[unicode], users.User, unicode, bool) -> SolutionNewsItem
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
    sln_item.app_ids = regional_apps
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


def publish_item(service_identity_user, app_id, is_free_regional_news, coupon, should_save_coupon, **kwargs):
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
        regional_apps = get_regional_apps_of_item(news_item, app_id)
        if regional_apps:
            if not news_id and not is_free_regional_news:
                # check for budget on creation only
                check_budget(service_user, identity)
            deferred.defer(create_regional_news_item, news_item, regional_apps, service_user, identity,
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
        return common_translate(lang, SOLUTION_COMMON, unicode(term), *args, **kwargs)

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


def send_news_for_review(city_service, service_identity_user, app_id, is_free_regional_news, coupon, **kwargs):
    key = NewsReview.create_key(city_service)
    review = key.get() or NewsReview(key=key)
    review.service_identity_user = service_identity_user
    review.app_id = app_id
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
    review = ndb.Key(urlsafe=review_key).get()
    if not review:
        raise BusinessException('review item is not found!')

    coupon = review.coupon_id and NewsCoupon.get_by_id(review.coupon_id)
    should_save_coupon = bool(coupon)

    service_user, _ = get_service_identity_tuple(review.service_identity_user)
    with users.set_user(service_user):
        item = publish_item(review.service_identity_user, review.app_id, review.is_free_regional_news, coupon,
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
           app_ids=[unicode], scheduled_at=(int, long), news_id=(NoneType, int, long),
           target_audience=NewsTargetAudienceTO, role_ids=[(int, long)], tag=unicode, media=BaseMediaTO,
           group_type=unicode, locations=NewsLocationsTO, group_visible_until=(int, long))
def put_news_item(service_identity_user, title, message, action_button, news_type, qr_code_caption, app_ids,
                  scheduled_at, news_id=None, target_audience=None, role_ids=None, tag=None, media=MISSING,
                  group_type=None, locations=None, group_visible_until=None):
    """
    Args:
        service_identity_user (users.User)
        title (unicode)
        message (unicode)
        action_button (NewsActionButtonTO)
        news_type (int)
        qr_code_caption (unicode)
        app_ids (list of unicode)
        scheduled_at (long)
        news_id (long): id of the news item to update. When not provided a new news item will be created.
        target_audience (NewsTargetAudienceTO)
        role_ids (list of long) the list of role ids to filter sending the news to their members
        tag(unicode)
        media (rogerthat.to.news.MediaTO)
        group_type (unicode)
        locations (NewsLocationsTO)
        group_visible_until (long)

    Returns:
        NewsItemTO
    """
    NEWS_TAG = u'news'
    if not tag or tag is MISSING:
        tag = NEWS_TAG
    service_user, identity = get_service_identity_tuple(service_identity_user)
    sln_settings = get_solution_settings(service_user)
    if news_type == NewsItem.TYPE_QR_CODE:
        azzert(SolutionModule.LOYALTY in sln_settings.modules)
        qr_code_caption = MISSING.default(qr_code_caption, title)
    should_save_coupon = news_type == NewsItem.TYPE_QR_CODE and not news_id
    si = get_service_identity(service_identity_user)

    if not news_id and not app_ids:
        raise BusinessException('Please select at least one app to publish this news in')

    default_app = get_app(si.defaultAppId)
    if default_app.demo and App.APP_ID_ROGERTHAT in app_ids:
        app_ids.remove(App.APP_ID_ROGERTHAT)

    feed_names = {}
    if is_regional_news_enabled(default_app):
        if tag == NEWS_TAG:
            if default_app.demo:
                # For demo apps the following rules count
                # Extra apps selected --> post in REGIONAL NEWS in the demo app
                # No extra apps selected --> post in LOCAL NEWS in the demo app
                if len(app_ids) == 1 and app_ids[0] == default_app.app_id:
                    pass  # LOCAL NEWS
                else:
                    feed_names[default_app.app_id] = NewsFeedNameTO(
                        default_app.app_id, u'regional_news')  # REGIONAL NEWS
                app_ids = [default_app.app_id]
            else:
                for app_id in app_ids:
                    if app_id not in (si.app_id, App.APP_ID_ROGERTHAT):
                        feed_names[app_id] = NewsFeedNameTO(app_id, u'regional_news')
        else:
            if default_app.demo:
                feed_names[default_app.app_id] = NewsFeedNameTO(default_app.app_id, tag)
            else:
                for app_id in app_ids:
                    feed_names[app_id] = NewsFeedNameTO(app_id, tag)
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
        'role_ids': role_ids,
        'tags': [tag],
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
    is_free_regional_news = (current_session and current_session.shop) or default_app.demo

    if not should_save_coupon:
        coupon = None

    new_app_ids = list(app_ids)
    if not news_id:
        # check for city-enabled news review
        for app_id in app_ids:
            city_service = get_service_user_for_city(app_id)
            if city_service and city_service != service_user:
                city_app_profile = get_cityapp_profile(city_service)
                if city_app_profile.review_news:
                    # create a city review for this app
                    city_kwargs = kwargs.copy()
                    city_kwargs['app_ids'] = [app_id]
                    city_kwargs['feed_names'] = feed_names.get(app_id, [])
                    send_news_for_review(city_service, service_identity_user, app_id, is_free_regional_news,
                                         coupon, **city_kwargs)
                    # remove from current feed
                    new_app_ids.remove(app_id)
                    if feed_names and app_id in feed_names:
                        del feed_names[app_id]

        if not DEBUG and new_app_ids == [App.APP_ID_ROGERTHAT] or (not new_app_ids and len(app_ids) > 0):
            raise AllNewsSentToReviewWarning(u'news_review_all_sent_to_review')

    # for the rest
    kwargs['feed_names'] = feed_names.values()
    kwargs['app_ids'] = new_app_ids

    with users.set_user(service_user):
        return publish_item(service_identity_user, si.app_id, is_free_regional_news, coupon, should_save_coupon,
                            **kwargs)


def delete_news(news_id, service_identity=None):
    news.delete(news_id, service_identity)


def is_regional_news_enabled(app_model):
    # type: (App) -> bool
    from rogerthat.consts import DEBUG
    if app_model.app_id.startswith('osa-') or DEBUG:
        return True
    country_code = app_model.app_id.split('-')[0].lower()
    return app_model.type == App.APP_TYPE_CITY_APP and get_apps_in_country_count(country_code) > 1


def get_news_reviews(service_user):
    parent_key = parent_ndb_key(service_user, SOLUTION_COMMON)
    return NewsReview.query(ancestor=parent_key)


def get_locations(app_id):
    # type: (str) -> CityAppLocations
    return CityAppLocations.create_key(app_id).get()
