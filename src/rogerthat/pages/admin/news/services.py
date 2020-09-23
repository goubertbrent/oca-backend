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
import json
import logging
import os

from google.appengine.ext.deferred import deferred
from google.appengine.ext.webapp import template

from rogerthat.bizz import channel
from rogerthat.bizz.rtemail import generate_auto_login_url
from rogerthat.consts import NEWS_MATCHING_QUEUE
from rogerthat.dal.profile import get_service_profile, get_service_visible
from rogerthat.dal.service import get_service_identities, count_users_connected_to_service_identity
from rogerthat.migrations.migrate_news_items import migrate_service
from rogerthat.models.news import NewsSettingsService, NewsItem, NewsGroup, \
    NewsSettingsServiceGroup
from rogerthat.pages.admin.news import NewsAdminHandler
from rogerthat.rpc import users
from rogerthat.rpc.models import ServiceLog


def get_last_activity(service_user):
    last_activity = ServiceLog.all().filter('user', service_user).order('-timestamp').get()
    if not last_activity:
        return None
    return datetime.datetime.utcfromtimestamp((last_activity.timestamp / 1000))


def get_days_between_last_activity(d1):
    d2 = datetime.datetime.utcnow()
    return (d2 - d1).days


class SetupNewsServiceHandler(NewsAdminHandler):

    def get(self):
        community_id = self.request.get("community_id", None)
        sni = self.request.get("sni", None)
        if not community_id or not sni:
            self.redirect('/mobiadmin/google/news')
            return

        sni = int(sni)
        qry = NewsSettingsService.list_setup_needed(community_id, sni)
        item = qry.get()
        if not item:
            self.redirect('/mobiadmin/google/news?community_id=%s' % community_id)
            return

        sp = get_service_profile(item.service_user)
        last_activity = get_last_activity(item.service_user)
        latest_activity_days = get_days_between_last_activity(last_activity) if last_activity else -1
        disabled_reason = None
        if sp.solution and sp.solution == u'flex':
            try:
                from shop.models import Customer
                c = Customer.get_by_service_email(item.service_user.email())
                if c and c.service_disabled_at:
                    disabled_reason = c.disabled_reason
            except:
                pass

        identities = []

        total_user_count = 0
        all_hidden = True
        for si in get_service_identities(item.service_user):
            news_count = NewsItem.query().filter(NewsItem.sender == si.user).count(None)
            user_count = count_users_connected_to_service_identity(si.user)
            total_user_count += user_count
            service_visible = get_service_visible(si.user)
            if service_visible and all_hidden:
                all_hidden = False
            identities.append(dict(id=si.identifier,
                                   name=si.name,
                                   news_count=news_count,
                                   user_count=user_count,
                                   search_enabled=service_visible))

        delete_enabled = False
        if disabled_reason:
            delete_enabled = True
        elif total_user_count == 0 and all_hidden:
            delete_enabled = True
        elif latest_activity_days > 300 and total_user_count < 20 and all_hidden:
            delete_enabled = True

        context = dict(sni=sni,
                       count=qry.count(None),
                       item=item,
                       sp=sp,
                       auto_login_url=generate_auto_login_url(item.service_user),
                       latest_activity=dict(date=str(last_activity) if last_activity else 'never', days=latest_activity_days),
                       delete_enabled=delete_enabled,
                       disabled_reason=disabled_reason,
                       identities=identities)
        path = os.path.join(os.path.dirname(__file__), 'services_detail.html')
        channel.append_firebase_params(context)
        self.response.out.write(template.render(path, context))

    def post(self):
        logging.debug(self.request.POST)
        data = self.request.get("data", None)
        if not data:
            self.redirect('/mobiadmin/google/news')
            return

        self.response.headers['Content-Type'] = 'text/json'

        data = json.loads(data)

        service_user_email = data.get("service_user_email", None)
        action = data.get("action", None)
        nss = NewsSettingsService.create_key(users.User(service_user_email)).get()  # type: NewsSettingsService
        if action == 'delete':
            should_delete = False
            try:
                from shop.models import Customer
                c = Customer.get_by_service_email(service_user_email)
                if c and c.service_disabled_at:
                    should_delete = True
            except:
                pass

            total_user_count = 0
            for si in get_service_identities(nss.service_user):
                user_count = count_users_connected_to_service_identity(si.user)
                total_user_count += user_count

            if total_user_count == 0:
                should_delete = True

            last_activity = get_last_activity(nss.service_user)
            if not should_delete and not last_activity:
                self.response.out.write(json.dumps({'success': False,
                                                    'errormsg': 'Delete failed could not find last activity'}))
                return

            latest_activity_days = get_days_between_last_activity(last_activity) if last_activity else -1
            if not should_delete and latest_activity_days <= 300:
                self.response.out.write(json.dumps({'success': False,
                                                    'errormsg': 'Service was active in the last 300 days'}))
                return

            nss.setup_needed_id = 998
            nss.put()

            service_profile = get_service_profile(nss.service_user, False)
            if service_profile.solution:
                from solutions.common.bizz.jobs import delete_solution
                delete_solution(nss.service_user, True)
            else:
                from rogerthat.bizz.job import delete_service
                delete_service.job(nss.service_user, nss.service_user)

        elif action == 'skip':
            nss.setup_needed_id = 999
            nss.put()
        elif action == 'save_group':
            groups = data.get("groups", None)
            if not groups:
                self.response.out.write(json.dumps({'success': False,
                                                    'errormsg': 'This is awkward... (groups not found)'}))
                return

            group_types = [ng.group_type for ng in NewsGroup.list_by_community_id(nss.community_id)]
            nss.setup_needed_id = 0
            nss.groups = []
            if groups == 'city':
                if NewsGroup.TYPE_CITY in group_types:
                    nss.groups.append(NewsSettingsServiceGroup(group_type=NewsGroup.TYPE_CITY))
                if NewsGroup.TYPE_TRAFFIC in group_types:
                    nss.groups.append(NewsSettingsServiceGroup(group_type=NewsGroup.TYPE_TRAFFIC))
                if NewsGroup.TYPE_EVENTS in group_types:
                    nss.groups.append(NewsSettingsServiceGroup(group_type=NewsGroup.TYPE_EVENTS))
            elif groups == 'other':
                if NewsGroup.TYPE_PROMOTIONS in group_types:
                    nss.groups.append(NewsSettingsServiceGroup(group_type=NewsGroup.TYPE_PROMOTIONS))
                if NewsGroup.TYPE_EVENTS in group_types:
                    nss.groups.append(NewsSettingsServiceGroup(group_type=NewsGroup.TYPE_EVENTS))
            else:
                self.response.out.write(json.dumps({'success': False,
                                                    'errormsg': 'This is awkward... (group not found)'}))
                return

            if not nss.groups:
                logging.debug(group_types)
                self.response.out.write(json.dumps({'success': False,
                                                    'errormsg': 'This is awkward... (no group matches)'}))
                return

            nss.put()
            deferred.defer(migrate_service, nss.service_user, dry_run=False, force=True, _countdown=5, _queue=NEWS_MATCHING_QUEUE)

        self.response.out.write(json.dumps({'success': True}))


class ListNewsServiceHandler(NewsAdminHandler):

    def get(self):
        community_id = self.request.get("community_id", None)
        sni = self.request.get("sni", None)
        if not community_id or not sni:
            self.redirect('/mobiadmin/google/news')
            return

        sni = int(sni)
        qry = NewsSettingsService.list_setup_needed(community_id, sni)

        items = []
        for nss in qry:
            last_activity = get_last_activity(nss.service_user)
            latest_activity_days = get_days_between_last_activity(last_activity) if last_activity else -1

            identities = []
            for si in get_service_identities(nss.service_user):
                news_count = NewsItem.query().filter(NewsItem.sender == si.user).count(None)
                service_visible = get_service_visible(si.user)
                identities.append(dict(id=si.identifier,
                                       name=si.name,
                                       news_count=news_count,
                                       search_enabled=service_visible))

            items.append(dict(service_user_email=nss.service_user.email(),
                              latest_activity=dict(date=str(last_activity) if last_activity else 'never', days=latest_activity_days),
                              identities=identities))

        context = dict(items=items)
        path = os.path.join(os.path.dirname(__file__), 'services_list.html')
        channel.append_firebase_params(context)
        self.response.out.write(template.render(path, context))
