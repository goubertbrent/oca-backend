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

import json
import logging
import uuid

from dateutil.relativedelta import relativedelta
from google.appengine.ext import db
from google.appengine.ext.deferred import deferred

from mcfw.cache import DSCache
from mcfw.utils import chunks
from rogerthat.bizz.job import run_job
from rogerthat.bizz.news import put_news
from rogerthat.bizz.service import re_index
from rogerthat.consts import DAY, MIGRATION_QUEUE
from rogerthat.dal.profile import is_trial_service, get_service_profile
from rogerthat.dal.service import get_service_identity, get_default_service_identity
from rogerthat.models import ServiceIdentity, FlowStatistics, App
from rogerthat.models.news import NewsItem, NewsItemImage
from rogerthat.rpc import users
from rogerthat.service.api import system
from rogerthat.to.news import NewsActionButtonTO
from rogerthat.to.statistics import FlowStatisticsTO
from rogerthat.utils import now, get_epoch_from_datetime
from rogerthat.utils.service import create_service_identity_user
from rogerthat.utils.service import get_service_user_from_service_identity_user
from rogerthat.utils.transactions import allow_transaction_propagation
from solutions import SOLUTION_FLEX, SOLUTION_COMMON, translate
from solutions.common.bizz.provisioning import get_default_language, get_and_complete_solution_settings, \
    get_and_store_main_branding, put_avatar_if_needed, populate_identity, provision_all_modules
from solutions.common.dal import get_solution_settings
from solutions.common.models import RestaurantMenu, SolutionSettings
from solutions.common.models import SolutionBrandingSettings
from solutions.common.models import SolutionScheduledBroadcast
from solutions.common.models.news import NewsCoupon
from solutions.common.models.statistics import AppBroadcastStatistics
from solutions.common.utils import limit_string
from solutions.flex.bizz import DEFAULT_COORDS


def _service_identity_worker(si_key):
    si = db.get(si_key)
    service_user = get_service_user_from_service_identity_user(si.service_identity_user)
    if not is_trial_service(service_user):
        re_index(si.service_identity_user)


def _service_identity_query():
    return ServiceIdentity.all(keys_only=True)


def _get_all_restaurant_menu_keys():
    return RestaurantMenu.all(keys_only=True)


def _migrate_menu(restaurant_menu_key):
    menu = RestaurantMenu.get(restaurant_menu_key)
    for category in menu.categories:
        if not category.id:
            category.id = unicode(str(uuid.uuid4()))
        for item in category.items:
            if not item.id:
                item.id = unicode(str(uuid.uuid4()))
    menu.put()


def _clear_qr_url_menu(restaurant_menu_key):
    menu = RestaurantMenu.get(restaurant_menu_key)
    for category in menu.categories:
        for item in category.items:
            item.qr_url = None
    menu.put()


def _get_solution_settings_keys():
    return SolutionSettings.all(keys_only=True)


def _get_solution_scheduled_broadcast_keys(_now):
    three_months_ago = _now - DAY * 30 * 3
    return SolutionScheduledBroadcast.all(keys_only=True).filter('timestamp >', three_months_ago)


def _get_app_broadcast_statistics():
    return AppBroadcastStatistics.all(keys_only=True)


def _create_news_for_app_broadcasts(app_broadcast_key):
    app_broadcast = AppBroadcastStatistics.get(app_broadcast_key)
    to_put = []
    for tag, message in zip(app_broadcast.tags, app_broadcast.messages):
        flow_stats = FlowStatistics.get(FlowStatistics.create_key(tag, app_broadcast.service_identity_user))
        if not flow_stats:  # should only happen on dev server
            logging.warn('Not creating news item for app broadcast with tag %s and message %s.', tag, message)
            return
        first_property_length = len(flow_stats.step_0_sent)
        timestamp = get_epoch_from_datetime(
            flow_stats.last_entry_datetime_date - relativedelta(days=first_property_length))
        news_item = _create_news_item(message, flow_stats.service_identity, flow_stats.service_user, u'Nieuws')
        flow_stats_to = FlowStatisticsTO.from_model(flow_stats, FlowStatisticsTO.VIEW_STEPS, 99999,
                                                    FlowStatisticsTO.GROUP_BY_YEAR)
        news_item.reach = 0
        for step in flow_stats_to.steps:
            for year_stats in step.read_count:
                news_item.reach += year_stats.count

        news_item.timestamp = timestamp + DAY / 2
        news_item.update_timestamp = now()
        to_put.append(news_item)
    if to_put:
        db.put(to_put)


def _create_news_for_scheduled_broadcast(broadcast_key, _now):
    broadcast = SolutionScheduledBroadcast.get(broadcast_key)
    if broadcast.broadcast_epoch < _now and not broadcast.target_audience_enabled:
        news_item = _create_news_item(broadcast.message, broadcast.service_identity, broadcast.service_user,
                                      broadcast.broadcast_type, json.loads(broadcast.json_urls))
        news_item.timestamp = broadcast.timestamp
        news_item.update_timestamp = now()
        news_item.put()


def _create_news_item(message, service_identity, service_user, broadcast_type, urls=None):
    if service_identity:
        service_identity_user = create_service_identity_user(service_user, service_identity)
        si = get_service_identity(service_identity_user)
    else:
        si = get_default_service_identity(service_user)
        service_identity_user = si.service_identity_user
    if '\n' in message:
        split = message.splitlines()
        title = limit_string(split[0], NewsItem.MAX_TITLE_LENGTH)
        message = '\n'.join(split[1:])
    else:
        title = limit_string(message, NewsItem.MAX_TITLE_LENGTH)
    news_buttons = []
    if urls:
        for url in urls:
            if url.get('url') and url.get('name'):
                id_ = u'url'
                caption = u'%s' % url['name']
                action = u'%s' % url['url']
                if len(caption) > NewsItem.MAX_BUTTON_CAPTION_LENGTH:
                    sln_settings = get_solution_settings(service_user)
                    caption = translate(sln_settings.main_language, SOLUTION_COMMON, u'read_more')
                news_buttons.append(NewsActionButtonTO(id_, caption, action))
                break

    app_ids = [app_id for app_id in si.appIds if app_id != App.APP_ID_OSA_LOYALTY]
    return put_news(service_identity_user,
                    sticky=False,
                    sticky_until=0,
                    title=title,
                    message=message,
                    image=None,
                    news_type=NewsItem.TYPE_NORMAL,
                    broadcast_type=broadcast_type,
                    news_buttons=news_buttons,
                    qr_code_content=None,
                    qr_code_caption=None,
                    app_ids=app_ids,
                    news_id=None,
                    accept_missing=True)


def add_ids_to_menus():
    # Run this second
    run_job(_get_all_restaurant_menu_keys, [], _migrate_menu, [],
            worker_queue=MIGRATION_QUEUE)


def clear_qr_url_from_menus():
    # Run this second
    run_job(_get_all_restaurant_menu_keys, [], _clear_qr_url_menu, [], worker_queue=MIGRATION_QUEUE)


def re_index_all_services():
    # Run this first
    run_job(_service_identity_query, [], _service_identity_worker, [],
            worker_queue=MIGRATION_QUEUE)


def provision_all_flex():
    # Run this last
    # updates branding and all modules
    run_job(_get_solution_settings_keys, [], _provision_without_publish, [],
            worker_queue=MIGRATION_QUEUE)


def generate_news_from_broadcasts():
    # Run this whenever you please (only once, though)
    _now = now()
    run_job(_get_solution_scheduled_broadcast_keys, [_now], _create_news_for_scheduled_broadcast, [_now],
            worker_queue=MIGRATION_QUEUE)
    run_job(_get_app_broadcast_statistics, [], _create_news_for_app_broadcasts, [],
            worker_queue=MIGRATION_QUEUE)


def _provision_without_publish(sln_settings_key):
    service_user = users.User(sln_settings_key.parent().name())
    service_profile = get_service_profile(service_user)
    if not service_profile or service_profile.solution != SOLUTION_FLEX:
        return

    with users.set_user(service_user):
        default_lang = get_default_language()
        sln_settings = get_and_complete_solution_settings(service_user, SOLUTION_FLEX)
        put_avatar_if_needed(service_user)
        # Force update branding settings
        branding_settings = SolutionBrandingSettings.get(SolutionBrandingSettings.create_key(service_user))
        if not branding_settings:
            return

        if branding_settings.color_scheme == u'dark':
            branding_settings.menu_item_color = SolutionBrandingSettings.default_menu_item_color(u'light')

        branding_settings.modification_time = now()
        branding_settings.color_scheme = u'light'
        branding_settings.background_color = SolutionBrandingSettings.default_background_color(
            branding_settings.color_scheme)
        branding_settings.text_color = SolutionBrandingSettings.default_text_color(branding_settings.color_scheme)
        branding_settings.show_avatar = False
        branding_settings.put()
        main_branding = get_and_store_main_branding(service_user)

        populate_identity(sln_settings, main_branding.branding_key)

        for i, label in enumerate(['About', 'History', 'Call', 'Recommend']):
            system.put_reserved_menu_item_label(i, translate(sln_settings.main_language, SOLUTION_COMMON, label))

        xg_on = db.create_transaction_options(xg=True)
        allow_transaction_propagation(db.run_in_transaction_options, xg_on, provision_all_modules, sln_settings,
                                      DEFAULT_COORDS, main_branding, default_lang)


def clear_cache():
    deferred.defer(_clear_cache, _queue=MIGRATION_QUEUE)


def nuke_news():
    for keys in chunks(list(NewsItem.all(keys_only=True)), 200):
        db.delete(keys)
    for keys in chunks(list(NewsCoupon.all(keys_only=True)), 200):
        db.delete(keys)
    for keys in chunks(list(NewsItemImage.all(keys_only=True)), 200):
        db.delete(keys)


def _clear_cache():
    chunks = list()
    qry = DSCache.all(keys_only=True)
    while True:
        keys = qry.fetch(500)
        if not keys:
            break

        chunks.append(keys)
        qry.with_cursor(qry.cursor())

    for keys in chunks:
        deferred.defer(db.delete, keys, _queue=MIGRATION_QUEUE)
