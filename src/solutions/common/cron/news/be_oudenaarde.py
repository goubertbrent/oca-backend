# -*- coding: utf-8 -*-
# Copyright 2017 GIG Technology NV
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
# @@license_version:1.2@@

from google.appengine.ext.deferred import deferred

from solutions.common.cron.news.NewsScraper import NewsScraper
from solutions.common.models import SolutionNewsScraperSettings


class BeOudenaardeNewsScraper(NewsScraper):
    BASE_URL = 'http://oudenaarde.be'

    def __init__(self, service_user):
        super(BeOudenaardeNewsScraper, self).__init__(service_user)

    def check_for_news(self):
        tree = self.get_page(u'%s/nieuws/' % self.BASE_URL)
        scraper_settings = SolutionNewsScraperSettings.get(self.scraper_settings_key)
        container = tree.xpath('//div[@class="table fixed"]//div[@class="col"]/div')
        urls_to_get = []
        for i, row in enumerate(container):
            permalink = u'%s%s' % (self.BASE_URL, row.xpath('//div[@class="node-links"]//a/@href')[i])
            if permalink not in scraper_settings.urls:
                urls_to_get.append(permalink)
        news = []
        for permalink in urls_to_get:
            title, message = self.get_details(permalink)
            news.append((title, message, permalink))
        for title, message, permalink in news:
            deferred.defer(self.create_news, self.broadcast_type, title, message, permalink)

    @classmethod
    def get_details(cls, permalink):
        doc = cls.get_page(permalink)
        title = u'%s' % doc.xpath('//h1/text()')[0].strip()
        return title, cls.get_message_from_paragraphs(doc.xpath('//div[@class="field body"]')[0])


def check_for_news(service_user):
    deferred.defer(_check_for_news, service_user)

def _check_for_news(service_user):
    BeOudenaardeNewsScraper(service_user).check_for_news()
