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

import os

from google.appengine.ext.webapp import template

from rogerthat.bizz import channel
from rogerthat.models.news import NewsGroup, NewsItem
from rogerthat.pages.admin.news import NewsAdminHandler


class NewsGroupsHandler(NewsAdminHandler):

    def get(self):
        app_id = self.request.get("app_id", None)
        if app_id:
            qry = NewsGroup.list_by_app_id(app_id)
        else:
            qry = NewsGroup.query()

        groups_dict = {}
        for g in qry:
            groups_dict[g.group_id] = dict(group=g, rpc=NewsItem.list_published_by_group_id(g.group_id).count_async())

        groups = []
        for v in groups_dict.values():
            v['group'].ni_count = v['rpc'].get_result()
            groups.append(v['group'])
        context = dict(groups=sorted(groups, key=lambda x: x.name))

        channel.append_firebase_params(context)
        path = os.path.join(os.path.dirname(__file__), 'groups.html')
        self.response.out.write(template.render(path, context))
