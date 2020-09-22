# -*- coding: utf-8 -*-
# Copyright 2020 Green Valley NV
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

import logging
from collections import defaultdict
from datetime import datetime

from google.appengine.ext import ndb, db
from typing import Dict, List

from rogerthat.bizz.communities.models import CommunityAutoConnectedService, Community, AppFeatures
from rogerthat.bizz.job import run_job, MODE_BATCH
from rogerthat.bizz.news.searching import re_index_all as re_index_all_news
from rogerthat.consts import MIGRATION_QUEUE, DEBUG
from rogerthat.dal import put_in_chunks, put_and_invalidate_cache
from rogerthat.models import App, UserProfile, ServiceProfile, ServiceIdentity, AppServiceFilter
from rogerthat.models.jobs import JobOffer
from rogerthat.models.news import NewsItem, NewsGroup, NewsSettingsService
from rogerthat.rpc import users
from rogerthat.utils.service import remove_slash_default
from shop.migrations import re_index_all_customers
from shop.models import Customer, ShopApp
from solutions.common.bizz.events.events_search import re_index_all_events
from solutions.common.models import SolutionRssLink, SolutionRssScraperSettings
from solutions.common.models.agenda import Event
from solutions.common.models.cityapp import CityAppProfile
from solutions.common.models.news import NewsReview, SolutionNewsItem
from solutions.common.models.participation import ParticipationCity


def _1_create_communities_from_apps(dry_run=True):
    if DEBUG:
        ndb.delete_multi(Community.query().fetch(keys_only=True))
    communities_to_put = []
    shop_apps = {a.app_id: a for a in ShopApp.query()}  # type: Dict[str, ShopApp]
    city_app_profiles = {p.service_user.email(): p for p in
                         CityAppProfile.query()}  # type: Dict[basestring, CityAppProfile]
    all_apps = App.all().fetch(None)  # type: List[App]
    for app in all_apps:
        community = Community()
        community.auto_connected_services = [CommunityAutoConnectedService(
            service_email=remove_slash_default(users.User(service.service_identity_email)).email(),
            removable=service.removable
        ) for service in app.auto_connected_services]
        community.create_date = datetime.utcfromtimestamp(app.creation_time) if app.creation_time else datetime.now()
        community.country = app.country
        community.default_app = app.app_id
        community.demo = app.demo
        community.main_service = app.main_service
        community.embedded_apps = app.embedded_apps
        community.name = app.name
        if app.app_id in shop_apps:
            shop_app = shop_apps[app.app_id]
            community.signup_enabled = shop_app.signup_enabled
            community.features = shop_app.paid_features
            if shop_app.paid_features_enabled:
                community.features.append(AppFeatures.NEWS_VIDEO)
        else:
            community.signup_enabled = False
            community.features = []
        if app.app_id.startswith('osa-demo'):
            community.features.append(AppFeatures.NEWS_LOCATION_FILTER)
        profile = city_app_profiles.get(app.main_service)
        if profile:
            if profile.review_news:
                community.features.append(AppFeatures.NEWS_REVIEW)
            if profile.gather_events_enabled:
                community.features.append(AppFeatures.EVENTS_SHOW_MERCHANTS)
        community.features.append(AppFeatures.NEWS_REGIONAL)
        communities_to_put.append(community)
    if dry_run:
        return communities_to_put
    ndb.put_multi(communities_to_put)
    apps_to_put = []
    for app, community in zip(all_apps, communities_to_put):
        app.service_filter_type = AppServiceFilter.COUNTRY
        app.community_ids = [community.id]
        apps_to_put.append(app)
    put_and_invalidate_cache(*apps_to_put)


def _2_migrate_news_groups(dry_run=True):
    communities = _get_default_communities()
    to_put = []
    group_mapping = defaultdict(list)
    for news_group in NewsGroup.query():  # type: NewsGroup
        if DEBUG and news_group.app_id not in communities:
            continue
        news_group.community_id = communities[news_group.app_id]
        group_mapping[news_group.community_id].append(news_group.group_id)
        to_put.append(news_group)
    if dry_run:
        return to_put
    ndb.put_multi(to_put)


def _2_1_migrate_news_settings():
    communities = _get_default_communities()
    to_put = []
    for settings in NewsSettingsService.query():  # type: NewsSettingsService
        settings.community_id = communities[settings.default_app_id]
        to_put.append(settings)
        if len(to_put) == 500:
            ndb.put_multi(to_put)
            to_put = []
    ndb.put_multi(to_put)


def _2_2_migrate_news_reviews():
    communities = _get_default_communities()
    to_put = []
    for review in NewsReview.query():  # type: NewsReview
        review.community_id = communities[review.app_id]
        to_put.append(review)
        if len(to_put) == 500:
            ndb.put_multi(to_put)
            to_put = []
    ndb.put_multi(to_put)


def _2_3_migrate_news_sln_items():
    communities = _get_default_communities()
    to_put = []
    for item in SolutionNewsItem.query():  # type: SolutionNewsItem
        item.community_ids = [communities[app_id] for app_id in item.app_ids]
        to_put.append(item)
        if len(to_put) == 500:
            ndb.put_multi(to_put)
            to_put = []
    ndb.put_multi(to_put)


def _3_migrate_customers():
    communities = _get_default_communities()
    to_put = []
    for customer in Customer.all():  # type: Customer
        customer.community_id = communities[customer.app_id]
        to_put.append(customer)
    put_in_chunks(to_put)
    re_index_all_customers()


def _4_migrate_profiles():
    communities = _get_default_communities()
    run_job(_get_user_profiles, [], _set_community_id_on_user_profiles, [communities], mode=MODE_BATCH,
            worker_queue=MIGRATION_QUEUE)
    run_job(_get_service_profiles, [], _set_community_id_on_service_profiles, [communities], mode=MODE_BATCH,
            worker_queue=MIGRATION_QUEUE)


def _get_user_profiles():
    return UserProfile.all(keys_only=True)


def _get_service_profiles():
    return ServiceProfile.all(keys_only=True)


def _set_community_id_on_user_profiles(profile_keys, communities):
    # type: (List[db.Key], Dict[str, int]) -> None
    profiles = db.get(profile_keys)  # type: List[UserProfile]
    for profile in profiles:
        profile.community_id = communities[profile.app_id]
    put_and_invalidate_cache(*profiles)


def _set_community_id_on_service_profiles(profile_keys, communities):
    # type: (List[db.Key], Dict[str, int]) -> None
    profiles = db.get(profile_keys)  # type: List[ServiceProfile]
    service_identities = db.get([ServiceIdentity.keyFromService(profile.service_user, ServiceIdentity.DEFAULT)
                                 for profile in profiles])  # type: List[ServiceIdentity]
    for profile, service_identity in zip(profiles, service_identities):
        profile.community_id = communities[service_identity.app_id]
    put_and_invalidate_cache(*profiles)


def _get_default_communities():
    # type: () -> Dict[str, int]
    return {community.default_app: community.id for community in Community.query()}


def _6_migrate_news_items():
    communities = _get_default_communities()
    run_job(_fetch_all_news, [], _migrate_news_items, [communities], mode=MODE_BATCH, worker_queue=MIGRATION_QUEUE)


def _fetch_all_news():
    return NewsItem.query()


def _migrate_news_items(keys, community_mappings):
    # type: (List[ndb.Key], Dict[str, int]) -> None
    news_items = ndb.get_multi(keys)  # type: List[NewsItem]
    for news_item in news_items:
        if DEBUG:
            news_item.community_ids = [community_mappings[app_id] for app_id in news_item.app_ids]
        else:
            news_item.community_ids = [community_mappings[app_id] for app_id in news_item.app_ids
                                       if app_id not in BLACKLISTED_APP_IDS]
        if not news_item.community_ids:
            logging.warning('News item has no communities: %s', news_item.id)
    ndb.put_multi(news_items)


def _6_1_index_news_items():
    re_index_all_news()


def _7_migrate_rss():
    to_put = []
    communities = _get_default_communities()
    for rss_settings in SolutionRssScraperSettings.query(): # type: SolutionRssScraperSettings
        for link in rss_settings.rss_links:  # type: SolutionRssLink
            link.community_ids = []
            for app_id in link.app_ids:
                if DEBUG and app_id not in communities:
                    continue
                if app_id in BLACKLISTED_APP_IDS:
                    continue
                link.community_ids.append(communities[app_id])
        to_put.append(rss_settings)
    ndb.put_multi(to_put)


def _8_migrate_events(dry_run=True):
    communities = _get_default_communities()

    total_updated = 0
    start_cursor = None
    has_more = True
    while has_more:
        events, start_cursor, has_more = Event.query().fetch_page(500, start_cursor=start_cursor)
        total_updated += len(events)
        for event in events:
            app_id = event.app_ids[0]
            event.community_id = communities[app_id]
        if not dry_run:
            ndb.put_multi(events)
    return total_updated


def _9_reindex_events():
    re_index_all_events()


def _10_reindex_services():
    from rogerthat.bizz.job.re_index_service_identities import job
    job()


def _11_nuke_participation():
    ndb.delete_multi(ParticipationCity.query().fetch(None, keys_only=True))


def _get_job_offers_qry():
    return JobOffer.query()


def _migrate_job_offers(keys):
    offers = ndb.get_multi(keys)  # type: List[JobOffer]
    for offer in offers:
        offer.demo = len(offer.demo_app_ids) > 0
        if offer.invisible_reason == 'dubble':
            offer.invisible_reason = JobOffer.INVISIBLE_REASON_DOUBLE
    ndb.put_multi(offers)


def _12_jobs():
    run_job(_get_job_offers_qry, [], _migrate_job_offers, [], mode=MODE_BATCH)
