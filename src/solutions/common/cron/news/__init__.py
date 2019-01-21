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

import importlib
import logging
from HTMLParser import HTMLParser

from google.appengine.ext import webapp

from markdownify import markdownify
from mcfw.rpc import arguments, returns
from mcfw.utils import chunks
from rogerthat.dal.service import get_default_service_identity
from rogerthat.models.news import NewsItem
from rogerthat.rpc import users
from rogerthat.service.api import news
from rogerthat.to.news import NewsActionButtonTO
from solution_server_settings import get_solution_server_settings
from solutions import translate as common_translate
from solutions.common import SOLUTION_COMMON
from solutions.common.models import SolutionSettings
from solutions.common.utils import limit_string

BROADCAST_TYPE_NEWS = u"News"


class SolutionNewsScraper(webapp.RequestHandler):

    def get(self):
        solution_server_settings = get_solution_server_settings()
        for module_name, service_user in chunks(solution_server_settings.solution_news_scrapers, 2):
            try:
                module = importlib.import_module("solutions.common.cron.news.%s" % module_name)
                getattr(module, 'check_for_news')(users.User(service_user))
            except:
                pass


def transl(key, language):
    try:
        return common_translate(language, SOLUTION_COMMON, key, suppress_warning=True)
    except:
        return key


@returns()
@arguments(sln_settings=SolutionSettings, broadcast_type=unicode, message=unicode, title=unicode, permalink=unicode,
           notify=bool)
def create_news_item(sln_settings, broadcast_type, message, title, permalink, notify=False):
    service_user = sln_settings.service_user
    logging.info('Creating news item:\n- %s\n- %s\n- %s\n- %s\n- %s - Notification: %s', service_user, message, title,
                 broadcast_type, permalink, notify)

    with users.set_user(service_user):
        sticky = False
        sticky_until = 0
        image = None
        news_type = NewsItem.TYPE_NORMAL
        link_caption = transl(u'More info', sln_settings.main_language)
        action_button = NewsActionButtonTO(u'url', link_caption, permalink)
        qr_code_content = None
        qr_code_caption = None
        si = get_default_service_identity(service_user)
        app_ids = si.appIds

        title = limit_string(title, NewsItem.MAX_TITLE_LENGTH)
        flags = NewsItem.DEFAULT_FLAGS
        if not notify:
            flags = flags | NewsItem.FLAG_SILENT
        news.publish(sticky=sticky,
                     sticky_until=sticky_until,
                     title=title,
                     message=message,
                     image=image,
                     news_type=news_type,
                     flags=flags,
                     broadcast_type=broadcast_type,
                     action_buttons=[action_button],
                     qr_code_content=qr_code_content,
                     qr_code_caption=qr_code_caption,
                     scheduled_at=0,
                     app_ids=app_ids)


def html_unescape(s):
    return HTMLParser().unescape(s)


def html_to_markdown(html_content):
    if not html_content:
        return html_content

    return markdownify(html_content)
