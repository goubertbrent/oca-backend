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

import os

from google.appengine.ext.webapp import template

from rogerthat.bizz import channel
from rogerthat.models.news import NewsGroup, NewsItem
from rogerthat.pages.admin.news import NewsAdminHandler


class NewsGroupsHandler(NewsAdminHandler):

    def get(self):
        community_id = self.request.get("community_id", None)
        if community_id:
            community_id = long(community_id)
            qry = NewsGroup.list_by_community_id(community_id)
        else:
            qry = NewsGroup.query()
        groups_dict = {g.group_id: (g, NewsItem.list_published_by_group_id_sorted(g.group_id).count_async())
                       for g in qry}
        groups = []
        for group, rpc in groups_dict.values():
            group.ni_count = rpc.get_result()
            groups.append(group)
        context = {'groups': sorted(groups, key=lambda x: x.name)}

        channel.append_firebase_params(context)
        path = os.path.join(os.path.dirname(__file__), 'groups.html')
        self.response.out.write(template.render(path, context))
