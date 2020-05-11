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

from rogerthat.pages.admin.news import NewsHandler
from rogerthat.pages.admin.news.groups import NewsGroupsHandler
from rogerthat.pages.admin.news.services import SetupNewsServiceHandler, \
    ListNewsServiceHandler
from rogerthat.wsgi import RogerthatWSGIApplication

handlers = [
    ('/mobiadmin/google/news', NewsHandler),
    ('/mobiadmin/google/news/groups', NewsGroupsHandler),
    ('/mobiadmin/google/news/services/setup', SetupNewsServiceHandler),
    ('/mobiadmin/google/news/services/list', ListNewsServiceHandler),
]

app = RogerthatWSGIApplication(handlers, True, name="main_google_authenticated", google_authenticated=True)
