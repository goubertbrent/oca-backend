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

from google.appengine.ext.deferred import deferred

from solutions.common.cron.news.NewsScraper import NewsScraper
from solutions.common.models import SolutionNewsScraperSettings


class BeNinoveNewsScraper(NewsScraper):
    BASE_URL = 'http://ninove.be'

    def __init__(self, service_user):
        super(BeNinoveNewsScraper, self).__init__(service_user)

    def check_for_news(self):
        tree = self.get_page(u'%s/nl/press/index.html' % self.BASE_URL)
        scraper_settings = SolutionNewsScraperSettings.get(self.scraper_settings_key)
        scraped_urls = scraper_settings.urls if scraper_settings else []
        urls_in_page = [u'%s%s' % (self.BASE_URL, url) for url in tree.xpath('//a[@class="readmore"]/@href')]
        urls = [url for url in urls_in_page if url not in scraped_urls]
        news = []
        for permalink in urls:
            title, message = self.get_details(permalink)
            news.append((title, message, permalink))
        for title, message, permalink in news:
            deferred.defer(self.create_news, self.broadcast_type, title, message, permalink)

    @classmethod
    def get_details(cls, permalink):
        tree = cls.get_page(permalink)
        container = tree.xpath('//div[@id="content"]')[0]
        title = u'%s' % container.xpath('//h1/text()')[0].strip()
        return title, cls.get_message_from_paragraphs(container, '//div[@class="text"]/p')


def check_for_news(service_user):
    BeNinoveNewsScraper(service_user).check_for_news()
