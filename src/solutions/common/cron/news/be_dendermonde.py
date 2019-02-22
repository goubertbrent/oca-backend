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

import logging
from xml.dom import minidom

from google.appengine.api import urlfetch
from google.appengine.ext import db, deferred

from lxml import html
from lxml.html import HtmlElement
from solutions.common.cron.news import BROADCAST_TYPE_NEWS, transl, create_news_item, html_to_markdown
from solutions.common.dal import get_solution_settings
from solutions.common.models import SolutionNewsScraperSettings


def check_for_news(service_user):
    deferred.defer(_check_for_news, service_user)


def _check_for_news(service_user, rss_url=None):
    if not rss_url:
        rss_url = u"http://www.dendermonde.be/rssout.aspx?cat=N"

    sln_settings = get_solution_settings(service_user)
    broadcast_type = transl(BROADCAST_TYPE_NEWS, sln_settings.main_language)
    if broadcast_type not in sln_settings.broadcast_types:
        logging.info(sln_settings.broadcast_types)
        logging.error("check_for_news_in_be_dendermonde failed no broadcast type found with name '%s' for service %s",
                      broadcast_type, service_user)
        return

    response = urlfetch.fetch(rss_url, deadline=60)
    if response.status_code != 200:
        logging.error("Could not check news for url %s in be_dendermonde.\n%s", rss_url, response.content)
        return

    sln_news_scraper_settings_key = SolutionNewsScraperSettings.create_key(service_user)

    def trans():
        sln_news_scraper_settings = SolutionNewsScraperSettings.get(sln_news_scraper_settings_key)
        if not sln_news_scraper_settings:
            return []

        return sln_news_scraper_settings.urls
    urls = db.run_in_transaction(trans)

    doc = minidom.parseString(response.content)
    for item in doc.getElementsByTagName('item'):
        try:
            title = item.getElementsByTagName("title")[0].firstChild.nodeValue
            url = item.getElementsByTagName("link")[0].firstChild.nodeValue
            url = unicode(url) if not isinstance(url, unicode) else url
            if url in urls:
                continue

            response = urlfetch.fetch(url, deadline=60)
            if response.status_code != 200:
                logging.warn('Received status code %d from %s with content:\n', response.status_code, url,
                             response.content)
                continue

            tree = html.fromstring(response.content.decode("utf8"))
            div = tree.xpath('//div[@class="long box"]')  # type: list[HtmlElement]
            if not div:
                logging.error('News scraper for dendermonde needs to be updated rss url %s', url, _suppress=False)
                continue
            message = html_to_markdown(html.tostring((div[0])))
        except Exception:
            logging.debug("title: %s", title)
            logging.debug(item.childNodes)
            raise

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
