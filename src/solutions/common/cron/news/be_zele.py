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

import logging
from lxml import html

from google.appengine.api import urlfetch
from google.appengine.ext import db, deferred

from rogerthat.consts import DEBUG
from rogerthat.rpc import users
from solutions.common.cron.news import BROADCAST_TYPE_NEWS, transl, create_news_item
from solutions.common.dal import get_solution_settings
from solutions.common.models import SolutionNewsScraperSettings


def check_for_news(service_user):
    sln_settings = get_solution_settings(service_user)
    if BROADCAST_TYPE_NEWS not in sln_settings.broadcast_types:
        logging.error("check_for_news_in_be_zele failed no broadcast type found with name '%s'", BROADCAST_TYPE_NEWS)
        return

    broadcast_type = transl(BROADCAST_TYPE_NEWS, sln_settings.main_language)

    url = u"https://www.zele.be/nieuws"
    response = urlfetch.fetch(url, deadline=60)
    if response.status_code != 200:
        logging.error("Could not check for news in be_zele.\n%s" % response.content)
        return

    tree = html.fromstring(response.content.decode("utf8"))

    sln_news_scraper_settings_key = SolutionNewsScraperSettings.create_key(service_user)

    def trans():
        sln_news_scraper_settings = SolutionNewsScraperSettings.get(sln_news_scraper_settings_key)
        if not sln_news_scraper_settings:
            return []

        return sln_news_scraper_settings.urls

    urls = db.run_in_transaction(trans)

    news_items = tree.xpath('//div[@class="news-partial "]//div[@class="partial-container"]//ul//li')

    for news_item in news_items:
        a = news_item.getchildren()[0]
        url = u'%s' % a.xpath("@href")[0]

        if not (url.startswith("http://") or url.startswith("https://")):
            url = u"https://www.zele.be%s" % url

        if url in urls:
            continue

        title = None
        message = u''
        for item in a.getchildren():
            if item.tag == "h3":
                title = u'%s' % item.text
            if item.tag == "div" and item.xpath("@class")[0] == "short":
                message = item.text

        if title:
            def trans():
                sln_news_scraper_settings = SolutionNewsScraperSettings.get(sln_news_scraper_settings_key)
                if not sln_news_scraper_settings:
                    sln_news_scraper_settings = SolutionNewsScraperSettings(key=sln_news_scraper_settings_key)
                    sln_news_scraper_settings.urls = []

                if url not in sln_news_scraper_settings.urls:
                    sln_news_scraper_settings.urls.append(url)
                    sln_news_scraper_settings.put()
                    deferred.defer(create_news_item, sln_settings, broadcast_type, message, title, url,
                                   _transactional=True)

            db.run_in_transaction(trans)
