# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
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

import webapp2

from rogerthat.rpc import users
from solutions.common.bizz.discussion_groups import get_discussion_group_pdf


class DiscussionGroupsPdfHandler(webapp2.RequestHandler):
    def get(self, discussion_group_id):
        discussion_group_id = long(discussion_group_id)
        service_user = users.get_current_user()
        pdf = get_discussion_group_pdf(service_user, discussion_group_id)
        self.response.headers['Content-Type'] = 'application/pdf'
        self.response.out.write(pdf)
