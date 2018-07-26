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
from google.appengine.ext import webapp, deferred, ndb

from rogerthat.bizz.job import run_job
from rogerthat.utils import now
from solutions.common.cron.news import html_unescape, parse_html_content, transl, \
    create_news_item
from solutions.common.dal import get_solution_settings
from solutions.common.models import SolutionRssScraperSettings, SolutionRssScraperItem

BROADCAST_TYPE_NEWS = u"News"


class SolutionRssScraper(webapp.RequestHandler):

    def get(self):
        run_job(_qry, [], _worker, [])


def _qry():
    return SolutionRssScraperSettings.query()


def _worker(rss_settings_key):
    rss_settings = rss_settings_key.get()  # type: SolutionRssScraperSettings
    if not rss_settings.rss_links:
        return
    service_user = rss_settings.service_user
    service_identity = rss_settings.service_identity

    sln_settings = get_solution_settings(service_user)
    if BROADCAST_TYPE_NEWS not in sln_settings.broadcast_types:
        logging.info(sln_settings.broadcast_types)
        logging.error("process_rss_links failed for '%s' no broadcast type found with name '%s'",
                      service_user,
                      BROADCAST_TYPE_NEWS)
        return
    broadcast_type = transl(BROADCAST_TYPE_NEWS, sln_settings.main_language)
    must_update_settings = False

    for rss_link in rss_settings.rss_links:
        dry_run = not rss_link.dry_runned
        try:
            response = urlfetch.fetch(rss_link.url, deadline=10)
        except Exception:
            logging.exception("Could not load rss url: %s" % rss_link.url)
            continue
        if response.status_code != 200:
            logging.error("Could not load rss url: %s with status code %s" % (rss_link.url, response.status_code))
            continue

        logging.info('Scraping rss for url %s in dry_run %s', rss_link.url, dry_run)

        doc = minidom.parseString(response.content)
        keys = []
        items = []
        for item in doc.getElementsByTagName('item'):
            try:
                title = html_unescape(item.getElementsByTagName("title")[0].firstChild.nodeValue)
                url = item.getElementsByTagName("link")[0].firstChild.nodeValue
                guid_elements = item.getElementsByTagName('guid')
                if guid_elements:
                    guid = guid_elements[0].firstChild.nodeValue
                else:
                    guid = None
                description_tags = item.getElementsByTagName("description")
                if not description_tags:
                    logging.debug("url: %s", url)
                    logging.info('description not found for %s', item.childNodes)
                    continue
                description_html = description_tags[0].firstChild.nodeValue
                message, _, _ = parse_html_content(description_html)

            except:
                logging.debug(item.childNodes)
                logging.debug("url: %s", url)
                raise

            url_key = SolutionRssScraperItem.create_key(service_user, service_identity, url)
            keys.append(url_key)
            if guid:
                guid_key = SolutionRssScraperItem.create_key(service_user, service_identity, guid)
                keys.append(guid_key)
            items.append((title, url, guid, description_html, message))

        scraper_items = {item.key.id(): item for item in ndb.get_multi(keys) if item}

        if dry_run:
            rss_link.dry_runned = True
            must_update_settings = True

        def trans():
            to_put = []
            for title, url, guid, description_html, message in items:
                if url not in scraper_items and guid not in scraper_items:
                    new_key = SolutionRssScraperItem.create_key(service_user, service_identity, guid if guid else url)
                    new_item = SolutionRssScraperItem(key=new_key,
                                                      timestamp=now(),
                                                      dry_run=dry_run)
                    if not dry_run:
                        deferred.defer(create_news_item, sln_settings, broadcast_type, message, title, url,
                                       rss_settings.notify, _transactional=True)
                    to_put.append(new_item)
            if to_put:
                ndb.put_multi(to_put)

        trans() if dry_run else ndb.transaction(trans, xg=True)
    if must_update_settings:
        rss_settings.put()
