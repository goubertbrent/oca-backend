# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
# NOTICE: THIS FILE HAS BEEN MODIFIED BY GREEN VALLEY BELGIUM NV IN ACCORDANCE WITH THE APACHE LICENSE VERSION 2.0
# Copyright 2018 GIG Technology NV
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
# @@license_version:1.6@@

import logging
import os

from google.appengine.api import users as gae_users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
import webapp2

from rogerthat.bizz import channel
from rogerthat.models.news import NewsStream, NewsGroup, NewsSettingsService
from rogerthat.settings import get_server_settings


def authorize_admin():
    server_settings = get_server_settings()
    VALID_USERS = [gae_users.User(email) for email in server_settings.news_admin_emails]

    user = gae_users.get_current_user()
    logging.debug('authorize_admin: %s', user)
    if user and user in VALID_USERS:
        return True
    return False


class NewsAdminHandler(webapp2.RequestHandler):

    def dispatch(self):
        if not authorize_admin():
            self.abort(401)
        return super(NewsAdminHandler, self).dispatch()


class NewsHandler(NewsAdminHandler):

    def get(self):
        context = {'apps': []}
        app_id = self.request.get("app_id", None)
        if app_id:
            ns_items = [NewsStream.create_key(app_id).get()]
        else:
            ns_items = [ns for ns in NewsStream.query()]

        data = {}
        for ns in ns_items:
            data[ns.app_id] = {
                'ns': ns,
                'data': {
                    'id': ns.app_id,
                    'stream_type': ns.stream_type,
                    'should_create_groups': ns.should_create_groups,
                    'services_need_setup': False if app_id else ns.services_need_setup,
                    'groups': NewsGroup.list_by_app_id(ns.app_id).count(None),
                    'services': []
                },
                'queries': []
            }

            if data[ns.app_id]['data']['groups'] > 0:
                if app_id or not data[ns.app_id]['data']['services_need_setup']:
                    ids = [i for i in xrange(0, 21)]
                    ids.append(999)
                    for i in ids:
                        data[ns.app_id]['queries'].append({'id': i,
                                                           'rpc': NewsSettingsService.list_setup_needed(ns.app_id, i).count_async(None)})
            else:
                data[ns.app_id]['data']['services_need_setup'] = False

        for d in data.itervalues():
            setup_count = 0
            for qry in d['queries']:
                c = qry['rpc'].get_result()
                if c == 0:
                    continue
                if qry['id'] != 0:
                    setup_count += c
                d['data']['services'].append({'sni': qry['id'], 'c': c})

            if app_id and setup_count == 0 and d['ns'].services_need_setup:
                d['ns'].services_need_setup = False
                d['ns'].put()
        
            context['apps'].append(d['data'])

        channel.append_firebase_params(context)
        path = os.path.join(os.path.dirname(__file__), 'apps.html')
        self.response.out.write(template.render(path, context))
