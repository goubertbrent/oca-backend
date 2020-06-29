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

from google.appengine.ext import ndb

from mcfw.consts import MISSING, REST_TYPE_TO
from mcfw.exceptions import HttpBadRequestException, HttpNotFoundException
from mcfw.properties import azzert
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.consts import DEBUG
from rogerthat.dal.app import get_app_by_id
from rogerthat.models import ServiceIdentity
from rogerthat.models.jobs import JobOffer
from rogerthat.models.news import NewsGroup, MediaType
from rogerthat.models.settings import ServiceInfo
from rogerthat.rpc import users
from rogerthat.rpc.service import ServiceApiException
from rogerthat.service.api import system
from rogerthat.service.api.news import list_groups
from rogerthat.to import ReturnStatusTO, RETURNSTATUS_TO_SUCCESS
from rogerthat.to.news import NewsItemTO, NewsItemListResultTO, NewsActionButtonTO
from rogerthat.utils.service import create_service_identity_user
from shop.exceptions import BusinessException
from shop.models import ShopApp
from solutions import translate as common_translate
from solutions.common.bizz.news import get_news, put_news_item, delete_news, get_news_statistics, get_news_reviews, \
    send_news_review_reply, publish_item_from_review, AllNewsSentToReviewWarning, get_locations, \
    is_regional_news_enabled, check_can_send_news
from solutions.common.dal import get_solution_settings
from solutions.common.dal.cityapp import get_service_user_for_city
from solutions.common.models.news import NewsSettings, NewsSettingsTags
from solutions.common.to.broadcast import NewsOptionsTO, RegionalNewsSettingsTO, NewsActionButtonWebsite, \
    NewsActionButtonAttachment, NewsActionButtonEmail, NewsActionButtonPhone, NewsActionButtonMenuItem, \
    NewsActionButtonOpen
from solutions.common.to.news import NewsStatsTO, NewsReviewTO, CreateNewsItemTO
from solutions.common.utils import is_default_service_identity


def _translate_exception_msg(sln_settings, msg):
    try:
        return common_translate(sln_settings.main_language, msg)
    except ValueError:
        return msg


@rest('/common/news', 'get', read_only_access=True, silent_result=True)
@returns(NewsItemListResultTO)
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
@returns(NewsItemTO)
@arguments(news_id=(int, long), data=CreateNewsItemTO)
def rest_put_news_item(news_id, data):
    # type: (int, CreateNewsItemTO) -> NewsItemTO
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    if is_default_service_identity(service_identity):
        service_identity_user = create_service_identity_user(service_user)
    else:
        service_identity_user = create_service_identity_user(service_user, service_identity)

    try:
        return put_news_item(
            service_identity_user, data.title, data.message, MISSING.default(data.action_button, None), data.type,
            data.qr_code_caption, data.app_ids, data.scheduled_at, news_id,
            target_audience=data.target_audience, role_ids=data.role_ids,
            tag=data.tag, media=data.media, group_type=data.group_type, locations=data.locations,
            group_visible_until=data.group_visible_until, accept_missing=True)
    except AllNewsSentToReviewWarning:
        return None
    except BusinessException as ex:
        sln_settings = get_solution_settings(service_user)
        message = _translate_exception_msg(sln_settings, ex.message)
        raise HttpBadRequestException('oca.error', {'message': message})


@rest('/common/news', 'post', silent_result=True, type=REST_TYPE_TO)
@returns(NewsItemTO)
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
@returns((ReturnStatusTO, NewsItemTO))
@arguments(review_key=unicode)
def rest_publish_news_from_review(review_key):
    try:
        return publish_item_from_review(review_key)
    except BusinessException as ex:
        sln_settings = get_solution_settings(users.get_current_user())
        message = _translate_exception_msg(sln_settings, ex.message)
        return ReturnStatusTO.create(False, message)


@rest('/common/locations/<app_id:[^/]+>', 'get', silent_result=True)
@returns(dict)
@arguments(app_id=unicode)
def rest_locations(app_id):
    locations = get_locations(app_id)
    if not locations:
        raise HttpNotFoundException('oca.errors.no_locations_for_city')
    return locations.to_dict(extra_properties=['app_id'])


@rest("/common/news-options", "get", read_only_access=True, silent_result=True)
@returns(NewsOptionsTO)
@arguments()
def rest_get_news_options():
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity or ServiceIdentity.DEFAULT
    sln_settings = get_solution_settings(service_user)
    service_info = ServiceInfo.create_key(service_user, service_identity).get()
    lang = sln_settings.main_language
    check_can_send_news(sln_settings, service_info)
    info = system.get_info(service_identity)
    news_settings_key = NewsSettings.create_key(service_user, service_identity)
    keys = [news_settings_key, ShopApp.create_key(info.default_app)]
    news_settings, shop_app = ndb.get_multi(keys)  # type: NewsSettings, ShopApp
    if not news_settings:
        news_settings = NewsSettings(key=news_settings_key)
    if not shop_app:
        shop_app = ShopApp()
    # For demo apps and for shop sessions, creating regional news items is free.
    default_app = get_app_by_id(info.default_app)
    tags = news_settings.tags
    if session_.shop or default_app.demo and NewsSettingsTags.FREE_REGIONAL_NEWS not in news_settings.tags:
        tags.append(NewsSettingsTags.FREE_REGIONAL_NEWS)

    news_groups = list_groups(lang)
    jobs_rpc = JobOffer.list_by_service(service_user.email()).fetch_async()

    regional_enabled_types = (NewsGroup.TYPE_PRESS, NewsGroup.TYPE_PROMOTIONS)
    regional_news_enabled = any(g.group_type in regional_enabled_types for g in news_groups) or DEBUG
    map_url = None
    if regional_news_enabled:
        regional_news_enabled = is_regional_news_enabled(default_app)
        if DEBUG or regional_news_enabled and (default_app.country == 'BE' or default_app.demo):
            map_url = '/static/js/shop/libraries/flanders.json'
    regional = RegionalNewsSettingsTO(enabled=regional_news_enabled, map_url=map_url)
    media_types = [MediaType.IMAGE]
    if default_app.demo or shop_app.paid_features_enabled:
        media_types.append(MediaType.VIDEO_YOUTUBE)
    action_buttons = [
        NewsActionButtonWebsite(label=common_translate(lang, 'Website'),
                                icon='http',
                                button=NewsActionButtonTO('url',
                                                          common_translate(lang, 'open_website'),
                                                          '')),
        NewsActionButtonAttachment(label=common_translate(lang, 'Attachment'),
                                   icon='attachment',
                                   button=NewsActionButtonTO('attachment',
                                                             common_translate(lang, 'Attachment'),
                                                             '')),
        NewsActionButtonEmail(label=common_translate(lang, 'email_address'),
                              icon='alternate_email',
                              email='',
                              button=NewsActionButtonTO('email',
                                                        common_translate(lang, 'send_email'),
                                                        '')),
        NewsActionButtonPhone(label=common_translate(lang, 'Phone number'),
                              icon='call',
                              phone='',
                              button=NewsActionButtonTO('phone',
                                                        common_translate(lang, 'Call'),
                                                        '')),
    ]
    menu = system.get_menu()
    action_buttons.extend([NewsActionButtonMenuItem(label=item.label,
                                                    icon='link',
                                                    button=NewsActionButtonTO(item.tag, item.label[0:15],
                                                                              'smi://' + item.tag))
                           for item in menu.items if not item.roles])

    open_actions = [
        ('scan', common_translate(lang,  'Scan')),
        ('profile', common_translate(lang, 'profile')),
        ('settings', common_translate(lang,  'Settings')),
        ('messages', common_translate(lang,  'news_items')),
    ]

    for action, label in open_actions:
        action_buttons.append(NewsActionButtonOpen(label=label,
                                                   icon='settings',
                                                   button=NewsActionButtonTO('open', label[:15],
                                                                             'open://{"action":"%s"}' % action)))
    for job_offer in jobs_rpc.get_result():  # type: JobOffer
        if not job_offer.visible:
            continue
        action_buttons.append(NewsActionButtonOpen(
            label=job_offer.info.function.title,
            icon='work',
            button=NewsActionButtonTO('job', common_translate(lang,  'oca.apply_for_job'),
                                      'open://{"action_type":"job","action":"%s"}' % job_offer.id)
        ))

    return NewsOptionsTO(tags=tags, regional=regional, groups=news_groups, media_types=media_types,
                         # location_filter_enabled=shop_app.paid_features_enabled)
                         location_filter_enabled=default_app.demo or DEBUG,
                         action_buttons=action_buttons)
