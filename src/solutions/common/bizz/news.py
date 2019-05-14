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

import base64
import datetime
import json
import logging
import time
from types import NoneType

from google.appengine.api import taskqueue
from google.appengine.ext import db, ndb
from google.appengine.ext.deferred import deferred

from babel.dates import format_datetime, get_timezone
from bs4 import BeautifulSoup
from markdown import markdown
from mcfw.consts import MISSING
from mcfw.properties import azzert
from mcfw.rpc import arguments, returns
from rogerthat.bizz.app import get_app
from rogerthat.consts import SCHEDULED_QUEUE
from rogerthat.dal import parent_ndb_key
from rogerthat.dal.service import get_service_identity
from rogerthat.models import App, Image
from rogerthat.models.news import NewsItem, NewsItemImage
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from rogerthat.rpc.users import get_current_session
from rogerthat.service.api import app, news
from rogerthat.to.news import NewsActionButtonTO, NewsTargetAudienceTO, NewsFeedNameTO, BaseMediaTO, MediaType
from rogerthat.utils import now, channel
from rogerthat.utils.service import get_service_identity_tuple
from shop.bizz import update_regiomanager_statistic, get_payed
from shop.business.legal_entities import get_vat_pct
from shop.constants import STORE_MANAGER
from shop.dal import get_customer
from shop.exceptions import NoCreditCardException
from shop.models import Contact, Product, RegioManagerTeam, Order, OrderNumber, OrderItem, Charge
from shop.to import OrderItemTO
from solutions import translate as common_translate
from solutions.common import SOLUTION_COMMON
from solutions.common.api_callback_handlers import _get_human_readable_tag
from solutions.common.bizz import SolutionModule, OrganizationType, facebook, twitter
from solutions.common.bizz.cityapp import get_apps_in_country_count
from solutions.common.bizz.forms import get_form_settings
from solutions.common.bizz.messaging import POKE_TAG_FORMS
from solutions.common.bizz.service import get_inbox_message_sender_details, new_inbox_message, \
    send_inbox_message_update, send_message_updates
from solutions.common.dal import get_solution_settings
from solutions.common.dal.cityapp import get_cityapp_profile, get_service_user_for_city
from solutions.common.models import SolutionInboxMessage, SolutionScheduledBroadcast
from solutions.common.models.budget import Budget
from solutions.common.models.news import NewsCoupon, SolutionNewsItem, NewsSettings, NewsSettingsTags, NewsReview
from solutions.common.to.news import SponsoredNewsItemCount, NewsBroadcastItemTO, NewsBroadcastItemListTO, \
    NewsStatsTO, NewsAppTO
from solutions.flex import SOLUTION_FLEX

FREE_SPONSORED_ITEMS_PER_APP = 5
SPONSOR_DAYS = 7


class AllNewsSentToReviewWarning(BusinessException):
    pass


@returns(NewsBroadcastItemListTO)
@arguments(cursor=unicode, service_identity=unicode, tag=unicode)
def get_news(cursor=None, service_identity=None, tag=None):
    if not tag or tag is MISSING:
        tag = u'news'
    news_list = news.list_news(cursor, 5, service_identity, tag=tag)
    result = NewsBroadcastItemListTO()
    result.result = []
    result.cursor = news_list.cursor

    for news_item in news_list.result:
        scheduled_item = get_scheduled_broadcast(news_item.id)
        if scheduled_item:
            on_facebook = scheduled_item.broadcast_on_facebook
            on_twitter = scheduled_item.broadcast_on_twitter
            result_item = NewsBroadcastItemTO.from_news_item_to(news_item, on_facebook, on_twitter)
        else:
            result_item = NewsBroadcastItemTO.from_news_item_to(news_item)
        result.result.append(result_item)

    return result


@returns(NewsStatsTO)
@arguments(news_id=(int, long), service_identity=unicode)
def get_news_statistics(news_id, service_identity=None):
    news_item = news.get(news_id, service_identity, True)
    apps_rpc = db.get([App.create_key(s.app_id) for s in news_item.statistics])
    result = NewsStatsTO(news_item=NewsBroadcastItemTO.from_news_item_to(news_item))
    result.apps = [NewsAppTO.from_model(model) for model in apps_rpc]
    return result


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
    # type: (NewsItem, list[unicode], users.User, unicode, bool) -> SolutionNewsItem
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


def publish_item(service_identity_user, app_id, host, is_free_regional_news, order_items, coupon,
                 should_save_coupon, broadcast_on_facebook, broadcast_on_twitter, facebook_access_token, **kwargs):
    service_user, identity = get_service_identity_tuple(service_identity_user)
    news_id = kwargs.get('news_id')
    sticky = kwargs.pop('sticky', False)
    if news_id:
        news_type = kwargs.pop('news_type')
    else:
        news_type = kwargs.get('news_type')
    qr_code_caption = kwargs.get('qr_code_caption')
    scheduled_at = kwargs.get('scheduled_at')

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
        if order_items:
            create_and_pay_news_order(service_user, news_item.id, order_items)
        regional_apps = get_regional_apps_of_item(news_item, app_id)
        if regional_apps:
            if not news_id and not is_free_regional_news:
                # check for budget on creation only
                check_budget(service_user, identity)
            deferred.defer(create_regional_news_item, news_item, regional_apps, service_user, identity,
                           paid=is_free_regional_news, _transactional=True)
        return news_item

    try:
        news_item = trans()
        if broadcast_on_facebook or broadcast_on_twitter:
            if scheduled_at is not MISSING and scheduled_at > 0:
                schedule_post_to_social_media(service_user, host, broadcast_on_facebook,
                                              broadcast_on_twitter, facebook_access_token,
                                              news_item.id, scheduled_at)
            else:
                post_to_social_media(service_user, broadcast_on_facebook,
                                     broadcast_on_twitter, facebook_access_token,
                                     news_item.id)

        return NewsBroadcastItemTO.from_news_item_to(news_item, broadcast_on_facebook, broadcast_on_twitter)
    except:
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


def send_news_for_review(city_service, service_identity_user, app_id, host, is_free_regional_news, order_items, coupon,
                         should_save_coupon, broadcast_on_facebook, broadcast_on_twitter, facebook_access_token,
                         **kwargs):

    key = NewsReview.create_key(city_service)
    review = key.get() or NewsReview(key=key)
    review.service_identity_user = service_identity_user
    review.app_id = app_id
    review.host = host
    review.is_free_regional_news = is_free_regional_news
    review.order_items = order_items
    review.coupon_id = coupon and coupon.id
    review.broadcast_on_facebook = broadcast_on_facebook
    review.broadcast_on_twitter = broadcast_on_twitter
    review.facebook_access_token = facebook_access_token
    review.data = kwargs

    image_url = None
    if kwargs['image']:
        image = store_image(kwargs['image'])
        review.image_id = image.id
        image_url = u'/unauthenticated/image/%d' % review.image_id

    sln_settings = get_solution_settings(city_service)
    sender_service, _ = get_service_identity_tuple(service_identity_user)
    review.inbox_message_key = send_news_review_message(
        sln_settings, sender_service, unicode(key), image_url, **kwargs)
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


@returns(NewsBroadcastItemTO)
@arguments(review_key=unicode)
def publish_item_from_review(review_key):
    review = ndb.Key(urlsafe=review_key).get()
    if not review:
        raise BusinessException('review item is not found!')

    coupon = review.coupon_id and NewsCoupon.get_by_id(review.coupon_id)
    should_save_coupon = bool(coupon)

    service_user, _ = get_service_identity_tuple(review.service_identity_user)
    with users.set_user(service_user):
        item = publish_item(
            review.service_identity_user, review.app_id, review.host, review.is_free_regional_news,
            review.order_items, coupon, should_save_coupon, review.broadcast_on_facebook, review.broadcast_on_twitter,
            review.facebook_access_token, **review.data)

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


@returns(NewsBroadcastItemTO)
@arguments(service_identity_user=users.User, title=unicode, message=unicode, broadcast_type=unicode, sponsored=bool,
           image=unicode, action_button=(NoneType, NewsActionButtonTO), order_items=(NoneType, [OrderItemTO]),
           news_type=(int, long), qr_code_caption=unicode, app_ids=[unicode], scheduled_at=(int, long),
           news_id=(NoneType, int, long), broadcast_on_facebook=bool, broadcast_on_twitter=bool,
           facebook_access_token=unicode, target_audience=NewsTargetAudienceTO, role_ids=[(int, long)], host=unicode,
           tag=unicode, media=BaseMediaTO)
def put_news_item(service_identity_user, title, message, broadcast_type, sponsored, image, action_button, order_items,
                  news_type, qr_code_caption, app_ids, scheduled_at, news_id=None, broadcast_on_facebook=False,
                  broadcast_on_twitter=False, facebook_access_token=None, target_audience=None, role_ids=None,
                  host=None, tag=None, media=MISSING):
    """
    Creates a news item first then processes the payment if necessary (not necessary for non-promoted posts).
    If the payment was unsuccessful it will be retried in a deferred task.

    Args:
        service_identity_user (users.User)
        title (unicode)
        message (unicode)
        broadcast_type (unicode)
        sponsored (bool)
        image (unicode)
        action_button (NewsActionButtonTO)
        order_items (list of OrderItemTO)
        news_type (int)
        qr_code_caption (unicode)
        app_ids (list of unicode)
        scheduled_at (long)
        news_id (long): id of the news item to update. When not provided a new news item will be created.
        broadcast_on_facebook (bool)
        broadcast_on_twitter (bool)
        facebook_access_token (unicode): user or page access token
        target_audience (NewsTargetAudienceTO)
        role_ids (list of long) the list of role ids to filter sending the news to their members
        host (unicode): host of the api request (used for social media apps)
        tag(unicode)
        media (rogerthat.to.news.MediaTO)

    Returns:
        news_item (NewsBroadcastItemTO)
    """
    NEWS_TAG = u'news'
    if not order_items or order_items is MISSING:
        order_items = []
    if not tag or tag is MISSING:
        tag = NEWS_TAG
    service_user, identity = get_service_identity_tuple(service_identity_user)
    sln_settings = get_solution_settings(service_user)
    if news_type == NewsItem.TYPE_QR_CODE:
        azzert(SolutionModule.LOYALTY in sln_settings.modules)
        qr_code_caption = MISSING.default(qr_code_caption, title)
    sponsored_until = None
    should_save_coupon = news_type == NewsItem.TYPE_QR_CODE and not news_id
    sponsored_app_ids = set()
    si = get_service_identity(service_identity_user)
    for order_item in reversed(order_items):
        if order_item.product == Product.PRODUCT_NEWS_PROMOTION and sponsored:
            azzert(order_item.app_id)
            azzert(order_item.app_id not in sponsored_app_ids)
            sponsored_app_ids.add(order_item.app_id)
            order_item.count = get_sponsored_news_count_in_app(service_identity_user, order_item.app_id).count
        else:
            raise BusinessException('Invalid product %s' % order_item.product)

    if not news_id and not app_ids:
        raise BusinessException('Please select at least one app to publish this news in')
    if sponsored:
        sponsored_until_date = datetime.datetime.utcnow() + datetime.timedelta(days=SPONSOR_DAYS)
        sponsored_until = long(sponsored_until_date.strftime('%s'))
        # for sponsored news that is free in certain apps no order item is given, so add it here
        sponsored_counts = get_sponsored_news_count(service_identity_user, app_ids)
        for sponsored_count in sponsored_counts:
            if sponsored_count.remaining_free != 0 and sponsored_count.app_id in app_ids:
                sponsored_app_ids.add(sponsored_count.app_id)
        app_ids = list(sponsored_app_ids)
    if SolutionModule.CITY_APP in sln_settings.modules:
        if action_button:
            tag_content = action_button.action.replace('smi://', '')
            smi_tag = _get_human_readable_tag(tag_content)
            if smi_tag == POKE_TAG_FORMS:
                form_id = json.loads(tag_content)['id']
                form = get_form_settings(form_id, service_user)
                if form.visible_until:
                    sponsored_until = long(time.mktime(form.visible_until.timetuple()))

    default_app = get_app(si.defaultAppId)
    if App.APP_ID_ROGERTHAT in si.appIds and App.APP_ID_ROGERTHAT not in app_ids:
        app_ids.append(App.APP_ID_ROGERTHAT)
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

    kwargs = {
        'sticky_until': sponsored_until,
        'message': message,
        'broadcast_type': broadcast_type,
        'service_identity': identity,
        'news_id': news_id,
        'news_type': news_type,
        'image': image,
        'scheduled_at': scheduled_at,
        'target_audience': target_audience,
        'role_ids': role_ids,
        'tags': [tag],
        'media': media,
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

    if sponsored:
        sticky = True
    else:
        customer = get_customer(service_user)
        if customer and customer.organization_type == OrganizationType.CITY and \
                not _app_uses_custom_organization_types(customer.language):
            sticky = True
            if kwargs['sticky_until'] is None:
                kwargs['sticky_until'] = now()
        else:
            sticky = False
    kwargs['sticky'] = sticky

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
                    send_news_for_review(
                        city_service, service_identity_user, app_id, host, is_free_regional_news, order_items,
                        coupon, should_save_coupon, broadcast_on_facebook, broadcast_on_twitter, facebook_access_token,
                        **city_kwargs)
                    # remove from current feed
                    new_app_ids.remove(app_id)
                    if feed_names and app_id in feed_names:
                        del feed_names[app_id]

        from rogerthat.consts import DEBUG
        if new_app_ids == [App.APP_ID_ROGERTHAT] or (not new_app_ids and len(app_ids) > 0):
            if not DEBUG:
                raise AllNewsSentToReviewWarning(u'news_review_all_sent_to_review')

    # for the rest
    kwargs['feed_names'] = feed_names.values()
    kwargs['app_ids'] = new_app_ids

    with users.set_user(service_user):
        return publish_item(
            service_identity_user, si.app_id, host, is_free_regional_news, order_items,
            coupon, should_save_coupon, broadcast_on_facebook, broadcast_on_twitter, facebook_access_token, **kwargs)


def remove_markdown(text):
    if not isinstance(text, unicode):
        text = text.decode('utf-8')
    html = markdown(text)
    return ''.join(BeautifulSoup(html, features='lxml').findAll(text=True))


@returns()
@arguments(service_user=users.User, on_facebook=bool, on_twitter=bool,
           facebook_access_token=unicode, news_id=(int, long))
def post_to_social_media(service_user, on_facebook, on_twitter,
                         facebook_access_token, news_id):
    news_item = NewsItem.get_by_id(news_id)
    if not news_item:
        logging.warn('Cannot post to social media, news item does not exist')
        return

    if news_item.type == NewsItem.TYPE_QR_CODE:
        logging.warn('Cannot post to social media for a coupon news type')
        return

    message = news_item.title + '\n' + remove_markdown(news_item.message)
    image_content = None
    if news_item.media:
        if news_item.media.type == MediaType.IMAGE:
            news_item_image = NewsItemImage.get_by_id(news_item.media.content)
            if news_item_image:
                image_content = news_item_image.image

    if on_facebook and facebook_access_token:
        facebook.post_to_facebook(facebook_access_token, message, image_content)

    if on_twitter:
        media = []
        if image_content:
            media.append(image_content)
        twitter.update_twitter_status(service_user, message, media)


def post_to_social_media_scheduled(str_key):
    scheduled_broadcast = SolutionScheduledBroadcast.get(str_key)
    if not scheduled_broadcast or scheduled_broadcast.deleted:
        return

    news_id = scheduled_broadcast.news_id
    on_facebook = scheduled_broadcast.broadcast_on_facebook
    on_twitter = scheduled_broadcast.broadcast_on_twitter
    facebook_access_token = scheduled_broadcast.facebook_access_token

    service_user = scheduled_broadcast.service_user
    with users.set_user(service_user):
        post_to_social_media(service_user, on_facebook, on_twitter,
                             facebook_access_token, news_id)
        scheduled_broadcast.delete()


def get_scheduled_broadcast(news_item_id, service_user=None, create=False):
    if service_user is None:
        service_user = users.get_current_user()

    key = SolutionScheduledBroadcast.create_key(news_item_id,
                                                service_user,
                                                SOLUTION_FLEX)
    scheduled_broadcast = db.get(key)
    if not scheduled_broadcast and create:
        scheduled_broadcast = SolutionScheduledBroadcast(key=key)

    return scheduled_broadcast


def schedule_post_to_social_media(service_user, host, on_facebook, on_twitter,
                                  facebook_access_token, news_id, scheduled_at):
    if scheduled_at < 1:
        return

    scheduled_broadcast = get_scheduled_broadcast(news_id, service_user, create=True)
    if scheduled_broadcast.timestamp == scheduled_at:
        return

    if on_facebook:
        if not facebook_access_token:
            if scheduled_broadcast.facebook_access_token:
                facebook_access_token = scheduled_broadcast.facebook_access_token
            else:
                raise ValueError('facebook access token is not provided, %s, news id: %d' % (service_user, news_id))

        # try to extend facebook access token first
        try:
            facebook_access_token = facebook.extend_access_token(host, facebook_access_token)
        except:
            logging.error('Cannot get an extended facebook access token', exc_info=True)

    if scheduled_broadcast.scheduled_task_name:
        # remove the old scheduled task
        task_name = str(scheduled_broadcast.scheduled_task_name)
        taskqueue.Queue(SCHEDULED_QUEUE).delete_tasks_by_name(task_name)

    scheduled_broadcast.timestamp = scheduled_at
    scheduled_broadcast.broadcast_on_facebook = on_facebook
    scheduled_broadcast.broadcast_on_twitter = on_twitter
    scheduled_broadcast.facebook_access_token = facebook_access_token
    scheduled_broadcast.news_id = news_id

    task = deferred.defer(post_to_social_media_scheduled,
                          scheduled_broadcast.key_str,
                          _countdown=scheduled_at - now(),
                          _queue=SCHEDULED_QUEUE,
                          _transactional=db.is_in_transaction())

    scheduled_broadcast.scheduled_task_name = task.name
    scheduled_broadcast.put()


@returns()
@arguments(service_user=users.User, news_item_id=(int, long), order_items_to=[OrderItemTO])
def create_and_pay_news_order(service_user, news_item_id, order_items_to):
    """
    Creates an order, orderitems, charge and executes the charge. Should be executed in a transaction.
    Args:
        service_user (users.User)
        news_item_id (long)
        order_items_to (ist of OrderItemTO)

    Raises:
        NoCreditCardException
        ProductNotFoundException
    """

    @db.non_transactional
    def _get_customer():
        return get_customer(service_user)

    @db.non_transactional
    def _get_contact():
        return Contact.get_one(customer)

    customer = _get_customer()
    azzert(customer)
    contact = _get_contact()
    azzert(contact)
    if not customer.stripe_valid:
        raise NoCreditCardException(customer)
    news_product_key = Product.create_key(Product.PRODUCT_NEWS_PROMOTION)
    rmt_key = RegioManagerTeam.create_key(customer.team_id)
    news_promotion_product, team = db.get((news_product_key, rmt_key))
    azzert(news_promotion_product)
    azzert(team)
    new_order_key = Order.create_key(customer.id, OrderNumber.next(team.legal_entity_key))
    vat_pct = get_vat_pct(customer, team)

    total_amount = 0
    for order_item in order_items_to:
        if order_item.product == Product.PRODUCT_NEWS_PROMOTION:
            total_amount += news_promotion_product.price * order_item.count
            order_item.price = news_promotion_product.price
        else:
            raise BusinessException('Invalid product \'%s\'' % order_item.product)

    vat = int(round(vat_pct * total_amount / 100))
    total_amount_vat_incl = int(round(total_amount + vat))
    now_ = now()
    to_put = []
    order = Order(
        key=new_order_key,
        date=now_,
        amount=total_amount,
        vat_pct=vat_pct,
        vat=vat,
        total_amount=total_amount_vat_incl,
        contact_id=contact.id,
        status=Order.STATUS_SIGNED,
        is_subscription_order=False,
        is_subscription_extension_order=False,
        date_signed=now_,
        manager=STORE_MANAGER,
        team_id=team.id
    )
    to_put.append(order)
    azzert(order.total_amount >= 0)

    for item in order_items_to:
        order_item = OrderItem(
            parent=new_order_key,
            number=item.number,
            product_code=item.product,
            count=item.count,
            comment=item.comment,
            price=item.price
        )
        order_item.app_id = item.app_id
        if order_item.product_code == Product.PRODUCT_NEWS_PROMOTION:
            order_item.news_item_id = news_item_id
        to_put.append(order_item)

    db.put(to_put)

    # Not sure if this is necessary
    from solutions.common.restapi.store import generate_and_put_order_pdf_and_send_mail
    deferred.defer(generate_and_put_order_pdf_and_send_mail, customer, new_order_key, service_user, contact,
                   _transactional=True)

    # No need for signing here, immediately create a charge.
    charge = Charge(parent=new_order_key)
    charge.date = now()
    charge.type = Charge.TYPE_ORDER_DELIVERY
    charge.amount = order.amount
    charge.vat_pct = order.vat_pct
    charge.vat = order.vat
    charge.total_amount = order.total_amount
    charge.manager = order.manager
    charge.team_id = order.team_id
    charge.status = Charge.STATUS_PENDING
    charge.date_executed = now()
    charge.currency_code = team.legal_entity.currency_code
    charge.put()

    # Update the regiomanager statistics so these kind of orders show up in the monthly statistics
    deferred.defer(update_regiomanager_statistic, gained_value=order.amount / 100,
                   manager=order.manager, _transactional=True)

    # charge the credit card
    if charge.total_amount > 0:
        get_payed(customer.id, order, charge)
    else:
        charge.status = Charge.STATUS_EXECUTED
        charge.date_executed = now()
        charge.put()
    channel.send_message(service_user, 'common.billing.orders.update')


def delete_news(news_id, service_identity=None):
    news.delete(news_id, service_identity)


@returns(SponsoredNewsItemCount)
@arguments(service_identity_user=users.User, app_id=unicode)
def get_sponsored_news_count_in_app(service_identity_user, app_id):
    """
    Args:
        service_identity_user (users.User)
        app_id (unicode)
    """
    news_items = NewsItem.list_sticky_by_sender_in_app(service_identity_user, app_id).fetch(
        FREE_SPONSORED_ITEMS_PER_APP)
    count = 0
    if len(news_items) == FREE_SPONSORED_ITEMS_PER_APP:
        for news_item in news_items:
            item_stats = news_item.statistics[app_id]
            if item_stats:
                count += item_stats.reached_total
    remaining_free_items = FREE_SPONSORED_ITEMS_PER_APP - len(news_items)
    return SponsoredNewsItemCount(app_id, count, remaining_free_items)


@returns([SponsoredNewsItemCount])
@arguments(service_identity_user=users.User, app_ids=[unicode])
def get_sponsored_news_count(service_identity_user, app_ids):
    """
      Calculate price for a news in every app, based on the average reach of the last five news items.
      First five news items in an app should be free.
    Args:
        service_identity_user (users.User)
        app_ids (list of unicode)
    Returns:
        things (list of SponsoredNewsItemCount)
    """
    price_per_apps = []
    for app_id in app_ids:
        news_items = NewsItem.list_sticky_by_sender_in_app(service_identity_user, app_id).fetch(
            FREE_SPONSORED_ITEMS_PER_APP)
        count = 0
        if len(news_items) == FREE_SPONSORED_ITEMS_PER_APP:
            for news_item in news_items:
                item_stats = news_item.statistics[app_id]
                if item_stats:
                    count += item_stats.reached_total
        remaining_free_items = FREE_SPONSORED_ITEMS_PER_APP - len(news_items)
        price_per_apps.append(SponsoredNewsItemCount(app_id, int(count / 5), remaining_free_items))
    return price_per_apps


def is_regional_news_enabled(app_model):
    # type: (App) -> bool
    if app_model.app_id.startswith('osa-'):
        return True
    country_code = app_model.app_id.split('-')[0].lower()
    return app_model.type == App.APP_TYPE_CITY_APP and get_apps_in_country_count(country_code) > 1


def get_news_reviews(service_user):
    parent_key = parent_ndb_key(service_user, SOLUTION_COMMON)
    return NewsReview.query(ancestor=parent_key)
