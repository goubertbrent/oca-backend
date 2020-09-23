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

import datetime
import logging

import webapp2
from google.appengine.ext import ndb

from rogerthat.bizz.communities.communities import get_communities_by_id
from rogerthat.bizz.news import processed_timeout_stickied_news
from rogerthat.bizz.news.influx.exporter import run as run_export
from rogerthat.models.news import NewsStream, NewsGroup, NewsSettingsService
from rogerthat.settings import get_server_settings
from rogerthat.utils import send_mail


class NewsStatisticsHandler(webapp2.RequestHandler):

    def get(self):
        run_export()


class NewsGroupVisibilityHandler(webapp2.RequestHandler):

    def get(self):
        dt = datetime.datetime.utcnow()
        to_put = []
        for ng in NewsGroup.list_by_visibility_date(dt):  # type: NewsGroup
            logging.debug('NewsGroupVisibilityHandler group_id:%s visible_until:%s', ng.group_id, ng.visible_until)
            if not ng.visible_until:
                logging.debug('skipping')
                continue
            logging.debug('updating')
            ng.visible_until = None
            ng.send_notifications = False

            news_stream = NewsStream.create_key(ng.community_id).get()
            news_stream.custom_layout_id = None

            to_put.extend([news_stream, ng])

        if to_put:
            ndb.put_multi(to_put)


class NewsUnstickHandler(webapp2.RequestHandler):

    def get(self):
        processed_timeout_stickied_news()


class NewsServiceSetupHandler(webapp2.RequestHandler):

    def get(self):
        query_mapping = {}
        for ns in NewsStream.query():  # type: NewsStream
            ng_count = NewsGroup.list_by_community_id(ns.community_id).count(None)
            if ng_count == 0:
                continue

            ids = [i for i in xrange(1, 21)]
            ids.append(999)

            query_mapping[ns.community_id] = [
                NewsSettingsService.list_setup_needed(ns.community_id, i).count_async(None) for i in ids
            ]

        data = {}
        for community_id, queries in query_mapping.iteritems():
            setup_count = 0
            for qry in queries:
                setup_count += qry.get_result()

            if setup_count > 0:
                data[community_id] = setup_count

        if not data:
            return

        r = ''
        communities = get_communities_by_id(data.keys())
        results = [(community.name, count) for community, count in zip(communities, data.itervalues())]
        for community_name, count in sorted(results, key=lambda item: -item[1]):
            r += '%s: %s services\n' % (community_name, count)

        server_settings = get_server_settings()
        send_mail(server_settings.dashboardEmail,
                  server_settings.news_admin_emails,
                  'News group setup required',
                  'Setup services here: %s/mobiadmin/google/news\n'
                  'The following apps have unconnected news services:\n\n%s' % (server_settings.baseUrl, r))
