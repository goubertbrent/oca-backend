# -*- coding: utf-8 -*-
# Copyright 2017 Mobicage NV
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

from lxml import html

from google.appengine.api import urlfetch
from google.appengine.ext.deferred import deferred, db

from rogerthat.rpc.service import BusinessException
from solutions.common.cron.news import create_news_item, BROADCAST_TYPE_NEWS, transl, parse_html_content
from solutions.common.dal import get_solution_settings
from solutions.common.models import SolutionNewsScraperSettings


class NewsScraperException(BusinessException):
    pass


class NewsScraper(object):
    sln_settings = None
    scraper_settings_key = None
    broadcast_type = None

    def __init__(self, service_user=None):
        if service_user:
            self.service_user = service_user
        self.scraper_settings_key = SolutionNewsScraperSettings.create_key(self.service_user)
        self.sln_settings = get_solution_settings(self.service_user)
        if BROADCAST_TYPE_NEWS not in self.sln_settings.broadcast_types:
            raise NewsScraperException(
                'Cannot check for news in %s because no broadcast type with name \'%s\' is found',
                self.sln_settings.name, BROADCAST_TYPE_NEWS)

        self.broadcast_type = transl(BROADCAST_TYPE_NEWS, self.sln_settings.main_language)

    def create_news(self, broadcast_type, title, message, permalink):
        def trans():
            sln_news_scraper_settings = SolutionNewsScraperSettings.get(self.scraper_settings_key)
            if not sln_news_scraper_settings:
                sln_news_scraper_settings = SolutionNewsScraperSettings(key=self.scraper_settings_key)
                sln_news_scraper_settings.urls = []

            if permalink not in sln_news_scraper_settings.urls:
                sln_news_scraper_settings.urls.append(permalink)
                sln_news_scraper_settings.put()
                deferred.defer(create_news_item, self.sln_settings, broadcast_type, message, title, permalink,
                               _transactional=True)

        db.run_in_transaction(trans)

    @staticmethod
    def get_page(permalink):
        """
        Args:
            permalink (basestring)
        Returns:
            html_element (HtmlElement)
        """
        response = urlfetch.fetch(permalink, deadline=60)
        if response.status_code != 200:
            msg = 'Could not fetch url %s.\n%s' % (permalink, response.content)
            raise NewsScraperException(msg)
        return html.fromstring(response.content.decode('utf-8'))

    @staticmethod
    def get_message_from_paragraphs(container, selector='//p'):
        """
        Args:
            container (HtmlElement)
            selector (basestring)
        """
        paragraphs = []
        for paragraph in container.xpath(selector):  # type: HtmlElement
            text = parse_html_content(paragraph.text_content())[0].strip()
            if text:
                paragraphs.append(text)
        return '\n\n'.join(paragraphs)
