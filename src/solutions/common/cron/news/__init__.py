# -*- coding: utf-8 -*-
# Copyright 2016 Mobicage NV
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
# @@license_version:1.1@@

from htmlentitydefs import name2codepoint
import importlib
import logging
import re

from google.appengine.ext import webapp
from google.appengine.ext.deferred import deferred
import html2text
from mcfw.rpc import arguments, returns
from rogerthat.dal.service import get_default_service_identity
from rogerthat.models.news import NewsItem
from rogerthat.rpc import users
from rogerthat.service.api import news
from rogerthat.to.news import NewsActionButtonTO
from solution_server_settings import get_solution_server_settings
from solutions import translate as common_translate
from solutions.common import SOLUTION_COMMON
from solutions.common.models import SolutionSettings


BROADCAST_TYPE_NEWS = u"News"


class SolutionNewsScraper(webapp.RequestHandler):

    def get(self):
        solution_server_settings = get_solution_server_settings()
        for module_name, service_user in solution_server_settings.solution_news_scrapers:
            try:
                module = importlib.import_module("solutions.common.cron.news.%s" % module_name)
                getattr(module, 'check_for_news')(service_user)
            except:
                pass

def transl(key, language):
    try:
        return common_translate(language, SOLUTION_COMMON, key, suppress_warning=True)
    except:
        return key


@returns()
@arguments(sln_settings=SolutionSettings, broadcast_type=unicode, message=unicode, title=unicode, permalink=unicode)
def create_news_item(sln_settings, broadcast_type, message, title, permalink):
    service_user = sln_settings.service_user
    title = title.strip()
    message = message.strip() if message else None
    logging.info('Creating news item:\n- %s\n- %s\n- %s\n- %s\n- %s', service_user, message, title, broadcast_type,
                 permalink)

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

        if len(title) > 80:
            title = title[:77] + '...'
        if message and len(message) > 497:
            message = message[:497] + '...'

        news.publish(sticky, sticky_until, title, message, image, news_type, broadcast_type, action_button,
                     qr_code_content, qr_code_caption, app_ids)


def html_unescape(s):
    return re.sub('&(%s);' % '|'.join(name2codepoint), lambda m: unichr(name2codepoint[m.group(1)]), s)


def parse_html_content(html_content):
    if not html_content:
        return html_content

    if not isinstance(html_content, unicode):
        html_content = html_content.decode('utf8')

    html_content = html_content.replace("<strong>", "").replace("</strong>", "")
    html_content = html_content.replace("<em>", "").replace("</em>", "")
    html_content = html_content.replace("<hr />", "")

    m = True
    while m:
        m = re.search('(?i)<img([^>]+)/>', html_content)
        if m:
            html_content = html_content.replace(m.group(), "")

    m = True
    while m:
        m = re.search('(?i)<a([^>]+)></a>', html_content)
        if m:
            html_content = html_content.replace(m.group(), "")

    mailtos = dict()
    m = True
    while m:
        m = re.search('<a href=[\'\"]mailto:(.+)[\'\"]>(.+)</a>', html_content)
        if m:
            action = m.group(1)
            name = m.group(2)
            mailtos[name] = action
            html_content = html_content.replace(m.group(), name)

    hrefs = dict()
    m = True
    while m:
        m = re.search('(?i)<a([^>]+)>(.+?)</a>', html_content)
        if m:
            found = False
            m_attributes = m.group(1)
            name = m.group(2)
            m_href = re.search('\\s*(?i)href\\s*=\\s*\"([^\"]*)\"', m_attributes)
            if m_href:
                action = m_href.group(1)
                found = True
                hrefs[name] = action

            if not found:
                logging.error("We need a better filter ...")
                logging.debug(m.group(0))

            html_content = html_content.replace(m.group(), name)

    return html2text.html2text(html_unescape(html_content)), mailtos.items(), hrefs.items()
