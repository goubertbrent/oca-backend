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



from rogerthat.bizz.jobs.workers import re_index_job_offers
from collections import defaultdict

from google.appengine.ext import ndb

from rogerthat.bizz.communities.models import Community
from rogerthat.bizz.job import run_job, MODE_BATCH
from rogerthat.bizz.news.searching import re_index_all as re_index_all_news
from rogerthat.consts import DEBUG
from rogerthat.models.news import NewsStream, NewsGroup, NewsSettingsUser, UserNewsGroupSettings
from solutions.common.bizz.events.events_search import re_index_all_events
from solutions.common.models import SolutionRssScraperSettings
from solutions.common.models.participation import ParticipationCity


def _2_migrate_news_streams(dry_run=True):
    communities = _get_default_communities()
    to_put = []
    group_mapping = defaultdict(list)
    for news_group in NewsGroup.query():  # type: NewsGroup
        if DEBUG and news_group.app_id not in communities:
            continue
        group_mapping[news_group.community_id].append(news_group.group_id)
    skipped = []
    for news_stream in NewsStream.query():  # type: NewsStream
        app_id = news_stream.key.string_id()
        if not app_id or (DEBUG and app_id not in communities):
            continue
        if app_id in ('em-be-bare-international', 'em-be-bliep', 'em-be-butik', 'em-be-gig-foundation', 'em-be-mobietrain-demo2', 'em-be-roi-booster', 'em-es-redexis-gas', 'em-mobietrain', 'mx-contry-demo'):
            continue
        if app_id not in communities:
            skipped.append(app_id)
            continue
        community_id = communities[app_id]
        new_stream = NewsStream(key=NewsStream.create_key(community_id))
        new_stream.stream_type = news_stream.stream_type
        new_stream.should_create_groups = news_stream.should_create_groups
        new_stream.services_need_setup = news_stream.services_need_setup
        new_stream.layout = news_stream.layout
        new_stream.group_ids = group_mapping[community_id]
        to_put.append(new_stream)
    if dry_run:
        return to_put
    if skipped:
        return skipped
    ndb.put_multi(to_put)


def _2_4_migrate_news_settings_user():
    run_job(_get_news_settings_users, [], _migrate_news_settings_users, [], mode=MODE_BATCH)


def _get_news_settings_users():
    return NewsSettingsUser.query()


def _migrate_news_settings_users(keys):
    models = ndb.get_multi(keys)  # type: List[NewsSettingsUser]
    for settings in models:
        settings.group_settings = []
        for group in settings.groups:
            for group_details in group.details:
                if not group_details.last_load_request:
                    continue
                new_settings = UserNewsGroupSettings()
                new_settings.group_id = group_details.group_id
                new_settings.notifications = group_details.notifications
                new_settings.last_load_request = group_details.last_load_request
                settings.group_settings.append(new_settings)
    ndb.put_multi(models)



def _get_default_communities():
    # type: () -> Dict[str, int]
    return {community.default_app: community.id for community in Community.query()}


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
                link.community_ids.append(communities[app_id])
        to_put.append(rss_settings)
    ndb.put_multi(to_put)


def _9_reindex_events():
    re_index_all_events()


def _10_reindex_services():
    from rogerthat.bizz.job.re_index_service_identities import job
    job()


def _11_nuke_participation():
    ndb.delete_multi(ParticipationCity.query().fetch(None, keys_only=True))


def _12_reindex_jobs():
    re_index_job_offers()
